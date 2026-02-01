"""TUI visualizer for Docker Compose (Pre-K8s Conversion)"""

from pathlib import Path
from typing import Dict, List, Any
import yaml

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Label


# -----------------------------
# Service Card
# -----------------------------
class ComposeServiceCard(Static):
    """Card widget for Docker Compose services"""

    def __init__(self, service_name: str, image: str = "", ports: List[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.service_name = service_name  # avoid Textual name conflict
        self.image = image
        self.ports = ports or []

    def compose(self) -> ComposeResult:
        self.styles.border = ("solid", "green")
        self.styles.width = 38
        self.styles.height = 6
        self.styles.padding = (0, 1)

        yield Label(f"[S] {self.service_name}", classes="card-name")

        if self.image:
            yield Label(f"Image: {self.image}", classes="card-detail")

        if self.ports:
            ports_str = ", ".join(self.ports[:2])
            yield Label(f"Ports: {ports_str}", classes="card-detail")


# -----------------------------
# Textual App
# -----------------------------
class ComposeVisualizerApp(App):
    """Textual app to visualize Docker Compose services"""

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

    /* IMPORTANT: allow vertical scrolling when content overflows */
    Vertical {
        overflow-y: auto;
    }

    .row {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }

    .arrow {
        width: 14;
        height: 6;
        content-align: center middle;
    }

    .spacer {
        width: 38;
        height: 6;
    }

    .card-name {
        text-style: bold;
    }

    .card-detail {
        text-style: dim;
    }

    #summary {
        border-top: solid white;
        padding: 1;
        margin-top: 1;
    }
    """

    def __init__(self, compose_file: Path, services: Dict[str, Any]):
        super().__init__()
        self.compose_file = compose_file
        self.services = services

    def compose(self) -> ComposeResult:
        yield Static(f"DOCK2K8S – DOCKER COMPOSE ARCHITECTURE", id="title")

        if not self.services:
            yield Static("⚠ No services found in compose file")
            return

        # Scrollable Vertical layout
        with Vertical():
            yield Label("Services & Dependencies")

            service_names = list(self.services.keys())
            for svc_name in service_names:
                svc = self.services[svc_name]
                depends = svc.get("depends_on", [])

                with Horizontal(classes="row"):
                    yield ComposeServiceCard(
                        service_name=svc_name,
                        image=svc.get("image", ""),
                        ports=svc.get("ports", [])
                    )

                    # show only first dependency
                    if depends:
                        yield Static("──────▶", classes="arrow")
                        dep = depends[0]
                        dep_svc = self.services.get(dep, {})
                        yield ComposeServiceCard(
                            service_name=dep,
                            image=dep_svc.get("image", ""),
                            ports=dep_svc.get("ports", [])
                        )
                    else:
                        yield Static("", classes="arrow")
                        yield Static("", classes="spacer")

        # Summary
        with Vertical(id="summary"):
            yield Label("Summary:")
            yield Label(f"● {len(self.services)} Service(s)")
            yield Label(f"● Compose file: {self.compose_file.name}")


# -----------------------------
# Wrapper (Like K8sVisualizer)
# -----------------------------
class ComposeVisualizer:
    """Docker Compose visualizer (Pre-Conversion)"""

    DEFAULT_NAMES = [
        "docker-compose.yml",
        "docker-compose.yaml",
        "compose.yml",
        "compose.yaml",
    ]

    def __init__(self, compose_file: str | None = None):
        self.compose_file = Path(compose_file) if compose_file else None
        self.services: Dict[str, Any] = {}

    def _find_compose_file(self) -> Path | None:
        if self.compose_file and self.compose_file.exists():
            return self.compose_file

        for name in self.DEFAULT_NAMES:
            p = Path(name)
            if p.exists():
                return p

        return None

    def load_services(self) -> Dict[str, Any]:
        compose_path = self._find_compose_file()
        if not compose_path:
            return {}

        with open(compose_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self.services = data.get("services", {})
        self.compose_file = compose_path
        return self.services

    def display_architecture(self):
        self.load_services()
        app = ComposeVisualizerApp(self.compose_file, self.services)
        app.run()
