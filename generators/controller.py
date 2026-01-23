def controller(kind, name, svc, config=None):
    """
    Generate a Kubernetes controller (Deployment/StatefulSet) manifest
    
    Args:
        kind: Controller kind (Deployment or StatefulSet)
        name: Service name
        svc: Docker Compose service definition
        config: Global config from config.py
    """
    if config is None:
        config = {}
    
    ports = []
    for p in svc.get("ports", []):
        try:
            _, c = p.split(":")
            ports.append({"containerPort": int(c)})
        except (ValueError, IndexError):
            # Handle malformed port
            if ":" in str(p):
                ports.append({"containerPort": int(str(p).split(":")[-1])})

    # Handle environment in both dict and list formats
    env_raw = svc.get("environment", {})
    env = []
    
    if isinstance(env_raw, dict):
        # Dict format: {KEY: VALUE}
        env = [{"name": k, "value": str(v)} for k, v in env_raw.items()]
    elif isinstance(env_raw, list):
        # List format: [KEY=VALUE, KEY2=VALUE2]
        for item in env_raw:
            if "=" in str(item):
                key, value = str(item).split("=", 1)
                env.append({"name": key.strip(), "value": value.strip()})
            else:
                # Handle edge case of key without value
                env.append({"name": str(item).strip(), "value": ""})

    spec = {
        "containers": [{
            "name": name,
            "image": svc["image"],
            "ports": ports,
            "env": env,
        }]
    }

    obj = {
        "apiVersion": "apps/v1",
        "kind": kind,
        "metadata": {"name": name},
        "spec": {
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": spec,
            }
        }
    }

    # Set replicas for Deployments
    if kind == "Deployment":
        default_replicas = config.get("default_replicas", 1)
        workload_replicas = config.get("workloads", {}).get(name, {}).get("replicas", default_replicas)
        obj["spec"]["replicas"] = workload_replicas

    return obj
