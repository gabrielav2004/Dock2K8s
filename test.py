import yaml
from pathlib import Path

file = Path("docker-compose.yml")

with open(file, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)

print(data.keys())  # should include 'services'
print(list(data["services"].keys()))
