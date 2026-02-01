# Dock2K8s - Docker Compose to Kubernetes Converter

A command-line tool that automatically converts Docker Compose configurations into Kubernetes manifests. Control the conversion process via CLI parameters or a `config.yml` file.

## Quick Links

- **[CLI Reference](CLI-REFERENCE.md)** - Complete CLI parameter documentation
- **[Config Reference](CONFIG-REFERENCE.md)** - Configuration file guide
- **[Testing Guide](TESTING.md)** - Testing and validation procedures

## Features

✅ **Automatic Conversion**
- Converts Docker Compose services to Kubernetes Deployments/StatefulSets
- Generates Kubernetes Service objects for service discovery
- Configurable output format (YAML or JSON)

✅ **Flexible Configuration**
- Load defaults from `config.yml`
- Override with CLI arguments
- Per-service configuration via `dock2k8s.yaml`

✅ **Robust Error Handling**
- Validates input files and port formats
- Warns on unsupported Docker Compose features
- Verbose logging for debugging

✅ **Customization**
- Set default replicas and service types
- Configure PVC storage for volumes
- Handle service dependencies
- Control build warnings

✅ **Secrets Management**
- Generate Kubernetes Secrets from `.env` files
- Support for multiple secret types (Opaque, TLS, docker-registry)
- Secure secret creation workflow (not hardcoded in manifests)

## Installation

### Requirements
- Python 3.7+
- PyYAML

### Setup

```bash
pip install pyyaml
```

### Optional: Command-Line Alias Setup

#### Option 1: Windows Batch Wrapper (Recommended for Windows)

A `dock2k8s.bat` file is included in the project directory. To use it:

**Local Usage (in project directory):**
```bash
# From the Dock2K8s directory
dock2k8s -v
dock2k8s -f docker-compose.prod.yml
```

**Global Usage (from anywhere):**

1. Add the Dock2K8s directory to your PATH environment variable:
   ```powershell
   # In PowerShell (as Administrator)
   $dock2k8sPath = "C:\Users\gabri\OneDrive\Documents\Dock2K8s"
   [Environment]::SetEnvironmentVariable(
       "PATH",
       "$([Environment]::GetEnvironmentVariable('PATH', 'User'));$dock2k8sPath",
       "User"
   )
   ```

2. Restart your terminal and use from anywhere:
   ```bash
   dock2k8s -p C:\path\to\project -v
   ```

#### Option 2: PowerShell Wrapper

A `dock2k8s.ps1` PowerShell script is included. To use it:

```powershell
# Run from Dock2K8s directory
.\dock2k8s.ps1 -v
.\dock2k8s.ps1 -f docker-compose.prod.yml
```

To make it available globally, create a PowerShell profile alias:

```powershell
# Open PowerShell profile
notepad $PROFILE

# Add this line
Set-Alias -Name dock2k8s -Value "C:\Users\gabri\OneDrive\Documents\Dock2K8s\dock2k8s.ps1"

# Save and reload
. $PROFILE
```

#### Option 3: Manual PATH Configuration

If the batch file doesn't work, manually add to PATH:

1. Press `Win + X` → System
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `PATH`
6. Variable value: `C:\Users\gabri\OneDrive\Documents\Dock2K8s`
7. Click OK and restart terminal

Then use:
```bash
dock2k8s -v
dock2k8s -f docker-compose.prod.yml
```

## Quick Start

### 1. Basic Usage (No Config)

```bash
python cli.py
```

Converts `docker-compose.yml` in the current directory to Kubernetes manifests in `k8s/` directory.

### 2. With Configuration File

Create a `config.yml` in your project root:

```yaml
output_dir: k8s
verbose: false
format: yaml

defaults:
  replicas: 2
  controller: Deployment

workloads:
  elasticsearch:
    replicas: 1
  kibana:
    replicas: 1

services:
  elasticsearch:
    enabled: true
    type: ClusterIP
  kibana:
    enabled: true
    type: LoadBalancer
```

Then run:

```bash
python cli.py
```

### 3. Using CLI Arguments

