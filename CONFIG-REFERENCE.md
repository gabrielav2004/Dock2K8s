# Configuration Reference

Complete reference for Dock2K8s configuration: `config.yml`

## Overview

Dock2K8s uses a single configuration file: `config.yml`

The file separates **workload configuration** (Pod/Deployment settings) from **service configuration** (Kubernetes Service settings), avoiding confusion between Docker Compose "services" (containers) and Kubernetes "services" (network objects).

## config.yml

The main configuration file. Loaded from your project root directory.

### Structure

```yaml
# Global defaults applied to all workloads
defaults:
  replicas: 1
  controller: Deployment

# Output and input settings
output_dir: k8s
docker_compose_file: docker-compose.yml

# Logging and output
verbose: false
format: yaml

# Volume handling
convert_volumes: true
pvc_storage_class: null
pvc_size: 10Gi

# Dependency handling
handle_depends_on: true
init_container_image: busybox:1.35

# Build handling
warn_on_build: true

# ============================================================================
# WORKLOADS - Pod/Deployment configuration (mirrors docker-compose structure)
# ============================================================================
workloads:
  service-name:
    replicas: 1
    controller: Deployment

# ============================================================================
# SERVICES - Kubernetes Service configuration (separate concern)
# ============================================================================
services:
  service-name:
    enabled: true
    type: ClusterIP
```

### Key Concept: Workloads vs Services

This configuration intentionally separates two Kubernetes concerns:

**Workloads** - Pod/Deployment configuration
- `replicas` - Number of pod replicas
- `controller` - Deployment or StatefulSet

**Services** - Network abstraction for workloads
- `enabled` - Whether to create a Kubernetes Service
- `type` - Service type (ClusterIP, NodePort, LoadBalancer, ExternalName)

#### `verbose`

```yaml
verbose: false
```

**Type:** Boolean  
**Default:** `false`  
**Options:** `true`, `false`  
**Description:** Enable verbose output during conversion

#### `format`

```yaml
format: yaml
```

**Type:** String  
**Default:** `yaml`  
**Options:** `yaml`, `json`  
**Description:** Output format for manifests

### Volume Settings

#### `convert_volumes`

```yaml
convert_volumes: true
```

**Type:** Boolean  
**Default:** `true`  
**Description:** Convert Docker volumes to PersistentVolumeClaims

#### `pvc_storage_class`

```yaml
pvc_storage_class: null
```

**Type:** String or null  
**Default:** `null` (uses cluster default)  
**Description:** Kubernetes storage class for PVCs

**Examples:**
```yaml
# Use cluster default
pvc_storage_class: null

# Specific storage class
pvc_storage_class: fast-ssd

# Standard/slow storage
pvc_storage_class: standard
```

#### `pvc_size`

```yaml
pvc_size: 10Gi
```

**Type:** String (with unit)  
**Default:** `10Gi`  
**Format:** `<number>Gi|Mi|Ti`  
**Description:** Default size for created PersistentVolumeClaims

**Examples:**
```yaml
pvc_size: 5Gi      # 5 gigabytes
pvc_size: 100Mi    # 100 megabytes
pvc_size: 1Ti      # 1 terabyte
```

### Dependency Settings

#### `handle_depends_on`

```yaml
handle_depends_on: true
```

**Type:** Boolean  
**Default:** `true`  
**Description:** Process Docker Compose `depends_on` relationships

**When enabled:**
- Creates init containers to wait for dependencies
- Service waits for dependencies to be ready

**When disabled:**
- Ignores `depends_on` directives
- Services start independently

#### `init_container_image`

```yaml
init_container_image: busybox:1.35
```

**Type:** String (Docker image)  
**Default:** `busybox:1.35`  
**Description:** Image used for init containers

**Examples:**
```yaml
# Standard busybox
init_container_image: busybox:1.35

# Alpine linux
init_container_image: alpine:latest

# Custom image
init_container_image: mycompany/wait-for:latest
```

### Build Settings

#### `warn_on_build`

```yaml
warn_on_build: true
```

**Type:** Boolean  
**Default:** `true`  
**Description:** Warn when Docker Compose uses `build` directives

**When enabled:**
```
⚠️  service-name: 'build' field ignored (using 'image' only)
```

**When disabled:**
- No warnings about `build` fields
- Still uses `image` field only

### Service-Specific Overrides

Like docker-compose.yml, you can define per-workload and per-service settings:

```yaml
workloads:
  web:
    replicas: 3
  
  api:
    replicas: 2
  
  cache:
    replicas: 1

services:
  web:
    enabled: true
    type: LoadBalancer
  
  api:
    enabled: true
    type: ClusterIP
  
  cache:
    enabled: false  # Internal workload, no service
```

**Available options per workload:**
- `replicas` - Override default replicas
- `controller` - Override default controller (Deployment/StatefulSet)

**Available options per service:**
- `enabled` - Whether to create a Kubernetes Service (default: true)
- `type` - Override default service type (ClusterIP/NodePort/LoadBalancer/ExternalName)

## config.yml Examples

### Example 1: Development

```yaml
# Development: quick iteration, minimal resources
defaults:
  replicas: 1
  controller: Deployment

output_dir: k8s
verbose: true
format: yaml

convert_volumes: false
warn_on_build: true
```

### Example 2: Production

