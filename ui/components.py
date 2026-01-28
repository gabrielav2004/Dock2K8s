"""NiceGUI UI components for Dock2K8s"""
from typing import Optional, Callable, Dict, Any, List
from nicegui import ui
import httpx


class UIManager:
    """Manages UI state and API interactions"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.selected_service: Optional[str] = None
        self.graph_mode: str = "compose"  # "compose" | "k8s"
        self.project_ir: Optional[Dict[str, Any]] = None
        self.project_files: list = []
        self.k8s_resources: list = []
    
    async def fetch_ir(self):
        """Fetch intermediate representation"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/ir")
            if response.status_code == 200:
                self.project_ir = response.json()
                return self.project_ir
            else:
                ui.notify(f"Failed to load project IR: {response.text}", type="negative")
                return None
    
    async def fetch_files(self):
        """Fetch project files"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/project")
            if response.status_code == 200:
                self.project_files = response.json()
                return self.project_files
            else:
                ui.notify(f"Failed to load project files: {response.text}", type="negative")
                return []
    
    async def update_config(self, update: Dict[str, Any]):
        """Update config.yml"""
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{self.base_url}/api/config", json=update)
            if response.status_code == 200:
                ui.notify("Config updated successfully", type="positive")
                await self.fetch_ir()  # Refresh IR
                return True
            else:
                ui.notify(f"Failed to update config: {response.text}", type="negative")
                return False
    
    async def trigger_conversion(self):
        """Trigger conversion"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/api/convert")
            result = response.json()
            if result.get("success"):
                ui.notify(f"Conversion completed! Generated {len(result.get('generated_files', []))} files", type="positive")
                await self.fetch_files()  # Refresh file list
                return True
            else:
                ui.notify(f"Conversion failed: {result.get('message', 'Unknown error')}", type="negative")
                return False
    
    async def preview_service(self, service_name: str):
        """Preview generated YAML for a service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/preview/{service_name}")
            return response.json()

    async def fetch_k8s_resources(self) -> List[Dict[str, Any]]:
        """Fetch parsed Kubernetes resources from generated manifests"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/k8s/resources")
            if response.status_code == 200:
                self.k8s_resources = response.json() or []
                return self.k8s_resources
            ui.notify(f"Failed to load Kubernetes resources: {response.text}", type="negative")
            return []


def create_sidebar(ui_manager: UIManager, on_service_select: Callable, on_view_change: Optional[Callable] = None):
    """Create sidebar with project explorer"""
    with ui.column().classes("w-64 bg-gray-100 p-4 h-full"):
        ui.label("Project Explorer").classes("text-lg font-bold mb-4")

        # Graph view toggle
        ui.label("Graph View").classes("text-md font-semibold mb-2")
        view_toggle = ui.toggle(
            {"compose": "Compose", "k8s": "K8s"},
            value=ui_manager.graph_mode,
        ).props("dense").classes("w-full mb-2")

        def _on_toggle_change(e):
            ui_manager.graph_mode = e.value
            if on_view_change:
                on_view_change(e.value)

        view_toggle.on_value_change(_on_toggle_change)
        
        # Project files list
        file_list = ui.column().classes("w-full")
        
        async def refresh_files():
            files = await ui_manager.fetch_files()
            file_list.clear()
            with file_list:
                for file_info in files:
                    icon = "📁" if file_info["type"] == "directory" else "📄"
                    with ui.row().classes("w-full items-center p-2 hover:bg-gray-200 rounded cursor-pointer"):
                        ui.label(f"{icon} {file_info['name']}").classes("text-sm")
        
        refresh_button = ui.button("Refresh", icon="refresh").classes("mb-2")
        refresh_button.on_click(lambda: ui.timer(0.1, refresh_files, once=True))
        
        # Services list
        ui.label("Services").classes("text-md font-semibold mt-4 mb-2")
        services_list = ui.column().classes("w-full")
        
        async def refresh_services():
            services_list.clear()
            try:
                ir = await ui_manager.fetch_ir()
                if ir and ir.get("services"):
                    with services_list:
                        for service in ir.get("services", []):
                            service_name = service["name"]
                            btn = ui.button(
                                service_name,
                                icon="settings"
                            ).classes("w-full justify-start mb-1")
                            btn.on_click(lambda e, name=service_name: on_service_select(name))
                else:
                    with services_list:
                        ui.label("No services found").classes("text-gray-500 text-sm p-2")
            except Exception as e:
                with services_list:
                    ui.label(f"Error: {str(e)}").classes("text-red-500 text-sm p-2")
        
        refresh_services_button = ui.button("Refresh Services", icon="refresh").classes("mb-2")
        refresh_services_button.on_click(lambda: ui.timer(0.1, refresh_services, once=True))
        
        # Initial load
        ui.timer(0.1, refresh_files, once=True)
        ui.timer(0.2, refresh_services, once=True)
        
        return file_list, services_list


