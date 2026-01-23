from pathlib import Path

def find_project_root(path="."):
    root = Path(path).resolve()
    compose = root / "docker-compose.yml"
    if not compose.exists():
        raise FileNotFoundError("docker-compose.yml not found in project root")
    return root
