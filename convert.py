import yaml
import json
from pathlib import Path
from generators.controller import controller
from generators.service import service
from generators.secret import secret
from config import get_workload_config, get_service_config, get_secrets_config
from env_loader import load_env_file

def load(path):
    with open(path) as f:
        return yaml.safe_load(f)

def write(obj, path, format="yaml"):
    """Write object as YAML or JSON"""
    with open(path, "w") as f:
        if format == "json":
            json.dump(obj, f, indent=2)
        else:
            yaml.dump(obj, f, sort_keys=False)

def convert(project_root, config=None):
    """
    Convert docker-compose.yml to Kubernetes manifests
    
    Args:
        project_root: Path to project directory
        config: Configuration dict from config.py
    """
    if config is None:
        config = {}
    
    # Get config values
    compose_file = config.get("docker_compose_file", "docker-compose.yml")
    output_dir = config.get("output_dir", "k8s")
    verbose = config.get("verbose", False)
    output_format = config.get("format", "yaml")
    warn_on_build = config.get("warn_on_build", True)
    
    project_root = Path(project_root)
    
    # Load docker-compose.yml
    compose_path = project_root / compose_file
    if not compose_path.exists():
        raise FileNotFoundError(f"'{compose_file}' not found")
    
    compose = load(compose_path)
    
    # Create output directory
    out = project_root / output_dir
    out.mkdir(exist_ok=True)
    
    if verbose:
        print(f"📁 Project root: {project_root}")
        print(f"📄 Loading: {compose_file}")
        print(f"⚙️  Config: config.yml")
        print(f"📦 Output: {out}")
        print()
    
    # Load environment variables for secrets
    env_vars = {}
    env_file = project_root / ".env"
    if env_file.exists():
        env_vars = load_env_file(env_file)
        if verbose and env_vars:
            print(f"📋 Loaded {len(env_vars)} env vars from .env")
    
    # Generate secrets if configured
    secrets_config = get_secrets_config(config)
    if secrets_config:
        for secret_name, secret_cfg in secrets_config.items():
            secret_obj = secret(secret_name, secret_cfg, env_vars)
            if secret_obj:
                secret_path = out / f"{secret_name}-secret.yaml"
                write(secret_obj, secret_path, output_format)
                print(f"✔ {secret_name} → Secret")
    
    # Convert each service
    for name, svc in compose.get("services", {}).items():
        # Check for unsupported build field
        if "build" in svc and warn_on_build:
            if verbose:
                print(f"⚠️  {name}: 'build' field ignored (using 'image' only)")
        
        # Determine controller kind
        kind = get_workload_config(name, config, "controller", config.get("default_controller", "Deployment"))
        
        # Generate controller manifest
        ctrl = controller(kind, name, svc, config)
        ctrl_path = out / f"{name}-{kind.lower()}.yaml"
        write(ctrl, ctrl_path, output_format)
        
        # Generate service manifest
        svc_obj = service(name, svc, config)
        if svc_obj:
            svc_path = out / f"{name}-service.yaml"
            write(svc_obj, svc_path, output_format)
            print(f"✔ {name} → {kind} + Service")
        else:
            print(f"✔ {name} → {kind}")
    
    if verbose:
        print()
        print(f"✅ Conversion complete!")

