def service(name, svc, config=None):
    """
    Generate a Kubernetes Service manifest
    
    Args:
        name: Service name
        svc: Docker Compose service definition
        config: Global config from config.py
    """
    if config is None:
        config = {}
    
    # Get service config for this workload
    svc_cfg = config.get("services", {}).get(name, {})
    
    # Check if service should be created
    if not svc_cfg.get("enabled", True):
        return None

    ports = []
    for p in svc.get("ports", []):
        try:
            _, c = p.split(":")
            ports.append({
                "port": int(c),
                "targetPort": int(c)
            })
        except (ValueError, IndexError):
            # Handle malformed port
            if ":" in str(p):
                port_num = int(str(p).split(":")[-1])
                ports.append({
                    "port": port_num,
                    "targetPort": port_num
                })

    if not ports:
        return None

    # Get service type from config or default
    service_type = svc_cfg.get("type", "ClusterIP")
    
    return {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name},
        "spec": {
            "selector": {"app": name},
            "ports": ports,
            "type": service_type
        }
    }
