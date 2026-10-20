# SSH Key Manager Agent

Natural-language SSH key management using a local LLM (Ollama) and MCP.

## Run
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama serve &
python agent_ollama.py
