"""
Parse .env files and return key-value pairs.
Handles standard .env format: KEY=VALUE
"""

from pathlib import Path


def load_env_file(env_path):
    """
    Load environment variables from .env file.
    
    Args:
        env_path: Path to .env file
    
    Returns:
        dict: Key-value pairs from .env file
        Empty dict if file not found
    """
    path = Path(env_path)
    
    if not path.exists():
        return {}
    
    env_vars = {}
    
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
    
    except Exception as e:
        print(f"Warning: Failed to parse {env_path}: {e}")
        return {}
    
    return env_vars
