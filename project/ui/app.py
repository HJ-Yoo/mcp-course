"""
Gradio Chat UI for the Internal Ops Assistant MCP Server.

This provides a complete demo of the MCP flow:
  User message → LLM (Claude / GPT / Gemini) → MCP tool calls → Results → LLM response

Features:
  - Chat interface with multi-LLM backend (Anthropic, OpenAI, Google Gemini)
  - Real-time MCP log panel showing tool calls and results
  - Transport selector: stdio or Streamable HTTP
  - API key input with dynamic provider dropdown

Run:
  macOS/Linux:  uv run python ui/app.py
  Windows:      uv run python ui\\app.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import gradio as gr

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.mcp_client import MCPClient

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
mcp_client: MCPClient | None = None

SYSTEM_PROMPT = """\
You are the Acme Corp Internal Ops Assistant. You help employees with:
- IT equipment inventory lookup
- Internal policy questions
- IT support ticket creation

You have access to MCP tools. Use them proactively when relevant.
Be concise, helpful, and professional. Answer in the same language the user uses.
When creating tickets, always preview first (confirm=False), show the preview to
the user, and only create (confirm=True) if they approve.
"""

# ---------------------------------------------------------------------------
# LLM provider registry
# ---------------------------------------------------------------------------
PROVIDERS: dict[str, dict] = {
    "anthropic": {
        "label": "Anthropic Claude",
        "model": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "label": "OpenAI GPT",
        "model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
    },
    "google": {
        "label": "Google Gemini",
        "model": "gemini-2.0-flash",
        "env_key": "GOOGLE_API_KEY",
    },
}


def _detect_available_providers() -> list[str]:
    """Return provider keys that have API keys set."""
    available = []
    for key, cfg in PROVIDERS.items():
        if os.environ.get(cfg["env_key"], "").strip():
            available.append(key)
    return available


# ---------------------------------------------------------------------------
# MCP connection management
# ---------------------------------------------------------------------------
async def connect_mcp(transport: str) -> str:
    global mcp_client

    if mcp_client and mcp_client.is_connected:
        await mcp_client.disconnect()

    if transport == "stdio":
        mcp_client = MCPClient(
            transport="stdio",
            server_cwd=str(PROJECT_ROOT),
        )
    else:
        mcp_client = MCPClient(
            transport="streamable-http",
            http_url="http://localhost:8000/mcp",
        )

    try:
        await mcp_client.connect()
        tools = await mcp_client.list_tools()
        resources = await mcp_client.list_resources()
        tool_names = [t["name"] for t in tools]
        resource_uris = [r["uri"] for r in resources]
        return (
            f"✅ Connected via **{transport}**\n\n"
            f"**Tools** ({len(tools)}): {', '.join(tool_names)}\n\n"
            f"**Resources** ({len(resources)}): {', '.join(resource_uris)}"
        )
    except Exception as e:
        mcp_client = None
        return f"❌ Connection failed: {e}"


async def disconnect_mcp() -> str:
    global mcp_client
    if mcp_client and mcp_client.is_connected:
        await mcp_client.disconnect()
        mcp_client = None
        return "Disconnected."
    return "Not connected."


# ---------------------------------------------------------------------------
# Provider-specific agentic loops
# ---------------------------------------------------------------------------
async def _run_anthropic(messages: list[dict], claude_tools: list[dict]) -> str:
    """Agentic loop using the Anthropic SDK."""
    import anthropic

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = PROVIDERS["anthropic"]["model"]

    for _ in range(10):
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=claude_tools,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            assistant_content = response.content
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results = []
            for block in assistant_content:
                if block.type == "tool_use":
                    result = await mcp_client.call_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
            messages.append({"role": "user", "content": tool_results})
        else:
            text_parts = [b.text for b in response.content if hasattr(b, "text")]
            return "\n".join(text_parts)

    return "⚠️ Tool call loop limit reached."


async def _run_openai(messages: list[dict], claude_tools: list[dict]) -> str:
    """Agentic loop using the OpenAI SDK (function calling)."""
    from openai import OpenAI

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    model = PROVIDERS["openai"]["model"]

    # Convert MCP tools to OpenAI function format
    openai_tools = []
    for t in claude_tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            },
        })

    # Build OpenAI-style messages
    oai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, str) and role in ("user", "assistant"):
            oai_messages.append({"role": role, "content": content})

    for _ in range(10):
        response = client.chat.completions.create(
            model=model,
            messages=oai_messages,
            tools=openai_tools if openai_tools else None,
        )

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            oai_messages.append(choice.message)

            for tc in choice.message.tool_calls:
                args = json.loads(tc.function.arguments)
                result = await mcp_client.call_tool(tc.function.name, args)
                oai_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        else:
            return choice.message.content or ""

    return "⚠️ Tool call loop limit reached."


async def _run_google(messages: list[dict], claude_tools: list[dict]) -> str:
    """Agentic loop using the Google GenAI SDK (function calling)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    model = PROVIDERS["google"]["model"]

    # Convert MCP tools to Gemini function declarations
    declarations = []
    for t in claude_tools:
        schema = dict(t["input_schema"])
        schema.pop("additionalProperties", None)
        declarations.append(types.FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=schema,
        ))
    gemini_tools = [types.Tool(function_declarations=declarations)]

    # Build contents for Gemini
    contents = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, str) and role in ("user", "assistant"):
            gemini_role = "model" if role == "assistant" else "user"
            contents.append(types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=content)],
            ))

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=gemini_tools,
    )

    for _ in range(10):
        response = client.models.generate_content(
            model=model,
            contents=contents,
            config=config,
        )

        # Check for function calls
        has_fn_call = False
        fn_responses = []

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_fn_call = True
                    fc = part.function_call
                    args = dict(fc.args) if fc.args else {}
                    result = await mcp_client.call_tool(fc.name, args)
                    fn_responses.append(types.Part.from_function_response(
                        name=fc.name,
                        response={"result": result},
                    ))

        if has_fn_call:
            # Add model response + function results to contents
            contents.append(response.candidates[0].content)
            contents.append(types.Content(
                role="user",
                parts=fn_responses,
            ))
        else:
            return response.text or ""

    return "⚠️ Tool call loop limit reached."


