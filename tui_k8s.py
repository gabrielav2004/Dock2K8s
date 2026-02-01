"""TUI visualizer for Kubernetes resources using Textual"""
from pathlib import Path
from typing import List, Dict, Any
import yaml

from textual.app import App
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Label


class ResourceCard(Static):
    """A card widget for displaying a Kubernetes resource"""
    
    def __init__(self, kind: str, resource_name: str, details: str = "", **kwargs):
        super().__init__(**kwargs)
        self.resource_kind = kind
        self.resource_name = resource_name
        self.resource_details = details
        
    def compose(self):
        """Create the card content"""
        kind_l = self.resource_kind.lower()
        if kind_l == "service":
            icon = "[S]"
            border_color = "blue"
        elif kind_l == "deployment":
            icon = "[D]"
            border_color = "green"
        elif kind_l == "statefulset":
            icon = "[SS]"
            border_color = "magenta"
        elif kind_l == "configmap":
            icon = "[C]"
            border_color = "yellow"
        else:
            icon = "[R]"
            border_color = "cyan"
        
        # Set border color
        self.styles.border = ("solid", border_color)
        self.styles.width = 35
        self.styles.height = 5
        self.styles.padding = (0, 1)
        
        yield Label(f"{icon} {self.resource_name}", classes="card-name")
        yield Label(self.resource_kind, classes="card-kind")
        if self.resource_details:
            yield Label(self.resource_details, classes="card-details")


class K8sVisualizerApp(App):
    """Textual app for visualizing Kubernetes resources"""
    
    # Enable Ctrl+C to quit
    BINDINGS = [("ctrl+c", "quit", "Quit")]
    
    CSS = """
    Screen {
        background: $background;
    }
    
    #title {
        width: 100%;
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $primary;
        color: $text;
        margin-bottom: 1;
    }
    
    #services-workloads {
        width: 100%;
        height: auto;
        /* Allow scroll when content overflows */
        overflow-y: auto;
    }
    
    #configmaps {
        width: 100%;
        height: auto;
        /* Allow scroll when content overflows */
        overflow-y: auto;
    }
    
    .row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    
    ResourceCard {
        width: 35;
        height: 5;
        border: solid;
    }
    
    .card-name {
        text-style: bold;
    }
    
    .card-kind {
        text-style: dim;
    }
    
    .arrow {
        width: 14;
        height: 5;
        content-align: center middle;
    }
    
    .spacer {
        width: 35;
        height: 5;
    }
    
    #summary {
        width: 100%;
        height: auto;
        margin-top: 1;
        border-top: solid white;
        padding: 1;
    }
    """
    
    def __init__(self, output_dir: str = "k8s", resources: List[Dict] = None):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.resources = resources or []
        
    def compose(self):
        """Create the UI layout"""
        # Title
        yield Static("DOCK2K8S - KUBERNETES ARCHITECTURE", id="title")
        
        if not self.resources:
            yield Static(f"⚠  No Kubernetes resources found in {self.output_dir}/ directory")
            yield Static("   Run conversion to generate manifests first.")
            return
        
        # Separate resources by type
        services = [r for r in self.resources if r["kind"].lower() == "service"]
        deployments = [r for r in self.resources if r["kind"].lower() == "deployment"]
        statefulsets = [r for r in self.resources if r["kind"].lower() == "statefulset"]
        configmaps = [r for r in self.resources if r["kind"].lower() == "configmap"]
        
        workloads = deployments + statefulsets
        
        # Services and Workloads section
        if services or workloads:
            with Vertical(id="services-workloads"):
                yield Label("Services → Workloads")
                
                max_items = max(len(services), len(workloads))
                for i in range(max_items):
                    with Horizontal(classes="row"):
                        # Service card
                        if i < len(services):
                            svc = services[i]
                            yield ResourceCard(svc["kind"], svc["name"])
                        else:
                            yield Static("", classes="spacer")
                        
                        # Arrow
                        if i < len(services) and i < len(workloads):
                            if services[i].get("selector_app") == workloads[i]["name"]:
                                yield Static("──────▶", classes="arrow")
                            else:
                                yield Static("", classes="arrow")
                        else:
                            yield Static("", classes="arrow")
                        
                        # Workload card
                        if i < len(workloads):
                            wl = workloads[i]
                            details = f"Replicas: {wl.get('replicas', 1)}"
                            yield ResourceCard(wl["kind"], wl["name"], details)
                        else:
                            yield Static("", classes="spacer")
        
        # ConfigMaps section
        if configmaps:
            with Vertical(id="configmaps"):
                yield Label("Configuration")
                for cm in configmaps:
                    yield ResourceCard(cm["kind"], cm["name"])
        
        # Summary
        with Vertical(id="summary"):
            yield Label("Summary:")
            yield Label(f"● {len(services)} Service(s)")
            yield Label(f"● {len(deployments)} Deployment(s)")
            yield Label(f"● {len(statefulsets)} StatefulSet(s)")
            yield Label(f"● {len(configmaps)} ConfigMap(s)")


class K8sVisualizer:
    """Wrapper to maintain compatibility with existing interface"""
    
    def __init__(self, output_dir: str = "k8s"):
        self.output_dir = Path(output_dir)
        self.resources = []
        
    def load_resources(self):
        """Load Kubernetes manifests from output directory"""
        if not self.output_dir.is_absolute():
            self.output_dir = self.output_dir.resolve()
        
        if not self.output_dir.exists():
            return []
        
        resources = []
        for manifest_path in sorted(self.output_dir.glob("*.yml")) + sorted(self.output_dir.glob("*.yaml")):
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    docs = list(yaml.safe_load_all(f))
                    for doc in docs:
                        if not isinstance(doc, dict):
                            continue
                        kind = doc.get("kind", "").strip()
                        meta = doc.get("metadata", {})
                        name = meta.get("name", "").strip()
                        namespace = meta.get("namespace", "default")
                        
                        if not kind or not name:
                            continue
                        
                        selector_app = None
                        if kind.lower() == "service":
                            spec = doc.get("spec", {})
                            selector = spec.get("selector", {})
                            if isinstance(selector, dict):
                                selector_app = selector.get("app")
                        
                        replicas = None
                        if kind.lower() in ("deployment", "statefulset"):
                            spec = doc.get("spec", {})
                            replicas = spec.get("replicas", 1)
                        
                        resources.append({
                            "kind": kind,
                            "name": name,
                            "namespace": namespace,
                            "file": manifest_path.name,
                            "selector_app": selector_app,
                            "replicas": replicas
                        })
            except Exception:
                continue
        
        self.resources = resources
        return resources
        
    def display_architecture(self, auto_exit: bool = False):
        """Display the architecture using Textual"""
        self.load_resources()
        app = K8sVisualizerApp(str(self.output_dir), self.resources)
        app.run()