Override config settings via command-line:

```bash
python cli.py --replicas 3 --service-type LoadBalancer --verbose
```

## Usage Guide

### CLI Parameters

```
Basic Options:
  -p, --project-dir DIR         Project directory (default: .)
  -c, --config FILE             Config file path (default: config.yml)
  -f, --file FILE               Docker Compose file name (default: docker-compose.yml)
  -v, --verbose                 Enable verbose output

Output Options:
  -o, --output-dir DIR          Output directory for K8s manifests
  --format {yaml,json}          Output format (default: yaml)

Kubernetes Defaults:
  --replicas N                  Default replicas for services
  --service-type TYPE           Default service type (ClusterIP, LoadBalancer, etc.)

Docker Compose Options:
  --docker-compose FILE         Docker Compose file name (alias for -f/--file)
  --dock2k8s-config FILE        Dock2K8s config file name (default: dock2k8s.yaml)

Feature Flags:
  --convert-volumes             Convert Docker volumes to PersistentVolumeClaims
  --pvc-size SIZE               Default PVC size (default: 10Gi)
  --no-depends-on               Skip handling depends_on relationships
```

> **For complete CLI documentation**, see [CLI-REFERENCE.md](CLI-REFERENCE.md)

#### Detailed Parameter Reference

##### Basic Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-p, --project-dir` | path | `.` (current dir) | Path to project containing docker-compose.yml. Can be absolute or relative. |
| `-c, --config` | filename | `config.yml` | Name/path of configuration file. Loaded from project directory. |
| `-f, --file` | filename | `docker-compose.yml` | Name of Docker Compose file in project directory. Shorter alias for `--docker-compose`. |
| `-v, --verbose` | flag | false | Print detailed conversion information. Useful for debugging. |

**Examples:**
```bash
# Use absolute path
python cli.py -p /home/user/myproject

# Use relative path
python cli.py -p ../other-project

# Use specific config file
python cli.py -c config-prod.yml

# Use specific docker-compose file (-f is shorter than --docker-compose)
python cli.py -f docker-compose.prod.yml

# Verbose output
python cli.py -v
```

##### Output Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-o, --output-dir` | path | `k8s` | Output directory for generated manifests. Overrides config.yml setting. |
| `--format` | choice | `yaml` | Output format: `yaml` or `json`. Overrides config.yml. |

**Format Details:**
- `yaml` - Kubernetes YAML (human-readable, kubectl compatible)
- `json` - JSON format (for programmatic processing)

**Examples:**
```bash
# Save to custom directory
python cli.py --output-dir ./manifests

# Generate JSON output
python cli.py --format json

# Custom dir and format
python cli.py -o ./k8s-manifests --format json
```

##### Kubernetes Defaults

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `--replicas` | integer | `1` | >= 1 | Set pod replicas for all services. Overrides config.yml and per-service settings. |
| `--service-type` | string | `ClusterIP` | Valid K8s type | Kubernetes service type. Options: `ClusterIP`, `NodePort`, `LoadBalancer`, `ExternalName`. |

**Service Types:**
- `ClusterIP` - Internal cluster access only (default)
- `NodePort` - Access via node IP + port (good for local development)
- `LoadBalancer` - Cloud provider load balancer (AWS, GCP, Azure)
- `ExternalName` - Maps to external DNS (advanced use case)

**Examples:**
```bash
# High availability setup
python cli.py --replicas 3 --service-type LoadBalancer

# Development with easy access
python cli.py --replicas 1 --service-type NodePort

# Single replica, internal only
python cli.py --replicas 1 --service-type ClusterIP
```

##### Docker Compose Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `-f, --file` | filename | `docker-compose.yml` | Docker Compose file name. Short form is recommended (follows Docker Compose convention). |
| `--docker-compose` | filename | - | Alias for `-f/--file`. Provided for backward compatibility. |
| `--dock2k8s-config` | filename | `dock2k8s.yaml` | Name of per-service configuration file. |

