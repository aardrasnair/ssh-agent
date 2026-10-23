
import asyncio
import json
import subprocess
import sys
import ollama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ssh_server import _check_host, USER_RE, NAME_RE, SSH_DIR

MODEL = "llama3.2"

SYSTEM = """
You manage SSH keys using the provided tools only.
Never invent tool results, key contents, fingerprints, or file paths.
Use the exact host and username the user gives.
If host or username is missing, ask the user.
Only generate a key when the user explicitly asks for a new key.
For generate_ssh_key, always provide name, key_type, and comment.
Use ed25519 unless the user explicitly requests rsa.
Use the requested key name exactly.
Never claim success unless the actual tool result confirms it.
If a tool reports an error, explain that error honestly.
"""


def copy_key_in_terminal(args):
    host = args.get("host", "")
    user = args.get("user", "")
    key = args.get("key_name", "id_ed25519_agent")

    try:
        _check_host(host)
    except ValueError as e:
        return f"Error: {e}"

    if not USER_RE.fullmatch(user) or not NAME_RE.fullmatch(key):
        return "Error: invalid user or key name"

    pub = SSH_DIR / f"{key}.pub"
    if not pub.is_file():
        return f"Error: {pub} not found. Generate it first."

    print(
        "\nssh-copy-id will request the SSH password in this terminal. "
        "Do not enter your password into the chat."
    )

    try:
        result = subprocess.run(
            [
                "ssh-copy-id",
                "-i", str(pub),
                "-o", "StrictHostKeyChecking=accept-new",
                f"{user}@{host}",
            ],
            timeout=60,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "Error: ssh-copy-id timed out."

    if result.returncode == 0:
        return f"Success: {key}.pub installed on {user}@{host}."
    return f"Error: ssh-copy-id exited with code {result.returncode}."


def get_tool_result(out):
    parts = [
        block.text
        for block in out.content
        if hasattr(block, "text")
    ]
    result = "\n".join(parts).strip()

    if getattr(out, "isError", False):
        return f"Error: tool execution failed. {result}"

    return result or "Error: tool returned no result."


async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["ssh_server.py"],
    )

    async with stdio_client(params) as (reader, writer):
        async with ClientSession(reader, writer) as session:
            await session.initialize()

            available_tools = (await session.list_tools()).tools
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in available_tools
            ]

            messages = [{"role": "system", "content": SYSTEM}]

            while True:
                try:
                    user = input("ssh-agent> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nExiting SSH agent.")
                    break

                if user.lower() in ("exit", "quit"):
                    break

                messages.append({"role": "user", "content": user})

                while True:
                    response = ollama.chat(
                        model=MODEL,
                        messages=messages,
                        tools=tools,
                    )

                    msg = response.message

                    if not msg.tool_calls:
                        print(msg.content or "No response from model.")
                        messages.append({
                            "role": "assistant",
                            "content": msg.content or "",
                        })
                        break

                    messages.append(msg)

                    for call in msg.tool_calls:
                        name = call.function.name
                        args = dict(call.function.arguments)

                        if name == "generate_ssh_key":
                            args.setdefault("name", "id_ed25519_agent")
                            args.setdefault("key_type", "ed25519")
                            args.setdefault("comment", "agent-generated")

                            if not isinstance(args["name"], str) or not NAME_RE.fullmatch(args["name"]):
                                text = "Error: invalid key name."
                                print(f"\n[RESULT] {text}")
                                messages.append({
                                    "role": "tool",
                                    "tool_name": name,
                                    "content": text,
                                })
                                continue

                            if args["key_type"] not in ("ed25519", "rsa"):
                                text = "Error: key_type must be ed25519 or rsa."
                                print(f"\n[RESULT] {text}")
                                messages.append({
                                    "role": "tool",
                                    "tool_name": name,
                                    "content": text,
                                })
                                continue

                        print(f"\n[PLAN] {name}({json.dumps(args)})")
                        approval = input("Execute? [y/N] ").strip().lower()

                        if approval != "y":
                            text = "User denied this action."
                        else:
                            try:
                                if name == "copy_ssh_key":
                                    text = copy_key_in_terminal(args)
                                else:
                                    result = await session.call_tool(name, args)
                                    text = get_tool_result(result)
                            except Exception as error:
                                text = f"Error: tool execution failed: {error}"

                            print(f"[RESULT] {text}")

                        messages.append({
                            "role": "tool",
                            "tool_name": name,
                            "content": text,
                        })

                        # Do not let the model fabricate a follow-up after
                        # an error or a denied action.
                        if text.startswith("Error:") or text == "User denied this action.":
                            print(text if text == "User denied this action." else
                                  "The operation failed. No success is claimed.")
                            break

                    else:
                        continue

                    break


if __name__ == "__main__":
    asyncio.run(main())
