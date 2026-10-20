import ipaddress, re, subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ssh-key-manager")
SSH_DIR = Path.home() / ".ssh"
NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
USER_RE = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
HOST_RE = re.compile(r"^[A-Za-z0-9.-]{1,253}$")

def _check_host(host):
    try:
        ipaddress.ip_address(host)
    except ValueError:
        if not HOST_RE.match(host):
            raise ValueError("Invalid host")

@mcp.tool()
def generate_ssh_key(name: str = "id_ed25519_agent",
                     key_type: str = "ed25519",
                     comment: str = "agent-generated") -> str:
    """Generate a new SSH key pair in ~/.ssh (never overwrites existing keys)."""
    if not NAME_RE.match(name) or key_type not in ("ed25519", "rsa"):
        return "Error: invalid name or key type"
    SSH_DIR.mkdir(mode=0o700, exist_ok=True)
    path = SSH_DIR / name
    if path.exists():
        return f"Error: {path} already exists"
    cmd = ["ssh-keygen", "-t", key_type, "-f", str(path), "-C", comment, "-N", ""]
    if key_type == "rsa":
        cmd += ["-b", "4096"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else f"Error: {r.stderr}"

@mcp.tool()
def copy_ssh_key(host: str, user: str, key_name: str = "id_ed25519_agent") -> str:
    """Install a public key on a remote server using ssh-copy-id."""
    try:
        _check_host(host)
    except ValueError as e:
        return f"Error: {e}"
    if not USER_RE.match(user) or not NAME_RE.match(key_name):
        return "Error: invalid user or key name"
    pub = SSH_DIR / f"{key_name}.pub"
    if not pub.exists():
        return f"Error: {pub} not found. Generate it first."
    r = subprocess.run(
        ["ssh-copy-id", "-i", str(pub), "-o", "StrictHostKeyChecking=accept-new",
         f"{user}@{host}"],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
    return r.stdout + r.stderr

@mcp.tool()
def list_ssh_keys() -> list[str]:
    """List public keys in ~/.ssh."""
    return sorted(p.name for p in SSH_DIR.glob("*.pub"))

if __name__ == "__main__":
    mcp.run()