```yaml
# Production: high availability, persistent storage
defaults:
  replicas: 3
  controller: Deployment

output_dir: k8s
verbose: false
format: yaml

convert_volumes: true
pvc_storage_class: fast-ssd
pvc_size: 100Gi

workloads:
  api:
    replicas: 3
  
  database:
    replicas: 1
    controller: StatefulSet
  
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

### Example 3: Staging

```yaml
# Staging: balanced approach
defaults:
  replicas: 2
  controller: Deployment

output_dir: k8s
verbose: true
format: yaml

convert_volumes: true
pvc_storage_class: standard
pvc_size: 50Gi

workloads:
  api:
    replicas: 2
  
  database:
    replicas: 1
    controller: StatefulSet

services:
  api:
    enabled: true
    type: LoadBalancer
```

### Example 4: CI/CD Pipeline

```yaml
# Automated tooling: JSON output for parsing
defaults:
  replicas: 1
  controller: Deployment

output_dir: manifests
verbose: false
format: json

convert_volumes: false
warn_on_build: false
```

## Workloads and Services Configuration Examples

### Example 1: Mixed Configuration

```yaml
services:
  frontend:
    controller: Deployment
    replicas: 3
    service:
      enabled: true
      type: LoadBalancer
  
  backend:
    controller: Deployment
    replicas: 2
    service:
      enabled: true
      type: ClusterIP
  
  database:
    controller: StatefulSet
    replicas: 1
    service:
      enabled: false  # No service for internal DB
```

### Example 2: Production Setup

```yaml
services:
  api:
    controller: Deployment
    replicas: 5
    service:
      enabled: true
      type: LoadBalancer
  
  worker:
    controller: Deployment
    replicas: 3
    service:
      enabled: false  # Workers don't need external service
  
  postgres:
    controller: StatefulSet
    replicas: 1
    service:
      enabled: true
      type: ClusterIP
```

### Example 3: Development Setup

```yaml
services:
  app:
    controller: Deployment
    replicas: 1
    service:
      enabled: true
      type: NodePort  # Easy local access
```

## Configuration Precedence

Settings are applied in this order (highest to lowest priority):

1. **CLI Arguments** - `dock2k8s --replicas 3`
2. **config.yml** - Per-workload or service overrides
3. **config.yml defaults** - Global defaults
4. **Hardcoded Defaults** - Built-in values

**Example:**

```bash
# config.yml defaults say: replicas: 1
# config.yml workloads say: api.replicas: 2
# CLI says: --replicas 3

# Result: 3 replicas (CLI wins)
dock2k8s --replicas 3
```

## File Locations

```
project-root/
├── docker-compose.yml          # Your docker-compose file
├── config.yml                   # Dock2K8s config (defaults, workloads, services)
└── k8s/                         # Generated Kubernetes manifests
    ├── service1-deployment.yaml
    ├── service1-service.yaml
    └── ...
```

## Template Example

Here's a complete working example:

### docker-compose.yml

```yaml
version: '3.8'
services:
  api:
    image: myapp/api:1.0
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
  
  database:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=secret
```

### config.yml

```yaml
defaults:
  replicas: 1
  controller: Deployment

output_dir: k8s
verbose: true
format: yaml

workloads:
  api:
    replicas: 2
    controller: Deployment
  
  database:
    replicas: 1
    controller: StatefulSet

services:
  api:
    enabled: true
    type: LoadBalancer
  
  database:
    enabled: true
    type: ClusterIP
```

## Common Configurations

### Minimal Config

```yaml
# Use all defaults
defaults:
  replicas: 1
  service_type: ClusterIP
```

### High Availability

```yaml
defaults:
  replicas: 3
  service_type: LoadBalancer

convert_volumes: true
pvc_size: 50Gi
```

### Development Only

```yaml
defaults:
  replicas: 1
  service_type: ClusterIP

verbose: true
convert_volumes: false
warn_on_build: false
```

### Microservices

```yaml
defaults:
  replicas: 2
  controller: Deployment

workloads:
  api-gateway:
    replicas: 3
  
  auth-service:
    replicas: 2
  
  user-service:
    replicas: 2
  
  payment-service:
    replicas: 1

services:
  api-gateway:
    enabled: true
    type: LoadBalancer
  
  auth-service:
    enabled: true
    type: ClusterIP
  
  user-service:
    enabled: true
    type: ClusterIP
  
  payment-service:
    enabled: false  # Internal service
```

## Tips & Best Practices

1. **Start with defaults** - Only override what you need
2. **Use environment-specific configs** - `config-prod.yml`, `config-dev.yml`
3. **Keep config.yml in version control** - Commit it with your repo
4. **Document custom settings** - Add comments explaining non-obvious choices
5. **Test locally first** - Use dev config before production

## Troubleshooting

### "Config file not found"

**Normal behavior** - config.yml is optional. Uses defaults if missing.

### Settings not applied for a specific workload

**Check your config.yml:** Ensure the workload is defined in the `workloads` section (or `services` section for service settings).

```yaml
workloads:
  myservice:  # Must match docker-compose service name
    replicas: 2
```

### Settings not being applied

**Check precedence:**
```bash
# CLI args override everything
dock2k8s --replicas 5

# Check what config.yml has
cat config.yml | grep replicas

# Verify with verbose mode
dock2k8s -v
```

### "Invalid storage class"

Ensure storage class exists in your Kubernetes cluster:
```bash
kubectl get storageclass
```
