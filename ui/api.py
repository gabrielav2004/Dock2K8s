"""REST API endpoints for Dock2K8s UI"""
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from project import find_project_root
from convert import convert, load, write
from config import load_config, merge_configs, DEFAULT_CONFIG

# Import models - try absolute first, fallback to relative
try:
    from ui.models import (
        ProjectIR, ServiceIR, ConfigUpdate, ConversionResult,
        PreviewResult, ProjectFile, ServiceConfig, KubernetesServiceConfig, K8sResource
    )
except ImportError:
    from .models import (
        ProjectIR, ServiceIR, ConfigUpdate, ConversionResult,
        PreviewResult, ProjectFile, ServiceConfig, KubernetesServiceConfig, K8sResource
    )

router = APIRouter(prefix="/api", tags=["api"])


def get_project_root() -> Path:
    """Get current project root"""
    try:
        return find_project_root(".")
    except FileNotFoundError:
        # If not in a project, use current directory
        return Path(".").resolve()


def build_service_ir(name: str, svc: Dict[str, Any], config: Dict[str, Any]) -> ServiceIR:
    """Build ServiceIR from docker-compose service and config"""
    # Get workload config
    workload_cfg = config.get("workloads", {}).get(name, {})
    workload_config = ServiceConfig(
        replicas=workload_cfg.get("replicas"),
        controller=workload_cfg.get("controller")
    )
    
    # Get Kubernetes service config
    svc_cfg = config.get("services", {}).get(name, {})
    service_config = KubernetesServiceConfig(
        enabled=svc_cfg.get("enabled"),
        type=svc_cfg.get("type")
    )
    
    # Parse ports
    ports = []
    for p in svc.get("ports", []):
        if isinstance(p, str):
            try:
                parts = p.split(":")
                if len(parts) >= 2:
                    ports.append({
                        "host": parts[0] if parts[0] else None,
                        "container": int(parts[-1])
                    })
                else:
                    ports.append({"container": int(p)})
            except ValueError:
                pass
        elif isinstance(p, dict):
            ports.append(p)
    
    # Parse environment variables
    env = []
    env_raw = svc.get("environment", {})
    if isinstance(env_raw, dict):
        env = [{"name": k, "value": str(v)} for k, v in env_raw.items()]
    elif isinstance(env_raw, list):
        for item in env_raw:
            if isinstance(item, str) and "=" in item:
                key, value = item.split("=", 1)
                env.append({"name": key.strip(), "value": value.strip()})
            elif isinstance(item, dict):
                env.append(item)
    
    # Parse depends_on
    depends_on = []
    if "depends_on" in svc:
        if isinstance(svc["depends_on"], list):
            depends_on = [str(d) for d in svc["depends_on"]]
        elif isinstance(svc["depends_on"], dict):
            depends_on = list(svc["depends_on"].keys())
    
    # Parse volumes
    volumes = []
    for vol in svc.get("volumes", []):
        if isinstance(vol, str):
            volumes.append({"source": vol.split(":")[0] if ":" in vol else vol})
        elif isinstance(vol, dict):
            volumes.append(vol)
    
    return ServiceIR(
        name=name,
        image=svc.get("image", ""),
        ports=ports,
        environment=env,
        depends_on=depends_on,
        volumes=volumes,
        workload_config=workload_config,
        service_config=service_config
    )


