"""
Generate Kubernetes Secret manifests.
Creates placeholder secrets with instructions for secure creation.
"""

import base64


def secret(name, secret_config, env_vars=None):
    """
    Generate a Kubernetes Secret manifest.
    
    Args:
        name: Secret resource name
        secret_config: Secret configuration from config.yml
        env_vars: Optional dict of environment variables from .env
    
    Returns:
        dict: Kubernetes Secret manifest
        None: If secrets disabled or no data
    """
    if env_vars is None:
        env_vars = {}
    
    # Check if secrets are enabled
    if not secret_config.get("enabled", False):
        return None
    
    # Get list of keys to include in secret
    keys = secret_config.get("data", {})
    if not keys:
        return None
    
    # Build secret data
    secret_data = {}
    
    for key in keys:
        if key in env_vars:
            # Use value from .env
            value = env_vars[key]
            # Base64 encode
            secret_data[key] = base64.b64encode(value.encode()).decode()
        else:
            # Placeholder value
            secret_data[key] = base64.b64encode(b"REPLACE_ME").decode()
    
    if not secret_data:
        return None
    
    return {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": name
        },
        "type": secret_config.get("type", "Opaque"),
        "data": secret_data
    }