**Use Cases:**
- `-f` / `--file` - Specify custom Docker Compose file names like `docker-compose.prod.yml`
- `--docker-compose` - Legacy name, same as `-f/--file`
- `--dock2k8s-config` - Use environment-specific configs

**Examples:**
```bash
# Convert production compose file (short form)
python cli.py -f docker-compose.prod.yml

# Equivalent using long form
python cli.py --docker-compose docker-compose.prod.yml

# Use environment-specific config
python cli.py --dock2k8s-config dock2k8s.staging.yaml

# Combine file and config
python cli.py -f docker-compose.staging.yml --dock2k8s-config dock2k8s.staging.yaml
```

##### Feature Flags

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--convert-volumes` | flag | (from config) | Enable volume to PVC conversion. |
| `--pvc-size` | string | `10Gi` | Default storage size for converted PVCs. Format: `<number>Gi`, `<number>Mi`. |
| `--no-depends-on` | flag | false | Disable depends_on relationship handling. |

**Volume Conversion:**
When enabled, Docker Compose volumes are converted to Kubernetes PersistentVolumeClaims.

**Storage Size Format:**
```
10Gi   = 10 gigabytes
100Mi  = 100 megabytes
1Ti    = 1 terabyte
```

**Examples:**
```bash
# Enable volume conversion with custom size
python cli.py --convert-volumes --pvc-size 50Gi

# Disable dependency handling
python cli.py --no-depends-on

# Both options
python cli.py --convert-volumes --pvc-size 100Gi --no-depends-on
```

### Parameter Priority & Combinations

Parameters work together with the following priority:

**CLI Arguments > config.yml workloads/services > config.yml defaults > Hardcoded Defaults**

**Examples:**

```bash
# Scenario 1: CLI overrides everything
# config.yml defaults: replicas: 1
# CLI uses: --replicas 3
# Result: 3 replicas
python cli.py --replicas 3

# Scenario 2: Workload-specific override
# config.yml defaults: replicas: 2
# config.yml workloads.api: replicas: 5
# Result: api gets 5 replicas, others get 2
python cli.py

# Scenario 3: Config.yml provides defaults
# config.yml has: defaults.replicas: 2, verbose: true
# CLI has no replica/verbose override
# Result: Use config.yml values (2 replicas, verbose)
python cli.py
```

### Examples

#### Example 1: Basic Conversion

```bash
python cli.py --project-dir ./my-project
```

**Input:** `my-project/docker-compose.yml`
```yaml
services:
  web:
    image: myapp:1.0
    ports:
      - "8080:8080"
  db:
    image: postgres:14
    ports:
      - "5432:5432"
```

**Output:**
- `my-project/k8s/web-deployment.yaml`
- `my-project/k8s/web-service.yaml`
- `my-project/k8s/db-deployment.yaml`
- `my-project/k8s/db-service.yaml`

#### Example 2: With Custom Replicas

```bash
python cli.py --replicas 3 --service-type LoadBalancer
```

Sets all services to 3 replicas and LoadBalancer service type.

#### Example 3: JSON Output for Tooling

```bash
python cli.py --format json --output-dir ./manifests
```

Generates JSON manifests for programmatic processing.

#### Example 4: Verbose Output for Debugging

```bash
python cli.py -v
```

Displays:
- Project directory and file locations
- Config source (file or defaults)
- Service conversion details
- Warnings for unsupported features

#### Example 5: Multiple Services with Different Configs

**config.yml:**
```yaml
output_dir: k8s
defaults:
  replicas: 1
  controller: Deployment

workloads:
  api:
    replicas: 3
  database:
    replicas: 1
  cache:
    replicas: 2

services:
  api:
    enabled: true
    type: LoadBalancer
  database:
    enabled: true
    type: ClusterIP
  cache:
    enabled: true
    type: ClusterIP
```

**Command:**
```bash
python cli.py
```

**Result:**
- `api-deployment.yaml`: 3 replicas, LoadBalancer service
- `database-deployment.yaml`: 1 replica, ClusterIP service
- `cache-deployment.yaml`: 2 replicas, ClusterIP service

#### Example 6: Production Deployment with Volumes

**Command:**
```bash
python cli.py \
  --replicas 3 \
  --service-type LoadBalancer \
  --convert-volumes \
  --pvc-size 50Gi \
  --format yaml \
  -v
