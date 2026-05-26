import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def run(cmd: list[str], *, check: bool = False) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )
    output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
    return output.strip()