def create_graph_view(ui_manager: UIManager):
    """Create graph visualization (Compose or K8s)"""
    with ui.card().classes("w-full h-full p-4"):
        title_label = ui.label("Graph").classes("text-lg font-bold mb-2")
        subtitle_label = ui.label("").classes("text-sm text-gray-600 mb-4")
        
        # Status message container
        status_container = ui.column().classes("w-full")
        
        # Graph container (will be created dynamically)
        graph_container_ref = {"container": None}
        
        async def render_graph():
            status_container.clear()
            
            try:
                mode = ui_manager.graph_mode

                if mode == "compose":
                    title_label.text = "Compose View"
                    subtitle_label.text = "Services + depends_on (from docker-compose.yml)"
                    ir = await ui_manager.fetch_ir()
                    if not ir:
                        with status_container:
                            ui.label("No project found. Make sure you're in a directory with docker-compose.yml").classes("text-orange-600 p-4")
                        if graph_container_ref["container"]:
                            graph_container_ref["container"].set_visibility(False)
                        return

                    services = ir.get("services", [])
                    if not services:
                        with status_container:
                            ui.label("No services found in docker-compose.yml").classes("text-gray-600 p-4")
                        if graph_container_ref["container"]:
                            graph_container_ref["container"].set_visibility(False)
                        return

                    svg_content = generate_svg_compose_graph(services)

                else:
                    title_label.text = "Kubernetes View"
                    subtitle_label.text = "Generated resources (from output_dir manifests)"
                    resources = await ui_manager.fetch_k8s_resources()
                    if not resources:
                        with status_container:
                            ui.label("No generated Kubernetes manifests found yet. Run conversion to populate output_dir.").classes("text-gray-600 p-4")
                        if graph_container_ref["container"]:
                            graph_container_ref["container"].set_visibility(False)
                        return

                    svg_content = generate_svg_k8s_graph(resources)

                # Create or update graph container
                if graph_container_ref["container"] is None:
                    graph_container_ref["container"] = ui.html("", sanitize=False).classes("w-full")
                graph_container_ref["container"].set_visibility(True)

                graph_container_ref["container"].content = f"""
                    <div id="graph-container" style="width: 100%; height: 600px; border: 1px solid #ddd; background: white; overflow: auto;">
                        {svg_content}
                    </div>
                """
                graph_container_ref["container"].update()
                
            except Exception as e:
                with status_container:
                    ui.label(f"Error loading graph: {str(e)}").classes("text-red-600 p-4")
                if graph_container_ref["container"]:
                    graph_container_ref["container"].set_visibility(False)
        
        # Initial render
        ui.timer(0.3, render_graph, once=True)
        
        # Refresh button
        refresh_btn = ui.button("Refresh Graph", icon="refresh").classes("mt-2")
        refresh_btn.on_click(lambda: ui.timer(0.1, render_graph, once=True))
        
        # Store render function for external refresh
        graph_container_ref["render"] = render_graph
        
        return graph_container_ref


