import yaml
from pathlib import Path

# Default configuration
DEFAULT_CONFIG = {
    "output_dir": "k8s",
    "docker_compose_file": "docker-compose.yml",
    "verbose": False,
    "format": "yaml",
    "default_replicas": 1,
    "default_controller": "Deployment",
    "convert_volumes": True,
    "pvc_storage_class": None,
    "pvc_size": "10Gi",
    "handle_depends_on": True,
    "init_container_image": "busybox:1.35",
    "warn_on_build": True,
    "workloads": {},
    "services": {}
}

def load_config(config_path):
    """Load config.yml file. Returns dict or empty dict if not found."""
    path = Path(config_path)
    if not path.exists():
        return {}
    
    try:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Failed to load {config_path}: {e}")
        return {}

def merge_configs(cli_args, config_file=None):
    """
    Merge configs with precedence: CLI args > config file > defaults
    
    Args:
        cli_args: dict of CLI arguments (None values are ignored)
        config_file: path to config.yml
    
    Returns:
        Merged config dict
    """
    # Start with defaults
    config = DEFAULT_CONFIG.copy()
    
    # Merge config file if provided
    if config_file:
        file_config = load_config(config_file)
        
        # Extract defaults section if present
        defaults_section = file_config.pop("defaults", {})
        if defaults_section:
            # Map defaults section to config keys
            if "replicas" in defaults_section:
                config["default_replicas"] = defaults_section["replicas"]
            if "controller" in defaults_section:
                config["default_controller"] = defaults_section["controller"]
        
        # Extract workloads and services sections
        workloads = file_config.pop("workloads", {})
        services = file_config.pop("services", {})
        
        # Merge rest of config file
        config.update({k: v for k, v in file_config.items() if v is not None})
        
        # Add workloads and services
        if workloads:
            config["workloads"] = workloads
        if services:
            config["services"] = services
    
    # Merge CLI args (only non-None values override)
    if cli_args:
        cli_config = {k: v for k, v in cli_args.items() if v is not None}
        config.update(cli_config)
    
    return config

def get_workload_config(name, config, key, default=None):
    """
    Get workload configuration from config.
    Precedence: workload-specific > defaults > function default
    """
    return (
        config.get("workloads", {})
           .get(name, {})
           .get(key,
                config.get("defaults", {}).get(key, default))
    )

def get_service_config(name, config, key, default=None):
    """
    Get service configuration from config.
    Precedence: service-specific > function default
    """
    return (
        config.get("services", {})
           .get(name, {})
           .get(key, default)
    )

# Kept for backward compatibility
def resolve(service, cfg, key, default=None):
    """Legacy function - use get_workload_config instead"""
    return (
        cfg.get("workloads", {})
           .get(service, {})
           .get(key,
                cfg.get("defaults", {}).get(key, default))
    )