```

**Result:**
- 3 replicas for all services
- LoadBalancer service type for external access
- Docker volumes converted to PersistentVolumeClaims (50Gi each)
- YAML output with verbose logging

#### Example 7: Environment-Specific Configurations

**Setup:**
```
project/
  docker-compose.yml
  config.yml              # Defaults
  config-dev.yml          # Development overrides
  config-prod.yml         # Production overrides
```

**Development:**
```bash
python cli.py -c config-dev.yml
```

**Production:**
```bash
python cli.py -c config-prod.yml
```

#### Example 8: Custom Docker Compose File

```bash
# Using -f (short form, recommended)
python cli.py -f docker-compose.override.yml

# Equivalent using --docker-compose (long form)
python cli.py --docker-compose docker-compose.override.yml
```

Useful for:
- Using environment-specific compose files
- Testing different configurations
- Maintaining multiple service variations

#### Example 9: Combining file and config overrides

```bash
python cli.py -f docker-compose.prod.yml -c config-prod.yml --replicas 3
```

Uses custom docker-compose file, custom config file, and CLI override for replicas.

#### Example 10: Combining config.yml with CLI Overrides

**config.yml:**
```yaml
defaults:
  replicas: 2
  controller: Deployment
```

**Command:**
```bash
python cli.py --replicas 3
```

**Result:**
- CLI arguments override config.yml
- Final settings: 3 replicas (workload-specific would be overridden by CLI)

#### Example 11: Quiet Mode for Automation

```bash
python cli.py --format json
```

- No verbose output (quiet mode)
- JSON output for parsing by automation tools
- Perfect for CI/CD pipeline integration

## Configuration Reference

### config.yml Structure

The config.yml follows a structure similar to docker-compose.yml for a familiar syntax:

```yaml
# Global defaults (like x- fields in docker-compose)
defaults:
  replicas: 1
  controller: Deployment

# Output and input settings
output_dir: k8s
docker_compose_file: docker-compose.yml

# Logging and output
verbose: false
format: yaml

# Volume conversion
convert_volumes: true
pvc_storage_class: null
pvc_size: 10Gi

# Dependency handling
handle_depends_on: true
init_container_image: busybox:1.35

# Build handling
warn_on_build: true

# Workload-specific overrides (Pod/Deployment configuration)
workloads:
  elasticsearch:
    replicas: 1
    controller: Deployment
  kibana:
    replicas: 1
    controller: Deployment

# Service-specific overrides (Kubernetes Service configuration)
services:
  elasticsearch:
    enabled: true
    type: ClusterIP
  kibana:
    enabled: true
    type: ClusterIP
```

> **For detailed configuration documentation**, see [CONFIG-REFERENCE.md](CONFIG-REFERENCE.md)

### Parameter Definitions

#### File & Directory Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_dir` | string | `k8s` | Directory where Kubernetes manifests will be saved. Created if doesn't exist. |
| `docker_compose_file` | string | `docker-compose.yml` | Name of Docker Compose file to convert. Must exist in project root. |
| `config_file` | string | `dock2k8s.yaml` | Name of per-service configuration file. Optional, no error if missing. |

**Examples:**
```yaml
# Use different docker-compose files
output_dir: kubernetes
docker_compose_file: docker-compose.prod.yml
config_file: dock2k8s.prod.yaml
```

#### Logging & Output Settings

| Parameter | Type | Default | Values | Description |
|-----------|------|---------|--------|-------------|
| `verbose` | boolean | `false` | `true`, `false` | Print detailed conversion process information and warnings. |
| `format` | string | `yaml` | `yaml`, `json` | Output format for generated manifests. |

**Verbose Output Includes:**
- Project directory and file paths
- Config source (file vs defaults)
- Service conversion progress
- Warnings for unsupported features
- Completion summary

**Format Details:**
- `yaml` - Standard Kubernetes YAML manifests (human-readable, kubectl compatible)
- `json` - JSON manifests (for programmatic processing, CI/CD pipelines)

