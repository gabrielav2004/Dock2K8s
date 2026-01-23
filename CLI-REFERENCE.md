# CLI Reference

Complete reference for all Dock2K8s command-line parameters.

## Quick Reference

```bash
dock2k8s [OPTIONS]
```

## All Parameters

| Short | Long | Type | Default | Description |
|-------|------|------|---------|-------------|
| `-p` | `--project-dir` | path | `.` | Project directory |
| `-c` | `--config` | file | `config.yml` | Config file path |
| `-f` | `--file` | file | - | Docker Compose file name |
| `-o` | `--output-dir` | path | `k8s` | Output directory |
| `-v` | `--verbose` | flag | false | Verbose output |
| | `--format` | yaml\|json | `yaml` | Output format |
| | `--replicas` | int | 1 | Default pod replicas |
| | `--service-type` | string | ClusterIP | Kubernetes service type |
| | `--docker-compose` | file | - | Docker Compose file (alias for -f) |
| | `--convert-volumes` | flag | - | Enable volume conversion |
| | `--pvc-size` | string | 10Gi | PVC default size |
| | `--no-depends-on` | flag | false | Disable depends_on handling |

## Detailed Parameter Guide

### Basic Options

#### `-p, --project-dir PATH`

**Type:** Path  
**Default:** `.` (current directory)  
**Description:** Path to project containing docker-compose.yml

**Behavior:**
- Accepts absolute or relative paths
- Looks for docker-compose.yml in this directory
- Creates k8s/ output directory here

**Examples:**
```bash
# Current directory
dock2k8s

# Absolute path
dock2k8s -p /home/user/myproject

# Relative path
dock2k8s -p ../other-project

# Nested path
dock2k8s -p ./projects/staging
```

#### `-c, --config FILE`

**Type:** Filename  
**Default:** `config.yml`  
**Description:** Configuration file path (loaded from project directory)

**Behavior:**
- Looks for file in project directory
- No error if file doesn't exist (uses defaults)
- Can be relative or absolute path

**Examples:**
```bash
# Default config.yml
dock2k8s

# Environment-specific config
dock2k8s -c config-prod.yml

# Development config
dock2k8s -c config-dev.yml

# Absolute path
dock2k8s -c /etc/dock2k8s/config.yml
```

#### `-f, --file FILE`

**Type:** Filename  
**Default:** `docker-compose.yml`  
**Description:** Docker Compose file name (in project directory)

**Behavior:**
- Follows Docker Compose convention (shorter than `--docker-compose`)
- File must exist in project directory
- If both `-f` and `--docker-compose` provided, `-f` takes precedence

**Examples:**
```bash
# Production compose file
dock2k8s -f docker-compose.prod.yml

# Staging compose file
dock2k8s -f docker-compose.staging.yml

# Custom name
dock2k8s -f docker-stack.yml
```

#### `-v, --verbose`

**Type:** Flag (no argument)  
**Default:** false  
**Description:** Enable detailed logging output

**Output includes:**
- Project root path
- Config file location
- Services being converted
- Warnings and errors
- Conversion summary

**Examples:**
```bash
# Show detailed conversion process
dock2k8s -v

# Verbose + other options
dock2k8s -v -f docker-compose.prod.yml
```

### Output Options

#### `-o, --output-dir PATH`

**Type:** Path  
**Default:** `k8s`  
**Description:** Output directory for generated Kubernetes manifests

**Behavior:**
- Creates directory if doesn't exist
- Overrides `output_dir` from config.yml
- CLI value takes precedence

**Examples:**
```bash
# Default location (k8s/)
dock2k8s

# Custom location
dock2k8s -o kubernetes

# Absolute path
dock2k8s -o /var/manifests

# Environment-specific
dock2k8s -o k8s-prod
```

#### `--format FORMAT`

**Type:** Choice: `yaml` or `json`  
**Default:** `yaml`  
**Description:** Output format for generated manifests

**Behavior:**
- `yaml` - Human-readable Kubernetes YAML
- `json` - JSON format for programmatic parsing
- Overrides `format` in config.yml

**Examples:**
```bash
# YAML output (default, human-readable)
dock2k8s --format yaml

# JSON output (for automation)
dock2k8s --format json

# Shorthand (YAML is default)
dock2k8s
```

### Kubernetes Settings

#### `--replicas N`

**Type:** Integer  
**Default:** 1  
**Constraints:** >= 1  
**Description:** Default pod replicas for all services

**Behavior:**
- Applied to all workloads without specific overrides
- Overrides `defaults.replicas` in config.yml
- Can be overridden per-workload in config.yml `workloads` section

**Examples:**
```bash
# High availability (3 replicas)
dock2k8s --replicas 3

# Single instance
dock2k8s --replicas 1

# Scale up for production
dock2k8s --replicas 5
```

#### `--service-type TYPE`

**Type:** String  
**Default:** `ClusterIP`  
**Valid Values:** 
- `ClusterIP` - Internal cluster access only
- `NodePort` - Access via node IP + port
- `LoadBalancer` - Cloud provider load balancer
- `ExternalName` - Maps to external DNS

**Description:** Kubernetes Service type for all services

**Behavior:**
- Applied to all services without specific overrides
- Overrides service config in config.yml
- Service-specific configs use the `services` section in config.yml

