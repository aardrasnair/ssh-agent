import asyncio, json, subprocess, sys
import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from ssh_server import _check_host, USER_RE, NAME_RE, SSH_DIR

MODEL = "llama3.2"
SYSTEM = ("You manage SSH keys using the provided tools only. "
          "Use the exact host and username the user gives. "
          "If the host or username is missing, ask the user. Never invent them. "
          "Only call generate_ssh_key if the user asks for a NEW key. "
          "After a tool finishes, briefly tell the user the result.")


def copy_key_in_terminal(args):
    """Run ssh-copy-id here, where the real keyboard is, so the password
    prompt works and the password never goes to the AI."""
    host = args.get("host", "")
    user = args.get("user", "")
    key = args.get("key_name", "id_ed25519_agent")
    try:
        _check_host(host)
    except ValueError as e:
        return f"Error: {e}"
    if not USER_RE.match(user) or not NAME_RE.match(key):
        return "Error: invalid user or key name"
    pub = SSH_DIR / f"{key}.pub"
    if not pub.exists():
        return f"Error: {pub} not found. Generate it first."
    print("\n(ssh-copy-id will ask for the SSH password. Type it here. "
          "The AI never sees it.)")
    r = subprocess.run(["ssh-copy-id", "-i", str(pub),
                        "-o", "StrictHostKeyChecking=accept-new",
                        f"{user}@{host}"])
    if r.returncode == 0:
        return f"Success: key {key}.pub installed on {user}@{host}"
    return f"Failed: ssh-copy-id exited with code {r.returncode}"


async def main():
    params = StdioServerParameters(command=sys.executable, args=["ssh_server.py"])
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        tools = [{"type": "function",
                  "function": {"name": t.name,
                               "description": t.description,
                               "parameters": t.inputSchema}}
                 for t in (await session.list_tools()).tools]
        messages = [{"role": "system", "content": SYSTEM}]
        while True:
            user = input("ssh-agent> ")
            if user in ("exit", "quit"):
                break
            messages.append({"role": "user", "content": user})
            while True:
                resp = ollama.chat(model=MODEL, messages=messages, tools=tools)
                msg = resp.message
                messages.append(msg)
                if not msg.tool_calls:
                    print(msg.content)
                    break
                for c in msg.tool_calls:
                    name = c.function.name
                    args = dict(c.function.arguments)
                    print(f"\n[PLAN] {name}({json.dumps(args)})")
                    if input("Execute? [y/N] ").lower() == "y":
                        if name == "copy_ssh_key":
                            text = copy_key_in_terminal(args)
                        else:
                            out = await session.call_tool(name, args)
                            text = "\n".join(b.text for b in out.content
                                             if hasattr(b, "text"))
                        print(f"[RESULT] {text}")
                    else:
                        text = "User denied this action."
                    messages.append({"role": "tool", "tool_name": name,
                                     "content": text})

asyncio.run(main())