# Testing Guide for Dock2K8s

This document provides comprehensive testing procedures and test cases for the Dock2K8s Docker Compose to Kubernetes converter.

## Table of Contents

1. [Test Environment Setup](#test-environment-setup)
2. [Manual Testing](#manual-testing)
3. [Test Cases](#test-cases)
4. [Verification Checklist](#verification-checklist)
5. [Edge Cases & Error Handling](#edge-cases--error-handling)
6. [Debugging Tips](#debugging-tips)
7. [CI/CD Integration](#cicd-integration)

## Test Environment Setup

### Prerequisites

```bash
# Install dependencies
pip install pyyaml

# Verify Python version
python --version  # Should be 3.7+
```

### Test Directory Structure

```
test-project/
├── docker-compose.yml
├── config.yml
├── dock2k8s.yaml
└── expected_output/
    ├── service1-deployment.yaml
    ├── service1-service.yaml
    └── ...
```

### Quick Test Setup

```bash
# Create test directory
mkdir test-project
cd test-project

# Create sample docker-compose.yml
cat > docker-compose.yml << 'EOF'
services:
  web:
    image: nginx:latest
    ports:
      - "80:80"
    environment:
      - NGINX_HOST=example.com
  database:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_DB=mydb
EOF

# Run conversion
cd ..
python cli.py -p test-project -v
```

## Manual Testing

### Test 1: Basic Conversion

**Purpose:** Verify basic Docker Compose to Kubernetes conversion works

**Setup:**
```bash
mkdir tests/basic
cd tests/basic

cat > docker-compose.yml << 'EOF'
services:
  app:
    image: myapp:1.0
    ports:
      - "8080:8080"
EOF
```

**Command:**
```bash
python ../../cli.py
```

**Expected Output:**
```
✔ app → Deployment
```

**Verification:**
```bash
# Check generated files
ls -la k8s/
# Should contain: app-deployment.yaml, app-service.yaml

# Check deployment
cat k8s/app-deployment.yaml
# Should have:
# - kind: Deployment
# - name: app
# - image: myapp:1.0
# - containerPort: 8080
# - replicas: 1

# Check service
cat k8s/app-service.yaml
# Should have:
# - kind: Service
# - name: app
# - port: 8080
# - type: ClusterIP
```

### Test 2: Configuration File Loading

**Purpose:** Verify config.yml is loaded and applied correctly

**Setup:**
```bash
mkdir tests/config
cd tests/config

cat > docker-compose.yml << 'EOF'
services:
  api:
    image: api:1.0
    ports:
      - "3000:3000"
EOF

cat > config.yml << 'EOF'
output_dir: kubernetes
default_replicas: 3
default_service_type: LoadBalancer
verbose: true
EOF
```

**Command:**
```bash
python ../../cli.py
```

**Expected Output:**
```
📁 Project root: ...
📄 Loading: docker-compose.yml
⚙️  Config: config.yml
📦 Output: kubernetes
✔ api → Deployment
✅ Conversion complete!
```

**Verification:**
```bash
# Check output directory
ls -la kubernetes/

# Check replicas and service type
cat kubernetes/api-deployment.yaml | grep replicas  # Should be 3
cat kubernetes/api-service.yaml | grep type         # Should be LoadBalancer
```

### Test 3: CLI Parameter Override

**Purpose:** Verify CLI arguments override config.yml

**Setup:**
```bash
mkdir tests/override
cd tests/override

cat > docker-compose.yml << 'EOF'
services:
  service:
    image: svc:1.0
    ports:
      - "9000:9000"
EOF

cat > config.yml << 'EOF'
default_replicas: 1
default_service_type: ClusterIP
EOF
```

**Command:**
```bash
python ../../cli.py --replicas 5 --service-type NodePort
```

**Expected Output:**
```
✔ service → Deployment
```

**Verification:**
```bash
# Check that CLI overrides config
cat k8s/service-deployment.yaml | grep replicas   # Should be 5
cat k8s/service-service.yaml | grep type          # Should be NodePort
```

### Test 4: Multiple Services

**Purpose:** Verify handling of multiple services with different configurations

**Setup:**
```bash
mkdir tests/multiple
cd tests/multiple

cat > docker-compose.yml << 'EOF'
services:
  frontend:
    image: frontend:1.0
    ports:
      - "3000:3000"
  backend:
    image: backend:2.0
    ports:
      - "8000:8000"
  cache:
    image: redis:7
    ports:
      - "6379:6379"
EOF

cat > config.yml << 'EOF'
default_replicas: 1
services:
  frontend:
    replicas: 2
    service_type: LoadBalancer
  backend:
    replicas: 1
    service_type: ClusterIP
  cache:
    replicas: 1
    service_type: ClusterIP
EOF
```

**Command:**
```bash
python ../../cli.py
```

**Expected Output:**
```
✔ frontend → Deployment + Service
✔ backend → Deployment + Service
✔ cache → Deployment + Service
```

**Verification:**
```bash
# Verify all manifests created
ls -la k8s/
# Should have 6 files: 3 deployments + 3 services

# Verify per-service configs
cat k8s/frontend-deployment.yaml | grep replicas  # 2
cat k8s/backend-deployment.yaml | grep replicas   # 1
cat k8s/frontend-service.yaml | grep type         # LoadBalancer
cat k8s/backend-service.yaml | grep type          # ClusterIP
```

### Test 5: Environment Variables

**Purpose:** Verify environment variables are correctly converted

**Setup:**
```bash
mkdir tests/env
cd tests/env

cat > docker-compose.yml << 'EOF'
services:
  app:
    image: app:1.0
    ports:
      - "8080:8080"
    environment:
      - DEBUG=true
      - DB_HOST=postgres
      - DB_PORT=5432
      - API_KEY=secret123
EOF
```

**Command:**
```bash
python ../../cli.py
```

**Verification:**
```bash
cat k8s/app-deployment.yaml
# Should contain:
# env:
# - name: DEBUG
#   value: 'true'
# - name: DB_HOST
#   value: postgres
# - name: DB_PORT
#   value: '5432'
# - name: API_KEY
#   value: secret123
```

### Test 6: Verbose Logging

**Purpose:** Verify verbose output contains helpful debugging information

**Setup:**
```bash
mkdir tests/verbose
cd tests/verbose

cat > docker-compose.yml << 'EOF'
services:
  app:
    image: app:1.0
    ports:
      - "8080:8080"
EOF
```

**Command:**
```bash
python ../../cli.py -v
```

**Expected Output:**
```
📁 Project root: /path/to/test-project
📄 Loading: docker-compose.yml
⚙️  Config: (none)
📦 Output: k8s
✔ app → Deployment
✅ Conversion complete!
```

### Test 7: JSON Output Format

**Purpose:** Verify JSON output is valid and parseable

**Setup:**
```bash
mkdir tests/json
cd tests/json

cat > docker-compose.yml << 'EOF'
services:
  api:
    image: api:1.0
    ports:
      - "8000:8000"
EOF

cat > config.yml << 'EOF'
format: json
output_dir: manifests
EOF
```

**Command:**
```bash
python ../../cli.py
```

**Verification:**
```bash
# Verify JSON is valid
cat manifests/api-deployment.yaml | python -m json.tool

# Should output formatted JSON without errors
# Should contain same data as YAML version
```

## Test Cases

### Test Case Matrix

| Test ID | Description | Input | Config | CLI Args | Expected Result |
|---------|-------------|-------|--------|----------|-----------------|
| TC-001 | Single service, basic | 1 service, ports | None | None | 1 deployment + 1 service |
| TC-002 | Multiple services | 3 services | None | None | 3 deployments + 3 services |
| TC-003 | Config file loading | 1 service | config.yml | None | Uses config values |
| TC-004 | CLI override | 1 service | config.yml | --replicas 5 | Replicas = 5 |
| TC-005 | Env variables | 1 service, env vars | None | None | Env vars in deployment |
| TC-006 | Custom output dir | 1 service | None | -o custom | Files in custom dir |
| TC-007 | JSON format | 1 service | None | --format json | JSON manifests |
| TC-008 | Verbose logging | 1 service | None | -v | Debug output printed |
| TC-009 | No ports | 1 service, no ports | None | None | Deployment only, no service |
| TC-010 | LoadBalancer type | 1 service | None | --service-type LoadBalancer | Service type = LoadBalancer |

## Verification Checklist

### After Each Test Run

- [ ] Manifests are created in correct directory
- [ ] Generated YAML is valid Kubernetes format
- [ ] Manifest names follow pattern: `{service}-{type}.yaml`
- [ ] Deployments have correct image names
- [ ] Services have correct port mappings
- [ ] Metadata labels are consistent
- [ ] Environment variables are properly formatted
- [ ] Replicas match configuration
- [ ] Service types match configuration

### Manifest Validation

```bash
# Validate YAML syntax
for f in k8s/*.yaml; do
    echo "Validating $f..."
    python -c "import yaml; yaml.safe_load(open('$f'))" || echo "ERROR in $f"
done

# Or use kubectl (if available)
kubectl apply -f k8s/ --dry-run=client
```

## Edge Cases & Error Handling

### Test 8: Missing Docker Compose File

**Setup:**
```bash
mkdir tests/missing
cd tests/missing
# Don't create docker-compose.yml
```

**Command:**
```bash
python ../../cli.py
```

**Expected Output:**
```
FileNotFoundError: 'docker-compose.yml' not found
```

**Verification:**
✅ Error message is clear and helpful

### Test 9: Malformed Port Format

**Setup:**
```bash
mkdir tests/bad-port
cd tests/bad-port

cat > docker-compose.yml << 'EOF'
services:
  app:
    image: app:1.0
    ports:
      - "invalid"
      - "8080:8080"
EOF
```

**Command:**
```bash
python ../../cli.py
```

**Expected Behavior:**
- Should handle gracefully or skip malformed ports
- Should still generate manifests for valid ports

### Test 10: Build Field Warning

**Setup:**
```bash
mkdir tests/build-warn
cd tests/build-warn

cat > docker-compose.yml << 'EOF'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: app:1.0
    ports:
      - "8080:8080"
EOF
```

**Command:**
```bash
python ../../cli.py -v
```

**Expected Output:**
```
⚠️  app: 'build' field ignored (using 'image' only)
```

### Test 11: Service Without Ports

**Setup:**
```bash
mkdir tests/no-ports
cd tests/no-ports

cat > docker-compose.yml << 'EOF'
services:
  worker:
    image: worker:1.0
    environment:
      - QUEUE=tasks
EOF
```

**Command:**
```bash
python ../../cli.py
```

**Expected Output:**
```
✔ worker → Deployment
```

**Verification:**
```bash
# Should create deployment only
ls k8s/
# Should have worker-deployment.yaml but NOT worker-service.yaml
```

### Test 12: Custom Config Path

**Setup:**
```bash
mkdir tests/custom-config
cd tests/custom-config

cat > docker-compose.yml << 'EOF'
services:
  app:
    image: app:1.0
    ports:
      - "8080:8080"
EOF

mkdir configs
cat > configs/prod.yml << 'EOF'
default_replicas: 5
default_service_type: LoadBalancer
EOF
```

**Command:**
```bash
python ../../cli.py -c configs/prod.yml
```

**Verification:**
```bash
# Verify it used the custom config
cat k8s/app-deployment.yaml | grep replicas  # Should be 5
cat k8s/app-service.yaml | grep type         # Should be LoadBalancer
```

## Debugging Tips

### Enable Verbose Mode

Always use `-v` flag when debugging:

```bash
python cli.py -v
```

**Output includes:**
- Project root path
- Config file location
- Services being converted
- Warnings and errors

### Check Generated Manifests

```bash
# View generated deployment
cat k8s/service-deployment.yaml

# View generated service
cat k8s/service-service.yaml

# Check with kubectl (if available)
kubectl apply -f k8s/ --dry-run=client -v=2
```

### Validate Configuration

```bash
# Print config as JSON (add to cli.py for debugging)
python -c "import yaml; print(yaml.dump(yaml.safe_load(open('config.yml'))))"
```

### Test Individual Components

```bash
# Test config loading
python -c "from config import load_config; print(load_config('config.yml'))"

# Test project root finding
python -c "from project import find_project_root; print(find_project_root('.'))"

# Test manifest generation
python -c "from generators.controller import controller; print(controller('Deployment', 'test', {'image': 'test:1.0', 'ports': ['8080:8080']}, {}, lambda *a, **k: 1))"
```

### Common Issues & Solutions

**Issue:** Manifests not created
```bash
# Check if k8s directory was created
ls -la | grep k8s

# Check if docker-compose.yml exists
ls -la docker-compose.yml

# Run with verbose
python cli.py -v
```

**Issue:** Wrong replica count
```bash
# Check config precedence
cat config.yml | grep replicas
# CLI args override config.yml
python cli.py --replicas 3
```

**Issue:** Port not converted
```bash
# Check port format in docker-compose.yml
# Must be HOST:CONTAINER format
ports:
  - "8080:8080"  # ✅ Correct
  - "8080"       # ❌ Wrong
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Dock2K8s

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install pyyaml
      
      - name: Run basic conversion test
        run: |
          python cli.py -p tests/basic -v
          
      - name: Validate generated manifests
        run: |
          for f in tests/basic/k8s/*.yaml; do
            python -c "import yaml; yaml.safe_load(open('$f'))"
          done
```

### Local Test Script

```bash
#!/bin/bash
# test.sh - Run all test cases

echo "Running Dock2K8s Tests..."

test_count=0
pass_count=0

run_test() {
    local name=$1
    local cmd=$2
    
    test_count=$((test_count + 1))
    echo -n "Test $test_count: $name... "
    
    if eval "$cmd" > /dev/null 2>&1; then
        pass_count=$((pass_count + 1))
        echo "✅ PASS"
    else
        echo "❌ FAIL"
    fi
}

# Test 1: Basic conversion
run_test "Basic conversion" \
    "python cli.py -p tests/basic -v"

# Test 2: Config loading
run_test "Config loading" \
    "python cli.py -p tests/config"

# Test 3: CLI override
run_test "CLI override" \
    "python cli.py -p tests/override --replicas 5"

echo ""
echo "Results: $pass_count/$test_count tests passed"
```

### Manual Test Checklist

Before releasing, run these tests:

- [ ] TC-001: Single service basic conversion
- [ ] TC-002: Multiple services
- [ ] TC-003: Config file loading
- [ ] TC-004: CLI parameter override
- [ ] TC-005: Environment variables
- [ ] TC-007: JSON format output
- [ ] TC-008: Verbose logging
- [ ] TC-010: Service type variation
- [ ] Edge case: Missing docker-compose.yml
- [ ] Edge case: Service without ports
- [ ] Verify all generated YAML is valid

## Test Data

### Sample docker-compose.yml

```yaml
services:
  frontend:
    image: frontend:1.0
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API=http://backend:8000

  backend:
    image: backend:2.0
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://db:5432/mydb
      - LOG_LEVEL=debug

  database:
    image: postgres:14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=mydb
```

### Sample config.yml

```yaml
output_dir: k8s
verbose: false
format: yaml
default_replicas: 2
default_service_type: ClusterIP

services:
  frontend:
    replicas: 3
    service_type: LoadBalancer
  backend:
    replicas: 2
    service_type: ClusterIP
  database:
    replicas: 1
    service_type: ClusterIP
```

## Continuous Testing

### Watch Mode (for development)

```bash
# Install watchdog
pip install watchdog

# Run tests on file change
watchmedo auto-restart -d . -p '*.py' python cli.py
```

### Performance Testing

```bash
# Time the conversion
time python cli.py

# With large docker-compose.yml (10+ services)
# Should complete in < 1 second
```

## Reporting Issues

When a test fails, collect:

1. **Docker Compose file** (sanitized)
2. **Config file** (if used)
3. **CLI command** run
4. **Verbose output**: `python cli.py -v`
5. **Generated manifest** (if created)
6. **Expected behavior** description

Example bug report:

```
## Test Case: Multiple services with custom replicas

### Docker Compose:
[file contents]

### Command:
python cli.py --replicas 3 --verbose

### Expected:
All services should have 3 replicas

### Actual:
Only frontend has 3 replicas, others have 1

### Verbose Output:
[output]
```