**Service Type Guide:**
| Type | Use Case | Access |
|------|----------|--------|
| ClusterIP | Internal services | In-cluster only |
| NodePort | Local development | `node-ip:port` |
| LoadBalancer | Production external | Cloud load balancer |
| ExternalName | External APIs | DNS name |

**Examples:**
```bash
# Internal service (default)
dock2k8s --service-type ClusterIP

# Easy local access
dock2k8s --service-type NodePort

# Production with load balancer
dock2k8s --service-type LoadBalancer

# External DNS mapping
dock2k8s --service-type ExternalName
```

### Docker Compose Options

#### `-f, --file FILE` (see [Basic Options](#basic-options) above)

#### `--docker-compose FILE`

**Type:** Filename  
**Default:** (none, use `-f` instead)  
**Description:** Alias for `-f/--file` (provided for backward compatibility)

**Behavior:**
- Same as `-f/--file`
- If both provided, `-f` takes precedence
- Use `-f` (shorter form)

**Examples:**
```bash
# Recommended: use -f
dock2k8s -f docker-compose.prod.yml

# Also works: longer form
dock2k8s --docker-compose docker-compose.prod.yml
```

### Volume Options

#### `--convert-volumes`

**Type:** Flag (no argument)  
**Default:** (from config.yml, default: true)  
**Description:** Enable conversion of Docker volumes to PersistentVolumeClaims

**Behavior:**
- Converts Docker volumes to Kubernetes PersistentVolumeClaims
- Uses `pvc_size` for storage size
- Uses `pvc_storage_class` for storage class

**Examples:**
```bash
# Enable volume conversion (may be default in config)
dock2k8s --convert-volumes

# Convert with specific size
dock2k8s --convert-volumes --pvc-size 50Gi
```

#### `--pvc-size SIZE`

**Type:** String (with unit)  
**Default:** `10Gi`  
**Format:** `<number>Gi|Mi|Ti`

**Description:** Default storage size for converted PersistentVolumeClaims

**Size Units:**
```
10Gi   = 10 gigabytes
100Mi  = 100 megabytes
1Ti    = 1 terabyte
```

**Examples:**
```bash
# Small volumes
dock2k8s --convert-volumes --pvc-size 5Gi

# Large volumes for databases
dock2k8s --convert-volumes --pvc-size 100Gi

# Terabyte scale
dock2k8s --convert-volumes --pvc-size 1Ti
```

### Dependency Options

#### `--no-depends-on`

**Type:** Flag (no argument)  
**Default:** false (handle dependencies)  
**Description:** Disable handling of Docker Compose `depends_on` relationships

**Behavior:**
- When enabled: Creates init containers to wait for dependencies
- When disabled (`--no-depends-on`): Ignores `depends_on` directives
- Useful when managing dependencies manually

**Examples:**
```bash
# Handle dependencies automatically (default)
dock2k8s

# Disable dependency handling
dock2k8s --no-depends-on

# Combine with other options
dock2k8s -v --no-depends-on
```

## Parameter Precedence

When the same setting appears in multiple places:

**Priority (highest to lowest):**
1. CLI Arguments
2. config.yml file
3. Defaults (hardcoded)

**Example:**
```bash
# config.yml defaults: replicas: 2
# CLI has: --replicas 3
# Result: 3 replicas (CLI wins)
dock2k8s --replicas 3
```

## Common Usage Patterns

### Development Setup

```bash
dock2k8s -v -c config-dev.yml -f docker-compose.dev.yml
```

### Production Deployment

```bash
dock2k8s \
  -f docker-compose.prod.yml \
  -c config-prod.yml \
  -o manifests-prod \
  --replicas 3 \
  --service-type LoadBalancer
```

### Automated Pipeline

```bash
dock2k8s \
  -f docker-compose.yml \
  --format json \
  -o ./manifests \
  --no-depends-on
```

### Quick Testing

```bash
dock2k8s -v
```

### Multiple Environments

```bash
# Development
dock2k8s -c config-dev.yml -o k8s-dev

# Staging
dock2k8s -c config-staging.yml -o k8s-staging

# Production
dock2k8s -c config-prod.yml -o k8s-prod
```

## Error Handling

### Common Errors

**"docker-compose.yml not found"**
```bash
# Solution: Use correct project directory
dock2k8s -p /path/to/project
```

**"config.yml not found"**
```bash
# Normal behavior - uses defaults
# No error, continues with default settings
dock2k8s
```

**Invalid replicas value**
```bash
# Error: --replicas must be >= 1
# Solution:
dock2k8s --replicas 1  # Valid
```

**Invalid format**
```bash
# Error: format must be 'yaml' or 'json'
# Solution:
dock2k8s --format yaml    # Valid
dock2k8s --format json    # Valid
```

## Tips & Tricks

### Dry Run with Verbose

See what would be converted without worrying:
```bash
dock2k8s -v
```

### Output to Different Locations

```bash
# Multiple environments
dock2k8s -o k8s-prod -f docker-compose.prod.yml
dock2k8s -o k8s-dev -f docker-compose.dev.yml
```

### JSON for Scripting

```bash
# Parse output programmatically
dock2k8s --format json | jq '.spec.replicas'
```

### Quick Help

```bash
dock2k8s --help
```