# ---------------------------------------------------------------------------
# Main agent chat
# ---------------------------------------------------------------------------
async def agent_chat(
    message: str,
    history: list[dict],
    provider: str,
) -> tuple[list[dict], str]:
    global mcp_client

    if not mcp_client or not mcp_client.is_connected:
        history.append({"role": "assistant", "content": "⚠️ MCP server not connected. Please connect first."})
        return history, _format_logs()

    if provider not in PROVIDERS:
        history.append({"role": "assistant", "content": f"⚠️ Unknown provider: {provider}"})
        return history, _format_logs()

    env_key = PROVIDERS[provider]["env_key"]
    if not os.environ.get(env_key, "").strip():
        history.append({"role": "assistant", "content": f"⚠️ {env_key} not set. Enter it in the API Key field."})
        return history, _format_logs()

    # Build messages from history
    messages = []
    for msg in history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    # Get tool definitions
    claude_tools = await mcp_client.get_claude_tools()
    mcp_client.clear_logs()

    # Dispatch to provider
    try:
        if provider == "anthropic":
            final_text = await _run_anthropic(messages, claude_tools)
        elif provider == "openai":
            final_text = await _run_openai(messages, claude_tools)
        elif provider == "google":
            final_text = await _run_google(messages, claude_tools)
        else:
            final_text = "⚠️ Provider not implemented."
    except Exception as e:
        final_text = f"⚠️ LLM Error: {e}"

    history.append({"role": "assistant", "content": final_text})
    return history, _format_logs()


def _format_logs() -> str:
    if not mcp_client:
        return "Not connected."

    logs = mcp_client.logs
    if not logs:
        return "_No tool calls this turn._"

    parts = []
    for i, log in enumerate(logs, 1):
        status = "✅" if log.success else "❌"
        args_str = json.dumps(log.arguments, ensure_ascii=False)
        if len(args_str) > 120:
            args_str = args_str[:120] + "..."
        result_preview = log.result[:200]
        if len(log.result) > 200:
            result_preview += "..."

        parts.append(
            f"### {status} Call {i}: `{log.tool_name}` ({log.duration_ms}ms)\n"
            f"**Args:** `{args_str}`\n\n"
            f"**Result:**\n```\n{result_preview}\n```"
        )

    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
