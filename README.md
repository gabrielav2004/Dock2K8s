# Dock2K8s

Convert Docker Compose configurations to Kubernetes manifests with a simple CLI or web UI.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Basic conversion (uses docker-compose.yml → k8s/)
python cli.py

# With custom config
python cli.py -c config.yml --replicas 3 --verbose

# Launch web UI (see ui/README.md for details)
python run_ui.py
```

## Features

- **CLI Tool**: Convert `docker-compose.yml` → Kubernetes manifests
- **Web UI**: Visual editor with service graphs (Compose & K8s views) - [docs](ui/README.md)
- **Flexible Config**: `config.yml` with CLI overrides
- **Secrets**: Generate K8s Secrets from `.env` files
- **Dependencies**: Handle `depends_on` relationships

## Installation

**Requirements:** Python 3.7+, PyYAML

```bash
pip install pyyaml
# For UI: pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Basic
python cli.py

# Custom project & output
python cli.py -p /path/to/project -o ./manifests

# Override defaults
python cli.py --replicas 3 --service-type LoadBalancer -v

# Custom compose file
python cli.py -f docker-compose.prod.yml
```

**Common Options:**
- `-p, --project-dir DIR` - Project directory (default: `.`)
- `-c, --config FILE` - Config file (default: `config.yml`)
- `-f, --file FILE` - Docker Compose file (default: `docker-compose.yml`)
- `-o, --output-dir DIR` - Output directory (default: `k8s`)
- `--replicas N` - Default replicas
- `--service-type TYPE` - Service type (ClusterIP/NodePort/LoadBalancer)
- `-v, --verbose` - Verbose output

### Web UI

```bash
python run_ui.py
# Opens at http://127.0.0.1:8000/
```

**Features:**
- **Compose View**: Visualize services and `depends_on` relationships
- **K8s View**: View generated Kubernetes resources
- **Properties Panel**: Edit service configs (replicas, controller, service type)
- **Preview**: See generated YAML before conversion

## Configuration

Create `config.yml` in your project root:

```yaml
defaults:
  replicas: 2
  controller: Deployment

output_dir: k8s
verbose: false

workloads:
  api:
    replicas: 3
    controller: Deployment
  
  db:
    replicas: 1
    controller: StatefulSet

services:
  api:
    enabled: true
    type: LoadBalancer
  
  db:
    enabled: true
    type: ClusterIP
```

**Precedence:** CLI args > `config.yml` > defaults

## Project Structure

```
project-root/
├── docker-compose.yml    # Input
├── config.yml            # Configuration (optional)
├── .env                  # Secrets source (optional)
└── k8s/                  # Generated manifests
    ├── api-deployment.yaml
    ├── api-service.yaml
    └── ...
```

## Documentation

- **[CLI Reference](CLI-REFERENCE.md)** - Complete CLI documentation
- **[Config Reference](CONFIG-REFERENCE.md)** - Configuration guide
- **[UI Documentation](ui/README.md)** - Web UI guide and features
- **[Testing Guide](TESTING.md)** - Testing procedures

## Examples

**Development:**
```bash
python cli.py --replicas 1 --service-type NodePort -v
```

**Production:**
```bash
python cli.py -c config-prod.yml --replicas 3 --service-type LoadBalancer
```

**With volumes:**
```bash
python cli.py --convert-volumes --pvc-size 50Gi
```

## License

See LICENSE file for details.