**Examples:**
```yaml
# Development setup - verbose for debugging
verbose: true
format: yaml

# Automated pipeline - JSON for tool integration
verbose: false
format: json
```

#### Kubernetes Defaults

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `defaults.replicas` | integer | `1` | >= 1 | Number of pod replicas for all workloads without specific overrides. |
| `defaults.controller` | string | `Deployment` | `Deployment`, `StatefulSet` | Kubernetes controller type for all workloads without specific overrides. |

**Controller Type Explanations:**
- `Deployment` - For stateless applications (web servers, APIs)
- `StatefulSet` - For stateful applications (databases, caches)

**Examples:**
```yaml
# High-availability setup
defaults:
  replicas: 3
  controller: Deployment

# Development (low resource)
defaults:
  replicas: 1
  controller: Deployment

# Stateful service
defaults:
  replicas: 1
  controller: StatefulSet
```

#### Volume Conversion

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `convert_volumes` | boolean | `true` | Whether to convert Docker volumes to PersistentVolumeClaims. |
| `pvc_storage_class` | string/null | `null` | Kubernetes storage class to use for PVCs. `null` uses cluster default. |
| `pvc_size` | string | `10Gi` | Default size for generated PVCs. Format: `<number>Gi`, `<number>Mi`, etc. |

**Storage Class Examples:**
```yaml
# Use cluster default storage class
pvc_storage_class: null

# Use specific fast storage
pvc_storage_class: fast-ssd

# Use slow/cheap storage for backups
pvc_storage_class: standard
```

**Storage Size Examples:**
```yaml
pvc_size: 1Gi      # 1 gigabyte
pvc_size: 100Mi    # 100 megabytes
pvc_size: 1Ti      # 1 terabyte
```

**Examples:**
```yaml
# Stateful application with persistent storage
convert_volumes: true
pvc_storage_class: fast-ssd
pvc_size: 50Gi

# Stateless application (no volumes)
convert_volumes: false
```

#### Dependency Handling

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `handle_depends_on` | boolean | `true` | Create init containers to handle `depends_on` relationships from docker-compose. |
| `init_container_image` | string | `busybox:1.35` | Image to use for init containers (for checking service availability). |

**How It Works:**
When a service has `depends_on` relationships, an init container starts first to wait for dependencies to be ready.

**Examples:**
```yaml
# Enable dependency handling with default busybox
handle_depends_on: true
init_container_image: busybox:1.35

# Disable dependency handling (manual or init containers)
handle_depends_on: false

# Use custom init container image
handle_depends_on: true
init_container_image: mycompany/wait-for:latest
```

#### Build Handling

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `warn_on_build` | boolean | `true` | Print warning when Docker Compose has `build` directives (only `image` is used). |

**Behavior:**
- When `true`: Warns if docker-compose.yml uses `build:` instead of `image:`
- When `false`: Silently ignores `build:` sections

**Examples:**
```yaml
# Development - show all warnings
warn_on_build: true

# Automated conversion - suppress warnings
warn_on_build: false
```

#### Per-Service Overrides

The `services` section allows per-service configuration:

```yaml
services:
  service_name:
    replicas: N              # Override default_replicas for this service
    service_type: TYPE       # Override default_service_type for this service
```

**Examples:**
```yaml
workloads:
  # Web service needs high availability
  web:
    replicas: 5
  
  # Database can be single replica
  database:
    replicas: 1
  
  # Cache doesn't need high availability
  redis:
    replicas: 1

services:
  web:
    enabled: true
    type: LoadBalancer
  
  database:
    enabled: true
    type: ClusterIP
  
  redis:
    enabled: true
    type: ClusterIP
```

### Complete config.yml Examples

#### Example 1: Development Environment

```yaml
# Development - quick iteration, minimal resources
output_dir: k8s
verbose: true
format: yaml

defaults:
  replicas: 1
  controller: Deployment

convert_volumes: false
warn_on_build: true
```

#### Example 2: Production Environment

