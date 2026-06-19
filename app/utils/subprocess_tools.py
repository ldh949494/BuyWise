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


def run_with_input(cmd: list[str], stdin: str) -> str:
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        input=stdin,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        output = "\n".join(part.strip() for part in (result.stdout, result.stderr) if part.strip())
        raise RuntimeError(output or f"Command failed: {' '.join(cmd)}")
    return result.stdout.strip()
