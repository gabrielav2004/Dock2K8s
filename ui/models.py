"""Data models for API requests and responses"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ServiceConfig(BaseModel):
    """Service workload configuration"""
    replicas: Optional[int] = None
    controller: Optional[str] = None  # Deployment or StatefulSet


class KubernetesServiceConfig(BaseModel):
    """Kubernetes Service configuration"""
    enabled: Optional[bool] = None
    type: Optional[str] = None  # ClusterIP, NodePort, LoadBalancer, etc.


class ServiceIR(BaseModel):
    """Intermediate representation of a service"""
    name: str
    image: str
    ports: List[Dict[str, Any]] = []
    environment: List[Dict[str, str]] = []
    depends_on: List[str] = []
    volumes: List[Dict[str, Any]] = []
    workload_config: Optional[ServiceConfig] = None
    service_config: Optional[KubernetesServiceConfig] = None


class ProjectIR(BaseModel):
    """Complete project intermediate representation"""
    project_root: str
    docker_compose_file: str
    services: List[ServiceIR]
    defaults: Dict[str, Any]
    global_config: Dict[str, Any]


class ConfigUpdate(BaseModel):
    """Update to config.yml"""
    defaults: Optional[Dict[str, Any]] = None
    workloads: Optional[Dict[str, Dict[str, Any]]] = None
    services: Optional[Dict[str, Dict[str, Any]]] = None
    global_settings: Optional[Dict[str, Any]] = None


class ConversionResult(BaseModel):
    """Result of conversion operation"""
    success: bool
    message: str
    output_dir: Optional[str] = None
    generated_files: List[str] = []
    errors: List[str] = []


class PreviewResult(BaseModel):
    """Preview of generated YAML"""
    service_name: str
    deployment_yaml: Optional[str] = None
    service_yaml: Optional[str] = None
    errors: List[str] = []


class ProjectFile(BaseModel):
    """Project file information"""
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None


class K8sResource(BaseModel):
    """A Kubernetes resource parsed from generated manifests"""
    kind: str
    name: str
    namespace: Optional[str] = None
    file: Optional[str] = None
    selector_app: Optional[str] = None


class BrowseEntry(BaseModel):
    """File/folder entry for the file browser"""
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    is_project: bool = False  # True if folder contains docker-compose.yml
    modified: Optional[str] = None


class WorkspaceInfo(BaseModel):
    """Current workspace information"""
    path: str
    name: str
    has_compose: bool
    has_config: bool
    has_output: bool