```yaml
# Production - high availability, persistent storage
output_dir: k8s-prod
verbose: false
format: yaml

defaults:
  replicas: 3
  controller: Deployment

convert_volumes: true
pvc_storage_class: fast-ssd
pvc_size: 100Gi

workloads:
  elasticsearch:
    replicas: 3
  kibana:
    replicas: 2
  cache:
    replicas: 1

services:
  elasticsearch:
    enabled: true
    type: LoadBalancer
  kibana:
    enabled: true
    type: LoadBalancer
  cache:
    enabled: true
    type: ClusterIP
```

#### Example 3: Staging Environment

```yaml
# Staging - balanced approach
output_dir: k8s-staging
verbose: true
format: yaml

defaults:
  replicas: 2
  controller: Deployment

convert_volumes: true
pvc_storage_class: standard
pvc_size: 50Gi

services:
  api:
    replicas: 2
  database:
    replicas: 1
```

#### Example 4: CI/CD Pipeline

```yaml
# Automated tooling - JSON output for parsing
output_dir: ./manifests
verbose: false
format: json

default_replicas: 1
default_service_type: ClusterIP

convert_volumes: false
warn_on_build: false
```

### dock2k8s.yaml (Per-Service Config)

Optional file for service-specific overrides:

```yaml
services:
  elasticsearch:
    controller: Deployment         # Deployment or StatefulSet
    replicas: 1
    service:
      enabled: true
      type: ClusterIP
  
  kibana:
    controller: Deployment
    replicas: 2
    service:
      enabled: true
      type: LoadBalancer
```

## Configuration Precedence

When the same setting appears in multiple places, precedence is:

1. **CLI Arguments** (highest priority)
2. **config.yml** file
3. **Defaults** (lowest priority)

Example:
```bash
# config.yml has: default_replicas: 1
# CLI has: --replicas 3
# Result: 3 replicas are used
python cli.py --replicas 3
```

## Generated Manifest Structure

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: service-name
spec:
  replicas: 1
  selector:
    matchLabels:
      app: service-name
  template:
    metadata:
      labels:
        app: service-name
    spec:
      containers:
      - name: service-name
        image: service-image:tag
        ports:
        - containerPort: 8080
        env:
        - name: ENV_VAR
          value: "value"
```

### Service Manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: service-name
spec:
  selector:
    app: service-name
  ports:
  - port: 8080
    targetPort: 8080
  type: ClusterIP
```

## Workflow

```
1. Load config.yml (if exists)
2. Parse CLI arguments
3. Merge: CLI > config.yml > defaults
4. Load docker-compose.yml
5. Load dock2k8s.yaml (if exists)
6. For each service:
   - Generate Deployment/StatefulSet manifest
   - Generate Service manifest (if ports exist)
   - Write to output_dir with format (YAML/JSON)
7. Display results with verbose logging
```

## Common Workflows

### Scenario 1: Development Environment

```bash
# config.yml
default_replicas: 1
default_service_type: ClusterIP
verbose: false

# Run
python cli.py
```

### Scenario 2: Production Deployment

```bash
# config.yml
default_replicas: 3
default_service_type: LoadBalancer
convert_volumes: true
pvc_size: 50Gi

# Run with additional customizations
python cli.py --replicas 5 --pvc-size 100Gi -v
```

### Scenario 3: Multi-Environment Setup

```bash
# Generate for staging
python cli.py -c config-staging.yml -o staging/

# Generate for production
python cli.py -c config-prod.yml -o production/
```

### Scenario 4: CI/CD Pipeline

```bash
# Generate JSON output for automation
python cli.py --format json --output-dir ./manifests

# Use output in automation tools
kubectl apply -f manifests/
```

## Build Handling

### Overview

Kubernetes doesn't support building Docker images from Dockerfiles like Docker Compose does. Instead, it requires pre-built images from a registry.

### How It Works

When you use `build` directives in your `docker-compose.yml`:

```yaml
# ❌ Docker Compose (has build directive)
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: myapp:1.0
    ports:
      - "8080:8080"
```

