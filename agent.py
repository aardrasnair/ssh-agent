import asyncio, json, sys
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

llm = Anthropic()
MODEL = "claude-sonnet-5-5"
SYSTEM = ("You manage SSH keys. Only use the provided tools. "
          "If host or username is missing, ask the user. Never invent them.")

async def main():
    params = StdioServerParameters(command=sys.executable, args=["ssh_server.py"])
    async with stdio_client(params) as (r, w), ClientSession(r, w) as session:
        await session.initialize()
        tools = [{"name": t.name, "description": t.description,
                  "input_schema": t.inputSchema}
                 for t in (await session.list_tools()).tools]
        messages = []
        while True:
            user = input("ssh-agent> ")
            if user in ("exit", "quit"):
                break
            messages.append({"role": "user", "content": user})
            while True:
                resp = llm.messages.create(model=MODEL, max_tokens=1000,
                                           system=SYSTEM, tools=tools,
                                           messages=messages)
                messages.append({"role": "assistant", "content": resp.content})
                calls = [b for b in resp.content if b.type == "tool_use"]
                if not calls:
                    print("".join(b.text for b in resp.content if b.type == "text"))
                    break
                results = []
                for c in calls:
                    print(f"\n[PLAN] {c.name}({json.dumps(c.input)})")
                    if input("Execute? [y/N] ").lower() == "y":
                        out = await session.call_tool(c.name, c.input)
                        text = out.content[0].text
                    else:
                        text = "User denied this action."
                    results.append({"type": "tool_result",
                                    "tool_use_id": c.id, "content": text})
                messages.append({"role": "user", "content": results})

asyncio.run(main())