def generate_svg_compose_graph(services: list) -> str:
    """Compose graph: services + depends_on"""
    if not services:
        return '<text x="50%" y="50%" text-anchor="middle" fill="#666">No services found</text>'
    
    # Calculate layout
    num_services = len(services)
    cols = min(4, num_services)
    rows = (num_services + cols - 1) // cols
    
    width = 800
    height = 600
    node_width = 150
    node_height = 100
    padding = 50
    
    svg_parts = []
    
    # Draw nodes (services)
    for idx, service in enumerate(services):
        col = idx % cols
        row = idx // cols
        
        x = padding + col * (width // cols)
        y = padding + row * (height // rows)
        
        service_name = service["name"]
        
        # Get workload config with defaults
        workload_cfg = service.get("workload_config") or {}
        controller = workload_cfg.get("controller") or "Deployment"
        replicas = workload_cfg.get("replicas") or 1
        
        # Get service config with defaults
        svc_cfg = service.get("service_config") or {}
        has_service = svc_cfg.get("enabled", True)  # Default to True if not specified
        
        # Node rectangle
        color = "#4CAF50" if has_service else "#FF9800"
        svg_parts.append(f'''
            <rect x="{x}" y="{y}" width="{node_width}" height="{node_height}" 
                  fill="{color}" stroke="#333" stroke-width="2" rx="5"/>
            <text x="{x + node_width/2}" y="{y + 25}" text-anchor="middle" 
                  font-weight="bold" fill="white">{service_name}</text>
            <text x="{x + node_width/2}" y="{y + 45}" text-anchor="middle" 
                  font-size="12" fill="white">{controller}</text>
            <text x="{x + node_width/2}" y="{y + 65}" text-anchor="middle" 
                  font-size="11" fill="white">Replicas: {replicas}</text>
        ''')
        
        # Draw dependencies
        depends_on = service.get("depends_on", [])
        for dep_name in depends_on:
            # Find dependency service index
            dep_idx = next((i for i, s in enumerate(services) if s["name"] == dep_name), None)
            if dep_idx is not None:
                dep_col = dep_idx % cols
                dep_row = dep_idx // cols
                dep_x = padding + dep_col * (width // cols) + node_width / 2
                dep_y = padding + dep_row * (height // rows) + node_height
                
                # Arrow from dependency to this service
                from_x = x + node_width / 2
                from_y = y
                
                svg_parts.append(f'''
                    <line x1="{dep_x}" y1="{dep_y}" x2="{from_x}" y2="{from_y}" 
                          stroke="#666" stroke-width="2" marker-end="url(#arrowhead)"/>
                ''')
    
    # Arrow marker definition
    arrow_marker = '''
        <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="10" 
                    refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#666"/>
            </marker>
        </defs>
    '''
    
    return f'<svg width="{width}" height="{height}">{arrow_marker}{"".join(svg_parts)}</svg>'


def generate_svg_k8s_graph(resources: List[Dict[str, Any]]) -> str:
    """K8s graph: Service -> Workload edges parsed from generated YAMLs"""
    if not resources:
        return '<text x="50%" y="50%" text-anchor="middle" fill="#666">No Kubernetes resources found</text>'

    services = [r for r in resources if str(r.get("kind", "")).lower() == "service"]
    workloads = [r for r in resources if str(r.get("kind", "")).lower() in ("deployment", "statefulset")]

    width = 900
    height = max(260, 120 + max(len(services), len(workloads)) * 120)
    node_w = 240
    node_h = 70
    left_x = 60
    right_x = 600

    svg_parts: List[str] = []

    def node(x: int, y: int, title: str, subtitle: str, color: str, key: str) -> None:
        svg_parts.append(f'''
            <rect id="{key}" x="{x}" y="{y}" width="{node_w}" height="{node_h}"
                  fill="{color}" stroke="#333" stroke-width="2" rx="6"/>
            <text x="{x + 12}" y="{y + 28}" font-weight="bold" fill="white">{title}</text>
            <text x="{x + 12}" y="{y + 50}" font-size="12" fill="white">{subtitle}</text>
        ''')

    svc_pos: Dict[str, Dict[str, int]] = {}
    wl_pos: Dict[str, Dict[str, int]] = {}

    for i, s in enumerate(services):
        y = 60 + i * 120
        name = s.get("name", "service")
        subtitle = f"Service • {s.get('file', '')}"
        node(left_x, y, str(name), subtitle, "#1976D2", f"svc-{name}")
        svc_pos[str(name)] = {"x": left_x + node_w, "y": y + node_h // 2}

    for i, w in enumerate(workloads):
        y = 60 + i * 120
        name = w.get("name", "workload")
        kind = w.get("kind", "Workload")
        subtitle = f"{kind} • {w.get('file', '')}"
        color = "#2E7D32" if str(kind).lower() == "deployment" else "#6A1B9A"
        node(right_x, y, str(name), subtitle, color, f"wl-{name}")
        wl_pos[str(name)] = {"x": right_x, "y": y + node_h // 2}

    # Arrow marker
    arrow_marker = '''
        <defs>
            <marker id="arrowhead-k8s" markerWidth="10" markerHeight="10"
                    refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#666"/>
            </marker>
        </defs>
    '''
    svg_parts.insert(0, arrow_marker)

    # Edges: Service -> Workload based on selector_app
    for s in services:
        selector_app = s.get("selector_app")
        if not selector_app:
            continue
        from_name = str(s.get("name"))
        to_name = str(selector_app)
        if from_name in svc_pos and to_name in wl_pos:
            x1 = svc_pos[from_name]["x"]
            y1 = svc_pos[from_name]["y"]
            x2 = wl_pos[to_name]["x"]
            y2 = wl_pos[to_name]["y"]
            svg_parts.append(f'''
                <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                      stroke="#666" stroke-width="2" marker-end="url(#arrowhead-k8s)"/>
            ''')

    return f'<svg width="{width}" height="{height}">{"".join(svg_parts)}</svg>'


def create_properties_panel(ui_manager: UIManager, selected_service: Optional[str] = None, on_save_callback: Optional[Callable] = None):
    """Create properties panel for editing service configuration"""
    with ui.card().classes("w-full h-full p-4"):
        ui.label("Service Properties").classes("text-lg font-bold mb-4")
        
        if not selected_service:
            ui.label("Select a service from the sidebar to edit").classes("text-gray-500 p-4")
            return
        
        # Service name display
        ui.label(f"Service: {selected_service}").classes("text-md font-semibold mb-4")
        
        # Workload configuration
        with ui.expansion("Workload Configuration", icon="settings").classes("w-full mb-2"):
            replicas_input = ui.number(
                label="Replicas",
                value=1,
                min=1,
                max=100
            ).classes("w-full")
            
            controller_select = ui.select(
                ["Deployment", "StatefulSet"],
                label="Controller Type",
                value="Deployment"
            ).classes("w-full")
        
        # Kubernetes Service configuration
        with ui.expansion("Kubernetes Service", icon="device_hub").classes("w-full mb-2"):
            service_enabled = ui.checkbox("Enable Service", value=True)
            
            service_type_select = ui.select(
                ["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"],
                label="Service Type",
                value="ClusterIP"
            ).classes("w-full")
        
        # Load current values dynamically
        async def load_service_config():
            try:
                ir = await ui_manager.fetch_ir()
                if not ir:
                    ui.notify("Failed to load service configuration", type="warning")
                    return
                
                service_data = next(
                    (s for s in ir.get("services", []) if s["name"] == selected_service),
                    None
                )
                if service_data:
                    workload_cfg = service_data.get("workload_config", {})
                    svc_cfg = service_data.get("service_config", {})
                    
                    # Get defaults if not set
                    defaults = ir.get("defaults", {})
                    
                    replicas_input.value = workload_cfg.get("replicas") or defaults.get("replicas") or 1
                    controller_select.value = workload_cfg.get("controller") or defaults.get("controller") or "Deployment"
                    service_enabled.value = svc_cfg.get("enabled", True)
                    service_type_select.value = svc_cfg.get("type", "ClusterIP")
                else:
                    ui.notify(f"Service '{selected_service}' not found", type="warning")
            except Exception as e:
                ui.notify(f"Error loading config: {str(e)}", type="negative")
        
        ui.timer(0.1, load_service_config, once=True)
        
        # Save button
        async def save_config():
            try:
                update = {
                    "workloads": {
                        selected_service: {
                            "replicas": int(replicas_input.value),
                            "controller": controller_select.value
                        }
                    },
                    "services": {
                        selected_service: {
                            "enabled": service_enabled.value,
                            "type": service_type_select.value
                        }
                    }
                }
                success = await ui_manager.update_config(update)
                if success and on_save_callback:
                    await on_save_callback()  # Refresh graph after save
            except Exception as e:
                ui.notify(f"Error saving config: {str(e)}", type="negative")
        
        save_btn = ui.button("Save Configuration", icon="save", color="primary").classes("w-full mt-4")
        save_btn.on_click(lambda: ui.timer(0.1, save_config, once=True))
        
        return {
            "replicas": replicas_input,
            "controller": controller_select,
            "service_enabled": service_enabled,
            "service_type": service_type_select
        }


def create_action_buttons(ui_manager: UIManager, graph_refresh_callback: Optional[Callable] = None):
    """Create action buttons for conversion, save, preview"""
    with ui.row().classes("w-full gap-2 p-4"):
        convert_btn = ui.button(
            "Run Conversion",
            icon="play_arrow",
            color="primary"
        ).classes("flex-1")
        async def run_convert():
            success = await ui_manager.trigger_conversion()
            if success and graph_refresh_callback:
                await graph_refresh_callback()  # Refresh graph after conversion
        convert_btn.on_click(lambda: ui.timer(0.1, run_convert, once=True))
        
        preview_btn = ui.button(
            "Preview YAML",
            icon="preview",
            color="secondary"
        ).classes("flex-1")
        
        # Preview dialog
        preview_dialog = ui.dialog()
        with preview_dialog:
            with ui.card().classes("w-full max-w-4xl"):
                ui.label("Generated YAML Preview").classes("text-lg font-bold mb-4")
                preview_content = ui.code().classes("w-full h-96")
                
                async def show_preview():
                    if ui_manager.selected_service:
                        result = await ui_manager.preview_service(ui_manager.selected_service)
                        yaml_content = ""
                        if result.get("deployment_yaml"):
                            yaml_content += f"# Deployment\n{result['deployment_yaml']}\n\n"
                        if result.get("service_yaml"):
                            yaml_content += f"# Service\n{result['service_yaml']}"
                        preview_content.content = yaml_content
                        preview_dialog.open()
                    else:
                        ui.notify("Please select a service first", type="warning")
                
                preview_btn.on_click(lambda: ui.timer(0.1, show_preview, once=True))
                
                with ui.row().classes("w-full justify-end mt-4"):
                    ui.button("Close", on_click=preview_dialog.close)
        
        return convert_btn, preview_btn


def create_layout(ui_manager: UIManager):
    """Create main UI layout"""
    # Header
    with ui.header().classes("bg-blue-600 text-white"):
        ui.label("Dock2K8s UI").classes("text-2xl font-bold")
    
    # Properties panel container (needs to be accessible)
    properties_container = ui.column().classes("w-full mt-4")
    
    # Graph refresh callback (will be set by create_graph_view)
    graph_refresh_callback = {"callback": None}
    
    def update_properties_panel():
        properties_container.clear()
        with properties_container:
            create_properties_panel(ui_manager, ui_manager.selected_service, graph_refresh_callback["callback"])
    
    def on_service_select(name: str):
        ui_manager.selected_service = name
        update_properties_panel()
    
    # Main content area
    with ui.row().classes("w-full h-screen"):
        # Sidebar
        sidebar_col = ui.column().classes("h-full")
        def on_view_change(_mode: str):
            if graph_refresh_callback["callback"]:
                ui.timer(0.1, graph_refresh_callback["callback"], once=True)

        create_sidebar(ui_manager, on_service_select, on_view_change)
        
        # Main panel
        with ui.column().classes("flex-1 h-full p-4"):
            # Graph view
            graph_ref = create_graph_view(ui_manager)
            # Store refresh callback - use the render function from graph_ref
            async def refresh_graph():
                if graph_ref and graph_ref.get("render"):
                    await graph_ref["render"]()
            graph_refresh_callback["callback"] = refresh_graph
            
            # Properties panel
            properties_container
            
            # Action buttons with refresh callback
            create_action_buttons(ui_manager, refresh_graph)
    
    return ui_manager