Dock2K8s will:

1. **Ignore the `build` section** - Kubernetes manifests can't include build instructions
2. **Use only the `image` field** - References `myapp:1.0`
3. **Show a warning** (if `warn_on_build: true` in config)

### Generated Kubernetes Manifest

```yaml
# ✅ Kubernetes (no build, only image)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:1.0  # Only image, no build
        ports:
        - containerPort: 8080
```

### Configuration

**In config.yml:**
```yaml
warn_on_build: true   # Show warnings (default)
warn_on_build: false  # Suppress warnings
```

### What You Need to Do

To use Dock2K8s with Docker Compose files that have `build` directives:

1. **Build your Docker images:**
   ```bash
   docker build -t myregistry/myapp:1.0 .
   ```

2. **Push to a registry:**
   ```bash
   docker push myregistry/myapp:1.0
   ```

3. **Update docker-compose.yml** to use the pushed image:
   ```yaml
   services:
     app:
       image: myregistry/myapp:1.0  # Change this
       ports:
         - "8080:8080"
   ```

4. **Convert:**
   ```bash
   dock2k8s -v
   ```

### Example Workflow

**Before (Docker Compose with build):**
```yaml
version: '3'
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
```

**Step 1: Build & Push**
```bash
docker build -t mycompany/backend:1.0 ./backend
docker push mycompany/backend:1.0
```

**After (Ready for Kubernetes):**
```yaml
version: '3'
services:
  backend:
    image: mycompany/backend:1.0
    ports:
      - "8000:8000"
```

**Convert:**
```bash
dock2k8s -v

# Output:
# ✔ backend → Deployment
# ✅ Conversion complete!
```

### Supported Image Formats

```yaml
# Public Docker Hub
image: nginx:latest
image: postgres:14

# Private registry
image: myregistry.com/myapp:1.0
image: gcr.io/myproject/myapp:1.0
image: 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0
```

## Limitations & Known Behavior

