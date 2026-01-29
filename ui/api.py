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
        PreviewResult, ProjectFile, ServiceConfig, KubernetesServiceConfig, 
        K8sResource, BrowseEntry, WorkspaceInfo
    )
except ImportError:
    from .models import (
        ProjectIR, ServiceIR, ConfigUpdate, ConversionResult,
        PreviewResult, ProjectFile, ServiceConfig, KubernetesServiceConfig,
        K8sResource, BrowseEntry, WorkspaceInfo
    )

router = APIRouter(prefix="/api", tags=["api"])

# Global workspace state (can be changed via API)
_current_workspace: Optional[Path] = None


def get_project_root() -> Path:
    """Get current project root (uses global workspace if set)"""
    global _current_workspace
    if _current_workspace and _current_workspace.exists():
        return _current_workspace
    try:
        return find_project_root(".")
    except FileNotFoundError:
        # If not in a project, use current directory
        return Path(".").resolve()


def set_workspace(path: Path) -> None:
    """Set the current workspace"""
    global _current_workspace
    _current_workspace = path.resolve()


def get_home_dir() -> Path:
    """Get user's home directory"""
    return Path.home()


# ============================================================================
# File Browser & Workspace Endpoints
# ============================================================================

@router.get("/browse", response_model=List[BrowseEntry])
async def browse_directory(path: Optional[str] = None):
    """Browse a directory, Jupyter-style. Returns files and folders."""
    try:
        if path:
            target = Path(path).resolve()
        else:
            # Default to home directory
            target = get_home_dir()
        
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        if not target.is_dir():
            raise HTTPException(status_code=400, detail=f"Not a directory: {path}")
        
        entries: List[BrowseEntry] = []
        
        try:
            items = sorted(target.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
        
        for item in items:
            # Skip hidden files/folders
            if item.name.startswith('.'):
                continue
            
            try:
                is_dir = item.is_dir()
                size = None if is_dir else item.stat().st_size
                
                # Check if this folder is a Dock2K8s project
                is_project = False
                if is_dir:
                    compose_file = item / "docker-compose.yml"
                    is_project = compose_file.exists()
                
                # Get modification time
                try:
                    mtime = item.stat().st_mtime
                    from datetime import datetime
                    modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                except Exception:
                    modified = None
                
                entries.append(BrowseEntry(
                    name=item.name,
                    path=str(item),
                    is_dir=is_dir,
                    size=size,
                    is_project=is_project,
                    modified=modified
                ))
            except (PermissionError, OSError):
                # Skip inaccessible items
                continue
        
        return entries
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browse/parent")
async def get_parent_path(path: str):
    """Get parent directory path"""
    try:
        target = Path(path).resolve()
        parent = target.parent
        return {"path": str(parent), "name": parent.name or str(parent)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/browse/home")
async def get_home_path():
    """Get home directory path"""
    home = get_home_dir()
    return {"path": str(home), "name": home.name}


@router.get("/workspace", response_model=WorkspaceInfo)
async def get_workspace():
    """Get current workspace information"""
    try:
        root = get_project_root()
        config_path = root / "config.yml"
        config = merge_configs({}, config_path) if config_path.exists() else {}
        output_dir = config.get("output_dir", "k8s")
        
        return WorkspaceInfo(
            path=str(root),
            name=root.name,
            has_compose=(root / "docker-compose.yml").exists(),
            has_config=config_path.exists(),
            has_output=(root / output_dir).exists()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/workspace")
async def set_workspace_path(path: str):
    """Set the current workspace/project root"""
    try:
        target = Path(path).resolve()
        
        if not target.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        if not target.is_dir():
            raise HTTPException(status_code=400, detail=f"Not a directory: {path}")
        
        # Check if it's a valid project (has docker-compose.yml)
        compose_file = target / "docker-compose.yml"
        if not compose_file.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Not a valid Dock2K8s project: docker-compose.yml not found in {path}"
            )
        
        set_workspace(target)
        
        return {
            "success": True,
            "message": f"Workspace set to: {target}",
            "path": str(target),
            "name": target.name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/folder/create")
async def create_folder(path: str, name: str):
    """Create a new folder"""
    try:
        # Validate inputs
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Folder name cannot be empty")
        
        # Clean the folder name (remove invalid characters)
        clean_name = "".join(c for c in name if c.isalnum() or c in ('-', '_', ' '))
        if not clean_name:
            raise HTTPException(status_code=400, detail="Invalid folder name")
        
        # Create the full path
        parent_path = Path(path).resolve()
        if not parent_path.exists():
            raise HTTPException(status_code=404, detail=f"Parent directory not found: {path}")
        
        new_folder = parent_path / clean_name
        
        # Check if folder already exists
        if new_folder.exists():
            raise HTTPException(status_code=409, detail=f"Folder '{clean_name}' already exists")
        
        # Create the folder
        new_folder.mkdir(parents=True, exist_ok=False)
        
        return {
            "success": True,
            "message": f"Folder '{clean_name}' created successfully",
            "path": str(new_folder),
            "name": clean_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create folder: {str(e)}")


@router.post("/project/create")
async def create_project(path: str, name: str):
    """Create a new Dock2K8s project with sample docker-compose.yml"""
    try:
        # Validate inputs
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="Project name cannot be empty")
        
        # Clean the project name
        clean_name = "".join(c for c in name if c.isalnum() or c in ('-', '_'))
        if not clean_name:
            raise HTTPException(status_code=400, detail="Invalid project name")
        
        # Create the full path
        parent_path = Path(path).resolve()
        if not parent_path.exists():
            raise HTTPException(status_code=404, detail=f"Parent directory not found: {path}")
        
        project_path = parent_path / clean_name
        
        # Check if project already exists
        if project_path.exists():
            raise HTTPException(status_code=409, detail=f"Project '{clean_name}' already exists")
        
        # Create project directory
        project_path.mkdir(parents=True, exist_ok=False)
        
        # Create sample docker-compose.yml
        sample_compose = {
            "version": "3.8",
            "services": {
                "web": {
                    "image": "nginx:latest",
                    "ports": ["80:80"],
                    "environment": {
                        "ENV": "production"
                    }
                },
                "api": {
                    "image": "node:18-alpine",
                    "ports": ["3000:3000"],
                    "depends_on": ["db"],
                    "environment": {
                        "DATABASE_URL": "postgres://db:5432/myapp"
                    }
                },
                "db": {
                    "image": "postgres:15-alpine",
                    "ports": ["5432:5432"],
                    "environment": {
                        "POSTGRES_DB": "myapp",
                        "POSTGRES_USER": "user",
                        "POSTGRES_PASSWORD": "password"
                    },
                    "volumes": ["db-data:/var/lib/postgresql/data"]
                }
            },
            "volumes": {
                "db-data": None
            }
        }
        
        compose_file = project_path / "docker-compose.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(sample_compose, f, sort_keys=False, default_flow_style=False)
        
        # Create basic config.yml
        sample_config = {
            "defaults": {
                "replicas": 1,
                "controller": "Deployment"
            },
            "output_dir": "k8s",
            "namespace": "default"
        }
        
        config_file = project_path / "config.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f, sort_keys=False, default_flow_style=False)
        
        # Create README.md
        readme_content = f"""# {clean_name}

This is a Dock2K8s project that converts Docker Compose to Kubernetes manifests.

## Getting Started

1. Edit `docker-compose.yml` to define your services
2. Customize `config.yml` to configure Kubernetes settings
3. Run conversion to generate Kubernetes manifests in the `k8s/` directory

## Project Structure

- `docker-compose.yml` - Your Docker Compose configuration
- `config.yml` - Dock2K8s configuration
- `k8s/` - Generated Kubernetes manifests (created after conversion)

## Sample Services

This project includes three sample services:
- **web**: Nginx web server
- **api**: Node.js API server
- **db**: PostgreSQL database

Feel free to modify or replace these with your own services!
"""
        
        readme_file = project_path / "README.md"
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        return {
            "success": True,
            "message": f"Project '{clean_name}' created successfully",
            "path": str(project_path),
            "name": clean_name,
            "files_created": [
                "docker-compose.yml",
                "config.yml",
                "README.md"
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.post("/file/create")
async def create_file(path: str, name: str, content: str = ""):
    """Create a new file with optional content"""
    try:
        # Validate inputs
        if not name or not name.strip():
            raise HTTPException(status_code=400, detail="File name cannot be empty")
        
        # Create the full path
        parent_path = Path(path).resolve()
        if not parent_path.exists():
            raise HTTPException(status_code=404, detail=f"Parent directory not found: {path}")
        
        if not parent_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")
        
        new_file = parent_path / name
        
        # Check if file already exists
        if new_file.exists():
            raise HTTPException(status_code=409, detail=f"File '{name}' already exists")
        
        # Create the file
        with open(new_file, 'w') as f:
            f.write(content)
        
        return {
            "success": True,
            "message": f"File '{name}' created successfully",
            "path": str(new_file),
            "name": name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create file: {str(e)}")


@router.get("/file/read")
async def read_file(path: str):
    """Read file contents"""
    try:
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
        
        # Check file size (limit to 10MB)
        file_size = file_path.stat().st_size
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="File too large (max 10MB)")
        
        # Try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "path": str(file_path),
                "name": file_path.name,
                "content": content,
                "size": file_size,
                "is_text": True
            }
        except UnicodeDecodeError:
            # Binary file
            return {
                "success": True,
                "path": str(file_path),
                "name": file_path.name,
                "content": None,
                "size": file_size,
                "is_text": False,
                "message": "Binary file cannot be displayed as text"
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


@router.put("/file/update")
async def update_file(path: str, content: str):
    """Update file contents"""
    try:
        file_path = Path(path).resolve()
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
        
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + '.bak')
        import shutil
        shutil.copy2(file_path, backup_path)
        
        try:
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "success": True,
                "message": f"File '{file_path.name}' updated successfully",
                "path": str(file_path),
                "backup_path": str(backup_path)
            }
        except Exception as e:
            # Restore from backup on error
            shutil.copy2(backup_path, file_path)
            raise e
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update file: {str(e)}")


@router.delete("/file/delete")
async def delete_file(path: str):
    """Delete a file or empty directory"""
    try:
        target_path = Path(path).resolve()
        
        if not target_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        if target_path.is_file():
            target_path.unlink()
            return {
                "success": True,
                "message": f"File '{target_path.name}' deleted successfully",
                "path": str(target_path)
            }
        elif target_path.is_dir():
            # Only delete empty directories
            if any(target_path.iterdir()):
                raise HTTPException(status_code=400, detail="Directory is not empty. Please delete contents first.")
            
            target_path.rmdir()
            return {
                "success": True,
                "message": f"Directory '{target_path.name}' deleted successfully",
                "path": str(target_path)
            }
        else:
            raise HTTPException(status_code=400, detail="Path is neither a file nor a directory")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {str(e)}")


@router.post("/file/rename")
async def rename_file(path: str, new_name: str):
    """Rename a file or directory"""
    try:
        old_path = Path(path).resolve()
        
        if not old_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {path}")
        
        # Validate new name
        if not new_name or not new_name.strip():
            raise HTTPException(status_code=400, detail="New name cannot be empty")
        
        # Clean the new name
        clean_name = "".join(c for c in new_name if c.isalnum() or c in ('-', '_', '.', ' '))
        if not clean_name:
            raise HTTPException(status_code=400, detail="Invalid name")
        
        new_path = old_path.parent / clean_name
        
        # Check if target already exists
        if new_path.exists():
            raise HTTPException(status_code=409, detail=f"'{clean_name}' already exists")
        
        # Rename
        old_path.rename(new_path)
        
        return {
            "success": True,
            "message": f"Renamed '{old_path.name}' to '{clean_name}'",
            "old_path": str(old_path),
            "new_path": str(new_path),
            "new_name": clean_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename: {str(e)}")