def build_ui() -> gr.Blocks:
    with gr.Blocks(
        title="Acme Internal Ops Assistant",
        theme=gr.themes.Soft(),
        css="""
        .log-panel { font-size: 0.85em; }
        .header { text-align: center; margin-bottom: 1em; }
        """,
    ) as demo:
        gr.Markdown(
            "# 🏢 Acme Corp Internal Ops Assistant\n"
            "> MCP-powered IT operations chatbot — Claude / GPT / Gemini + Tools + Resources",
            elem_classes="header",
        )

        with gr.Row():
            # ----- Left: Chat -----
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Chat",
                    type="messages",
                    height=520,
                    show_copy_button=True,
                )
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask me about inventory, policies, or create a ticket...",
                        show_label=False,
                        scale=5,
                        container=False,
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

                gr.Examples(
                    examples=[
                        "노트북 재고가 몇 대 남았어?",
                        "VPN 설정 방법을 알려줘",
                        "모니터가 깜빡거려서 수리 요청하고 싶어",
                        "원격근무 정책에서 해외 근무가 가능한가요?",
                        "What headsets do we have in stock?",
                    ],
                    inputs=msg_input,
                    label="Try these examples",
                )

            # ----- Right: Controls + Logs -----
            with gr.Column(scale=2):
                gr.Markdown("### ⚙️ MCP Connection")
                transport_radio = gr.Radio(
                    choices=["stdio", "streamable-http"],
                    value="stdio",
                    label="Transport",
                )
                with gr.Row():
                    connect_btn = gr.Button("Connect", variant="primary")
                    disconnect_btn = gr.Button("Disconnect", variant="secondary")
                connection_status = gr.Markdown("_Not connected._")

                gr.Markdown("### 🤖 LLM Provider")
                api_key_input = gr.Textbox(
                    label="API Key",
                    placeholder="Enter API key (sk-ant-..., sk-..., or AI...)",
                    type="password",
                )
                provider_dropdown = gr.Dropdown(
                    choices=[],
                    label="Provider",
                    interactive=True,
                    info="Enter an API key above to enable providers",
                )

                gr.Markdown("### 📋 MCP Tool Call Logs")
                log_display = gr.Markdown(
                    "_Connect to the server and send a message to see tool calls here._",
                    elem_classes="log-panel",
                )

        # ----- Event handlers -----
        async def on_connect(transport):
            return await connect_mcp(transport)

        async def on_disconnect():
            return await disconnect_mcp()

        def on_api_key_change(api_key: str):
            """When user types an API key, detect provider and update dropdown."""
            api_key = api_key.strip()
            if not api_key:
                return gr.update(choices=[], value=None)

            # Auto-detect provider from key prefix
            detected = []
            if api_key.startswith("sk-ant-"):
                os.environ["ANTHROPIC_API_KEY"] = api_key
                detected.append("anthropic")
            elif api_key.startswith("AI"):
                os.environ["GOOGLE_API_KEY"] = api_key
                detected.append("google")
            else:
                # Default: try as OpenAI key
                os.environ["OPENAI_API_KEY"] = api_key
                detected.append("openai")

            # Also include any previously-set providers
            for key, cfg in PROVIDERS.items():
                if os.environ.get(cfg["env_key"], "").strip() and key not in detected:
                    detected.append(key)

            labels = [(PROVIDERS[p]["label"], p) for p in detected]
            default = detected[0] if detected else None
            return gr.update(choices=labels, value=default)

        async def on_send(message, history, provider):
            if not message.strip():
                return history, "", _format_logs()
            if not provider:
                history = history or []
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": "⚠️ Please enter an API key and select a provider."})
                return history, "", _format_logs()
            history = history or []
            history.append({"role": "user", "content": message})
            history, logs = await agent_chat(message, history, provider)
            return history, "", logs

        connect_btn.click(fn=on_connect, inputs=[transport_radio], outputs=[connection_status])
        disconnect_btn.click(fn=on_disconnect, inputs=[], outputs=[connection_status])
        api_key_input.change(fn=on_api_key_change, inputs=[api_key_input], outputs=[provider_dropdown])

        send_btn.click(
            fn=on_send,
            inputs=[msg_input, chatbot, provider_dropdown],
            outputs=[chatbot, msg_input, log_display],
        )
        msg_input.submit(
            fn=on_send,
            inputs=[msg_input, chatbot, provider_dropdown],
            outputs=[chatbot, msg_input, log_display],
        )

    return demo


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

    demo = build_ui()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