@router.get("/ir", response_model=ProjectIR)
async def get_ir():
    """Get intermediate representation of current project"""
    try:
        root = get_project_root()
        config_path = root / "config.yml"
        
        # Load config
        config = merge_configs({}, config_path)
        
        # Load docker-compose.yml
        compose_file = config.get("docker_compose_file", "docker-compose.yml")
        compose_path = root / compose_file
        if not compose_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Docker Compose file '{compose_file}' not found"
            )
        
        compose = load(compose_path)
        
        # Build IR
        services = []
        for name, svc in compose.get("services", {}).items():
            services.append(build_service_ir(name, svc, config))
        
        # Extract defaults
        defaults = {}
        if "defaults" in config:
            defaults = config["defaults"]
        else:
            defaults = {
                "replicas": config.get("default_replicas", 1),
                "controller": config.get("default_controller", "Deployment")
            }
        
        # Global config (non-defaults)
        global_config = {k: v for k, v in config.items() 
                        if k not in ["workloads", "services", "defaults"]}
        
        return ProjectIR(
            project_root=str(root),
            docker_compose_file=compose_file,
            services=services,
            defaults=defaults,
            global_config=global_config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project", response_model=List[ProjectFile])
async def get_project_files():
    """Get list of relevant project files"""
    try:
        root = get_project_root()
        config_path = root / "config.yml"
        config = merge_configs({}, config_path)
        output_dir_name = config.get("output_dir", "k8s")
        files = []
        
        # Add docker-compose.yml
        compose_file = root / "docker-compose.yml"
        if compose_file.exists():
            files.append(ProjectFile(
                name="docker-compose.yml",
                path=str(compose_file.relative_to(root)),
                type="file",
                size=compose_file.stat().st_size
            ))
        
        # Add config.yml
        config_file = root / "config.yml"
        if config_file.exists():
            files.append(ProjectFile(
                name="config.yml",
                path=str(config_file.relative_to(root)),
                type="file",
                size=config_file.stat().st_size
            ))
        
        # Add output directory (defaults to k8s/)
        k8s_dir = root / output_dir_name
        if k8s_dir.exists() and k8s_dir.is_dir():
            files.append(ProjectFile(
                name=output_dir_name,
                path=str(k8s_dir.relative_to(root)),
                type="directory"
            ))
            # List generated files
            for f in k8s_dir.glob("*.yaml"):
                files.append(ProjectFile(
                    name=f.name,
                    path=str(f.relative_to(root)),
                    type="file",
                    size=f.stat().st_size
                ))
        
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/k8s/resources", response_model=List[K8sResource])
async def get_k8s_resources():
    """Parse generated Kubernetes manifests from output_dir and return high-level resources."""
    try:
        root = get_project_root()
        config_path = root / "config.yml"
        config = merge_configs({}, config_path)
        output_dir = root / config.get("output_dir", "k8s")

        if not output_dir.exists() or not output_dir.is_dir():
            return []

        resources: List[K8sResource] = []
        for manifest_path in sorted(output_dir.glob("*.yml")) + sorted(output_dir.glob("*.yaml")):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    docs = list(yaml.safe_load_all(f))
                for doc in docs:
                    if not isinstance(doc, dict):
                        continue
                    kind = str(doc.get("kind") or "").strip()
                    meta = doc.get("metadata") or {}
                    name = str(meta.get("name") or "").strip()
                    namespace = meta.get("namespace")

                    if not kind or not name:
                        continue

                    selector_app: Optional[str] = None
                    if kind.lower() == "service":
                        spec = doc.get("spec") or {}
                        selector = spec.get("selector") or {}
                        if isinstance(selector, dict):
                            selector_app = selector.get("app")

                    resources.append(K8sResource(
                        kind=kind,
                        name=name,
                        namespace=namespace,
                        file=manifest_path.name,
                        selector_app=selector_app,
                    ))
            except Exception:
                # Skip unreadable manifests; the UI will still work
                continue

        return resources
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_config(update: ConfigUpdate):
    """Update config.yml file"""
    try:
        root = get_project_root()
        config_path = root / "config.yml"
        
        # Load existing config or start with defaults
        if config_path.exists():
            current_config = load_config(config_path)
        else:
            current_config = {}
        
        # Apply updates
        if update.defaults:
            current_config["defaults"] = update.defaults
        
        if update.workloads:
            if "workloads" not in current_config:
                current_config["workloads"] = {}
            current_config["workloads"].update(update.workloads)
        
        if update.services:
            if "services" not in current_config:
                current_config["services"] = {}
            current_config["services"].update(update.services)
        
        if update.global_settings:
            # Merge global settings (avoid overwriting workloads/services)
            for k, v in update.global_settings.items():
                if k not in ["workloads", "services", "defaults"]:
                    current_config[k] = v
        
        # Write back
        with open(config_path, "w") as f:
            yaml.dump(current_config, f, sort_keys=False, default_flow_style=False)
        
        return {"success": True, "message": "Config updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/convert", response_model=ConversionResult)
async def trigger_conversion():
    """Trigger conversion and return results"""
    try:
        root = get_project_root()
        config_path = root / "config.yml"
        
        # Load config
        config = merge_configs({}, config_path)
        
        # Run conversion
        convert(root, config)
        
        # List generated files
        output_dir = root / config.get("output_dir", "k8s")
        generated_files = []
        if output_dir.exists():
            generated_files = [f.name for f in output_dir.glob("*.yaml")]
        
        return ConversionResult(
            success=True,
            message="Conversion completed successfully",
            output_dir=str(output_dir.relative_to(root)),
            generated_files=generated_files
        )
    except Exception as e:
        return ConversionResult(
            success=False,
            message="Conversion failed",
            errors=[str(e)]
        )


@router.get("/preview/{service_name}", response_model=PreviewResult)
async def preview_service(service_name: str):
    """Preview generated YAML for a specific service"""
    try:
        root = get_project_root()
        config_path = root / "config.yml"
        
        # Load config
        config = merge_configs({}, config_path)
        
        # Load docker-compose.yml
        compose_file = config.get("docker_compose_file", "docker-compose.yml")
        compose_path = root / compose_file
        if not compose_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Docker Compose file '{compose_file}' not found"
            )
        
        compose = load(compose_path)
        
        # Find service
        if service_name not in compose.get("services", {}):
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service_name}' not found"
            )
        
        svc = compose["services"][service_name]
        
        # Generate manifests
        from generators.controller import controller
        from generators.service import service
        
        kind = config.get("workloads", {}).get(service_name, {}).get(
            "controller",
            config.get("default_controller", "Deployment")
        )
        
        ctrl = controller(kind, service_name, svc, config)
        svc_obj = service(service_name, svc, config)
        
        deployment_yaml = yaml.dump(ctrl, sort_keys=False, default_flow_style=False)
        service_yaml = yaml.dump(svc_obj, sort_keys=False, default_flow_style=False) if svc_obj else None
        
        return PreviewResult(
            service_name=service_name,
            deployment_yaml=deployment_yaml,
            service_yaml=service_yaml
        )
    except HTTPException:
        raise
    except Exception as e:
        return PreviewResult(
            service_name=service_name,
            errors=[str(e)]
        )
