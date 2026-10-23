# SSH Key Manager Agent

An AI-powered SSH Key Manager Agent that accepts natural-language instructions and uses tools to manage SSH keys. Built with Python, Ollama, and the Model Context Protocol (MCP), the agent interprets user requests, proposes tool calls, and asks for approval before executing operations.

## Features

- **Natural-language interaction:** Request SSH key operations using ordinary English.
- **SSH key generation:** Generate Ed25519 or RSA SSH key pairs using `ssh-keygen`.
- **Public-key deployment:** Deploy a public key to an authorized remote account using `ssh-copy-id`.
- **Key listing:** List existing SSH public-key filenames.
- **Execution approval:** Review the agent's proposed tool call before execution.
- **Input validation:** Validate key names, usernames, and key types.
- **Overwrite protection:** Refuse to overwrite an existing private-key file.
- **Local LLM integration:** Use Ollama with the `llama3.2` model.
- **MCP tool integration:** Expose SSH operations through an MCP server.

## Technology Stack

- Python 3
- Ollama
- Llama 3.2
- Model Context Protocol (MCP)
- OpenSSH utilities: `ssh-keygen`, `ssh-copy-id`, and `ssh`
- Linux / Ubuntu or WSL Ubuntu

## Project Structure

```text
ssh-agent/
├── agent.py
├── agent_ollama.py
├── ssh_server.py
├── requirements.txt
└── README.md
```

- `agent.py` — Original agent implementation.
- `agent_ollama.py` — Ollama-powered agent interface.
- `ssh_server.py` — MCP server containing SSH key management tools.
- `requirements.txt` — Python dependencies.
- `README.md` — Project documentation.

## Prerequisites

Before running the project, ensure you have:

1. Python 3 and `venv`.
2. Git.
3. Ollama installed and running.
4. The `llama3.2` model downloaded.
5. OpenSSH client utilities installed.

The following instructions assume Ubuntu or WSL Ubuntu.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/aardrasnair/ssh-agent.git
cd ssh-agent
```

If you already have the repository locally, navigate to it instead:

```bash
cd ~/ssh-agent
```

### 2. Install system dependencies

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip openssh-client
```

If you intend to use `ssh-copy-id` to deploy keys to a server, ensure that the `ssh-copy-id` utility is available.

### 3. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Install and prepare Ollama

Install Ollama using its official installation instructions: https://ollama.com/download

Download the model:

```bash
ollama pull llama3.2
```

Verify that the model is available:

```bash
ollama list
```

Ensure the Ollama service is running. In a separate terminal, you can test the model with:

```bash
ollama run llama3.2
```

Type a simple prompt to confirm that the model responds, then enter `/bye` to exit.

## Running the Agent

From the project directory, activate the virtual environment and start the Ollama-powered agent:

```bash
cd ~/ssh-agent
source .venv/bin/activate
python3 agent_ollama.py
```

Wait until the following prompt appears:

```text
ssh-agent>
```

You can now enter natural-language requests.

To exit the agent, type:

```text
exit
```

## Usage Examples

### 1. Generate a new SSH key

Enter:

```text
Generate a new SSH key named demo_key
```

Review the proposed tool call. If the filename and key type are correct, approve the operation when prompted.

The server uses `ssh-keygen` to generate the key pair. The private and public keys are stored in the user's `~/.ssh/` directory.

For example:

```text
~/.ssh/demo_key
~/.ssh/demo_key.pub
```

The private key must remain secret.

### 2. List existing public keys

Enter:

```text
List my existing SSH public keys
```

The agent calls the key-listing tool and displays the public-key filenames found in the SSH directory.

### 3. Deploy a public key to an authorized server

Enter a request using your actual server details:

```text
Copy my demo_key public key to USERNAME@SERVER_HOST
```

Replace `USERNAME` and `SERVER_HOST` with the username and hostname or IP address of a server you are authorized to access.

Review the proposed operation before approving it. The deployment tool uses `ssh-copy-id` to install the public key on the target account. The server must be reachable, and the account must permit the required authentication.

### 4. Test an existing key name

If `demo_key` already exists, enter:

```text
Generate a new SSH key named demo_key
```

The server should reject the operation rather than overwrite the existing private-key file.

## Security Considerations

- Keep private keys private. Never commit private keys to GitHub or include their contents in screenshots.
- Review every proposed tool call before approving it.
- Deploy keys only to servers and accounts you are authorized to access.
- Never place passwords, passphrases, API tokens, or other credentials in source code or Git commits.
- Use strong authentication and protect the permissions of your SSH directory and private keys.
- Treat LLM-generated plans as suggestions; validate the arguments and verify actual tool results.
- Do not interpret a generated plan as proof that an operation succeeded.
- Avoid overwriting existing keys. Back up important keys securely before making changes.

## Troubleshooting

### Ollama connection error

Ensure Ollama is installed and running, then verify the model:

```bash
ollama list
```

If necessary, download it:

```bash
ollama pull llama3.2
```

### Python module not found

Activate the virtual environment and install dependencies again:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### SSH key already exists

The agent intentionally refuses to overwrite an existing key. Choose a different filename or securely handle the existing key outside the agent's overwrite-protection workflow.

### Invalid username or key name

Use a valid lowercase Linux username and a key name permitted by the server's validation rules. Check the actual username on your Ubuntu machine with:

```bash
whoami
```

### Public-key deployment fails

Check that the target hostname or IP is correct, the server is reachable, SSH is enabled on the target, and the username is valid. Review the actual `ssh-copy-id` error rather than assuming the key was installed.

### Git changes are not appearing

Check your working tree:

```bash
git status
git diff
```

Only modified or newly created files need to be staged and committed.

## Limitations

- The LLM may interpret ambiguous requests incorrectly; review plans before approval.
- Remote deployment requires a reachable, authorized SSH server.
- Successful key generation does not guarantee successful remote authentication.
- SSH deployment and login verification must be tested separately.
- The agent's capabilities depend on the available MCP tools, installed dependencies, and local Ollama model.

## Future Enhancements

- Stronger structured validation of model-generated tool arguments.
- More comprehensive automated tests for valid, invalid, and unsafe requests.
- Improved error recovery and operation logging.
- Automated SSH connectivity verification after key deployment.
- Support for additional key-management workflows and clearer execution summaries.

## Author

**Repository:** https://github.com/aardrasnair/ssh-agent