⚠️ **Not Supported:**
- `build` context (uses `image` field only) - see [Build Handling](#build-handling)
- Volume mounts (conversion not yet implemented)
- Health checks
- Resource limits (CPU/memory)
- Init containers (for `depends_on`)
- Restart policies

⚠️ **Notes:**
- Environment variables are passed as simple key-value pairs
- Port parsing expects `HOST:CONTAINER` format
- Generated manifests require Kubernetes 1.19+

## Troubleshooting

### Issue: "docker-compose.yml not found"
```
FileNotFoundError: 'docker-compose.yml' not found
```
**Solution:** Ensure you're in the correct project directory or use `-p`:
```bash
python cli.py -p /path/to/project
```

### Issue: Warnings about build directives
```
⚠️  service-name: 'build' field ignored (using 'image' only)
```
**Solution:** Ensure your `docker-compose.yml` has `image` fields for all services. Disable warnings:
```bash
# Create config.yml with:
warn_on_build: false
```

### Issue: Port parsing failures
**Solution:** Ensure ports are in `HOST:CONTAINER` format:
```yaml
# ✅ Correct
ports:
  - "8080:8080"

# ❌ Incorrect
ports:
  - "8080"
```

## Secrets Management

Dock2K8s supports automatic Kubernetes Secret generation from `.env` files. This provides a secure way to manage sensitive data like database passwords, API keys, and tokens.

### Quick Start with Secrets

1. **Create `.env` file** (or copy `.env.example`):
```bash
DATABASE_PASSWORD=postgres123
API_KEY=sk_live_1234567890abcdef
JWT_SECRET=your-secret-key-here
```

2. **Configure in `config.yml`**:
```yaml
secrets:
  app-secrets:
    enabled: true
    type: Opaque
    data:
      DATABASE_PASSWORD: null    # null = read from .env
      API_KEY: null
      JWT_SECRET: null
```

3. **Run conversion**:
```bash
python cli.py
```

Output: `k8s/app-secrets-secret.yaml` (with base64-encoded values)

### Using Secrets in Deployments

Once the Secret is created, use it in your pods:

```bash
# Create the secret in Kubernetes
kubectl apply -f k8s/app-secrets-secret.yaml

# Or create from .env directly (recommended for production)
kubectl create secret generic app-secrets --from-env-file=.env
```

Then reference it in your deployment:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  template:
    spec:
      containers:
      - name: api
        image: myapp/api:1.0
        envFrom:
        - secretRef:
            name: app-secrets  # Reference by name
```

### Security Best Practices

⚠️ **Important:** The generated Secret YAML contains base64-encoded values (not encrypted). For production:

1. **Never commit `.env` files to git** (add to `.gitignore`)
2. **Never commit Secret YAML files** with real values
3. **Create secrets via `kubectl` or external secret managers:**
   ```bash
   # Recommended: Create from .env
   kubectl create secret generic app-secrets --from-env-file=.env
   
   # Or use a secret manager
   kubectl apply -f secret-from-vault.yaml
   ```

### Supported Secret Types

- `Opaque` (default) - Generic key-value secrets
- `kubernetes.io/dockercfg` - Docker registry credentials
- `kubernetes.io/dockerconfigjson` - Docker registry config
- `kubernetes.io/basic-auth` - Username/password
- `kubernetes.io/ssh-auth` - SSH private key
- `kubernetes.io/tls` - TLS certificate + key

### Multiple Secrets Example

```yaml
secrets:
  # Database credentials
  db-credentials:
    enabled: true
    type: Opaque
    data:
      DATABASE_PASSWORD: null
      DATABASE_USER: null
  
  # API keys
  api-keys:
    enabled: true
    type: Opaque
    data:
      STRIPE_KEY: null
      JWT_SECRET: null
  
  # Docker registry
  docker-registry:
    enabled: true
    type: kubernetes.io/dockerconfigjson
    data:
      .dockerconfigjson: null
```

## Future Enhancements

- [ ] Volume → PersistentVolumeClaim conversion
- [ ] Init containers for depends_on handling
- [ ] Resource limits support
- [ ] Health checks → Readiness/Liveness probes
- [ ] Web UI for visualization
- [ ] Manifest validation
- [ ] Helm chart generation

## Implementation Status

### ✅ Completed Features

- [x] **Basic Conversion** - Docker Compose → Kubernetes Deployments/StatefulSets
- [x] **Service Discovery** - Generate Kubernetes Service objects
- [x] **Volume Handling** - Convert volumes to PersistentVolumeClaims
- [x] **CLI Parameters** - Flexible command-line arguments
- [x] **Configuration File** - config.yml with defaults, workloads, services sections
- [x] **Environment Variables** - Handle both dict and list formats from docker-compose
- [x] **Dependency Management** - Init containers for depends_on handling
- [x] **Secrets Generation** - Parse .env files and create Kubernetes Secrets
- [x] **Multiple Secret Types** - Opaque, docker-registry, TLS, basic-auth, etc.
- [x] **Build Warnings** - Alert on unsupported docker-compose features
- [x] **Output Formats** - YAML and JSON manifest generation
- [x] **Documentation** - Comprehensive README, CLI-REFERENCE, CONFIG-REFERENCE, TESTING guide

### 🚧 Planned Features

- [ ] **Ingress** - HTTP routing and TLS termination
- [ ] **Resource Limits** - CPU and memory constraints per workload
- [ ] **Health Checks** - Map Docker healthchecks to K8s readiness/liveness probes
- [ ] **ConfigMaps** - Generate ConfigMaps for application configuration
- [ ] **Advanced Secrets** - Vault/AWS Secrets Manager integration
- [ ] **Helm Chart Generation** - Package manifests as Helm charts
- [ ] **Web UI** - Visual configuration builder
- [ ] **Manifest Validation** - Pre-deployment validation and checks
- [ ] **Namespace Management** - Multi-namespace support
- [ ] **RBAC** - ServiceAccount and Role definitions

## License

MIT

## Contributing

Contributions welcome! Priority areas:
- Ingress support
- Resource limits and constraints
- Health check mapping
- ConfigMap support
- Additional test coverage
- Performance optimizations
