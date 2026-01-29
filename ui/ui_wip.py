"""NiceGUI UI components for Dock2K8s - Final Enhanced Version"""
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
        self.current_browse_path: Optional[str] = None
        self.workspace: Optional[Dict[str, Any]] = None
    
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
    
    async def browse_directory(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Browse a directory"""
        async with httpx.AsyncClient() as client:
            params = {"path": path} if path else {}
            response = await client.get(f"{self.base_url}/api/browse", params=params)
            if response.status_code == 200:
                return response.json() or []
            return []
    
    async def get_parent_path(self, path: str) -> Optional[str]:
        """Get parent directory path"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/browse/parent", params={"path": path})
            if response.status_code == 200:
                return response.json().get("path")
            return None
    
    async def get_home_path(self) -> Optional[str]:
        """Get home directory path"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/browse/home")
            if response.status_code == 200:
                return response.json().get("path")
            return None
    
    async def get_workspace(self) -> Optional[Dict[str, Any]]:
        """Get current workspace info"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/api/workspace")
            if response.status_code == 200:
                self.workspace = response.json()
                return self.workspace
            return None
    
    async def set_workspace(self, path: str) -> bool:
        """Set workspace to a directory"""
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/api/workspace", params={"path": path})
            if response.status_code == 200:
                result = response.json()
                ui.notify(f"Opened project: {result.get('name', path)}", type="positive")
                self.workspace = await self.get_workspace()
                return True
            else:
                error = response.json().get("detail", "Failed to open project")
                ui.notify(error, type="negative")
                return False


def format_size(size: int) -> str:
    """Format file size in human-readable format"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"


def create_file_browser(ui_manager: UIManager, on_project_open: Optional[Callable] = None, show_create_options: bool = True):
    """Create a modern file browser with project creation support"""
    
    current_path_ref = {"path": None}
    
    with ui.card().classes("w-full shadow-lg border-0").style("""
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        overflow: hidden;
    """):
        # Modern header with gradient
        with ui.row().classes("w-full items-center justify-between p-6").style("background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("folder_special", size="2rem").classes("text-white drop-shadow-lg")
                with ui.column().classes("gap-0"):
                    ui.label("Project Explorer").classes("text-2xl font-bold text-white m-0")
                    ui.label("Navigate and manage your projects").classes("text-sm text-white opacity-90 m-0")
            
            # Create new project button (optional)
            if show_create_options:
                with ui.row().classes("gap-2"):
                    create_folder_btn = ui.button("New Folder", icon="create_new_folder").props("outline").classes("text-white border-white")
                    create_project_btn = (
    ui.button("New Project", icon="add")
    .props("unelevated")
    .classes("font-semibold text-white")
    .style("""
        background: linear-gradient(135deg, #facc15 0%, #f59e0b 50%, #d97706 100%);
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(245, 158, 11, 0.35);
    """)
)

                    
        
        # Navigation bar
        with ui.row().classes("w-full items-center px-4 py-3 gap-2").style("""
            background: rgba(255,255,255,0.95);
            border-bottom: 1px solid rgba(0,0,0,0.05);
        """):
            home_btn = ui.button(icon="home").props("flat round").classes("text-purple-600 hover:bg-purple-50")
            up_btn = ui.button(icon="arrow_upward").props("flat round").classes("text-purple-600 hover:bg-purple-50")
            refresh_btn = ui.button(icon="refresh").props("flat round").classes("text-purple-600 hover:bg-purple-50")
            
            with ui.row().classes("flex-1 items-center gap-2 px-3 py-2 rounded-lg").style("background: #f5f5f5;"):
                ui.icon("folder", size="sm").classes("text-gray-600")
                path_label = ui.label("").classes("text-sm text-gray-700 font-medium")
        
        # File list container
        file_list_container = ui.column().classes("w-full p-4 gap-2").style("""
            max-height: 500px;
            overflow-y: auto;
            background: rgba(255,255,255,0.98);
        """)
        
        # Dialogs for file/folder creation
        if show_create_options:
            # Create folder dialog
            create_folder_dialog = ui.dialog()
            with create_folder_dialog:
                with ui.card().classes("w-96"):
                    ui.label("Create New Folder").classes("text-xl font-bold mb-4")
                    folder_name_input = ui.input("Folder Name", placeholder="my-folder").classes("w-full")
                    with ui.row().classes("w-full justify-end gap-2 mt-4"):
                        ui.button("Cancel", on_click=create_folder_dialog.close).props("flat")
                        async def create_folder():
                            folder_name = folder_name_input.value.strip()
                            if not folder_name:
                                ui.notify("Please enter a folder name", type="warning")
                                return
                            
                            current_path = current_path_ref["path"] or await ui_manager.get_home_path()
                            
                            try:
                                async with httpx.AsyncClient() as client:
                                    response = await client.post(
                                        f"{ui_manager.base_url}/api/folder/create",
                                        params={"path": current_path, "name": folder_name}
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        ui.notify(result.get("message", "Folder created"), type="positive")
                                        create_folder_dialog.close()
                                        folder_name_input.value = ""
                                        await refresh_current()
                                    else:
                                        error = response.json().get("detail", "Failed to create folder")
                                        ui.notify(error, type="negative")
                            except Exception as e:
                                ui.notify(f"Error creating folder: {str(e)}", type="negative")
                        
                        ui.button("Create", on_click=lambda: ui.timer(0.1, create_folder, once=True)).props("unelevated")
            
            # Create project dialog
            create_project_dialog = ui.dialog()
            with create_project_dialog:
                with ui.card().classes("w-96"):
                    ui.label("Create New Dock2K8s Project").classes("text-xl font-bold mb-4")
                    project_name_input = ui.input("Project Name", placeholder="my-project").classes("w-full")
                    ui.label("This will create a new folder with a sample docker-compose.yml file").classes("text-sm text-gray-600 mt-2")
                    with ui.row().classes("w-full justify-end gap-2 mt-4"):
                        ui.button("Cancel", on_click=create_project_dialog.close).props("flat")
                        async def create_project():
                            project_name = project_name_input.value.strip()
                            if not project_name:
                                ui.notify("Please enter a project name", type="warning")
                                return
                            
                            current_path = current_path_ref["path"] or await ui_manager.get_home_path()
                            
                            try:
                                async with httpx.AsyncClient() as client:
                                    response = await client.post(
                                        f"{ui_manager.base_url}/api/project/create",
                                        params={"path": current_path, "name": project_name}
                                    )
                                    
                                    if response.status_code == 200:
                                        result = response.json()
                                        ui.notify(result.get("message", "Project created"), type="positive")
                                        create_project_dialog.close()
                                        project_name_input.value = ""
                                        await refresh_current()
                                    else:
                                        error = response.json().get("detail", "Failed to create project")
                                        ui.notify(error, type="negative")
                            except Exception as e:
                                ui.notify(f"Error creating project: {str(e)}", type="negative")
                        
                        ui.button("Create", on_click=lambda: ui.timer(0.1, create_project, once=True)).props("unelevated")
            
            create_folder_btn.on_click(create_folder_dialog.open)
            create_project_btn.on_click(create_project_dialog.open)
        
        async def navigate_to(path: Optional[str]):
            """Navigate to a directory"""
            current_path_ref["path"] = path
            entries = await ui_manager.browse_directory(path)
            
            path_label.text = path or "Home"
            
            file_list_container.clear()
            
            with file_list_container:
                if not entries:
                    with ui.row().classes("w-full justify-center items-center p-8"):
                        ui.icon("folder_off", size="3rem").classes("text-gray-300")
                        ui.label("Empty directory").classes("text-gray-400 ml-3")
                    return
                
                for entry in entries:
                    is_dir = entry.get("is_dir", False)
                    is_project = entry.get("is_project", False)
                    name = entry.get("name", "")
                    entry_path = entry.get("path", "")
                    size = entry.get("size")
                    modified = entry.get("modified", "")
                    
                    with ui.card().classes("w-full cursor-pointer transition-all hover:shadow-md").style(f"""
                        border: 2px solid {'#10b981' if is_project else 'transparent'};
                        border-radius: 12px;
                        background: {'linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%)' if is_project else 'white'};
                        padding: 0;
                        margin: 0;
                    """) as row:
                        with ui.row().classes("w-full items-center p-4 gap-3"):
                            if is_project:
                                with ui.avatar().classes("shadow-md").style("background: linear-gradient(135deg, #10b981 0%, #059669 100%);"):
                                    ui.icon("rocket_launch", color="white")
                            elif is_dir:
                                with ui.avatar(color="orange").classes("shadow-sm"):
                                    ui.icon("folder", color="white")
                            else:
                                icon_name = "description" if name.endswith(('.yml', '.yaml')) else "code" if name.endswith('.py') else "insert_drive_file"
                                with ui.avatar(color="blue-grey-2"):
                                    ui.icon(icon_name, color="blue-grey-7")
                            
                            with ui.column().classes("flex-1 gap-1"):
                                name_classes = "font-semibold text-base m-0"
                                if is_project:
                                    name_classes += " text-green-800"
                                ui.label(name).classes(name_classes)
                                
                                with ui.row().classes("items-center gap-3 text-xs"):
                                    if is_project:
                                        ui.badge("DOCKER COMPOSE PROJECT", color="green").classes("text-xs font-bold")
                                    if not is_dir and size is not None:
                                        ui.label(f"📦 {format_size(size)}").classes("text-gray-500")
                                    if modified:
                                        ui.label(f"🕒 {modified}").classes("text-gray-500")
                            
                            if is_project:
                                async def open_project(p=entry_path):
                                    success = await ui_manager.set_workspace(p)
                                    if success and on_project_open:
                                        on_project_open()
                                
                                ui.button("Open Project", icon="launch").props("unelevated").classes("bg-green-600 text-white").style("""
                                    border-radius: 8px;
                                    font-weight: 600;
                                    padding: 8px 20px;
                                """).on_click(lambda e, p=entry_path: ui.timer(0.1, lambda: open_project_wrapper(p), once=True))
                    
                    if is_dir:
                        row.on("click", lambda e, p=entry_path: ui.timer(0.1, lambda: navigate_wrapper(p), once=True))
        
        def navigate_wrapper(path: str):
            async def _nav():
                await navigate_to(path)
            return _nav()
        
        def open_project_wrapper(path: str):
            async def _open():
                success = await ui_manager.set_workspace(path)
                if success and on_project_open:
                    on_project_open()
            return _open()
        
        async def go_home():
            home = await ui_manager.get_home_path()
            if home:
                await navigate_to(home)
        
        async def go_up():
            if current_path_ref["path"]:
                parent = await ui_manager.get_parent_path(current_path_ref["path"])
                if parent:
                    await navigate_to(parent)
        
        async def refresh_current():
            await navigate_to(current_path_ref["path"])
        
        home_btn.on_click(lambda: ui.timer(0.1, go_home, once=True))
        up_btn.on_click(lambda: ui.timer(0.1, go_up, once=True))
        refresh_btn.on_click(lambda: ui.timer(0.1, refresh_current, once=True))
        
        ui.timer(0.1, go_home, once=True)
    
    return current_path_ref


    """Create modern sidebar with better visual hierarchy"""
    with ui.column().classes("h-full shadow-xl").style("""
        width: 320px;
        background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    """):
        with ui.row().classes("w-full items-center p-6 gap-3").style("border-bottom: 1px solid rgba(255,255,255,0.1);"):
            ui.icon("dashboard", size="lg").classes("text-blue-400")
            ui.label("Dashboard").classes("text-xl font-bold text-white")
        
        with ui.column().classes("flex-1 p-4 gap-6 overflow-y-auto"):
            with ui.card().classes("w-full border-0").style("""
                background: rgba(255,255,255,0.05);
                border-radius: 12px;
                padding: 16px;
            """):
                ui.label("Visualization Mode").classes("text-sm font-semibold text-white opacity-80 mb-3")
                view_toggle = ui.toggle(
                    {"compose": "Docker Compose", "k8s": "Kubernetes"},
                    value=ui_manager.graph_mode,
                ).classes("w-full").style("""
                    background: rgba(255,255,255,0.1);
                    border-radius: 8px;
                    padding: 4px;
                """)

                def _on_toggle_change(e):
                    ui_manager.graph_mode = e.value
                    if on_view_change:
                        on_view_change(e.value)

                view_toggle.on_value_change(_on_toggle_change)
            
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Project Files").classes("text-sm font-semibold text-white opacity-80")
                    refresh_button = ui.button(icon="refresh").props("flat round dense").classes("text-white opacity-60 hover:opacity-100")
                
                file_list = ui.column().classes("w-full gap-1")
                
                async def refresh_files():
                    files = await ui_manager.fetch_files()
                    file_list.clear()
                    with file_list:
                        if not files:
                            ui.label("No files").classes("text-gray-400 text-sm p-2")
                        else:
                            for file_info in files:
                                icon = "📁" if file_info["type"] == "directory" else "📄"
                                with ui.row().classes("w-full items-center p-2 rounded-lg transition-colors").style("""
                                    background: rgba(255,255,255,0.03);
                                    cursor: pointer;
                                """).on("mouseenter", lambda e: e.sender.style("background: rgba(255,255,255,0.08)")).on("mouseleave", lambda e: e.sender.style("background: rgba(255,255,255,0.03)")):
                                    ui.label(f"{icon}").classes("text-lg")
                                    ui.label(file_info['name']).classes("text-sm text-white ml-2")
                
                refresh_button.on_click(lambda: ui.timer(0.1, refresh_files, once=True))
            
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Services").classes("text-sm font-semibold text-white opacity-80")
                    refresh_services_button = ui.button(icon="refresh").props("flat round dense").classes("text-white opacity-60 hover:opacity-100")
                
                services_list = ui.column().classes("w-full gap-1")
                
                async def refresh_services():
                    services_list.clear()
                    try:
                        ir = await ui_manager.fetch_ir()
                        if ir and ir.get("services"):
                            with services_list:
                                for service in ir.get("services", []):
                                    service_name = service["name"]
                                    is_selected = ui_manager.selected_service == service_name
                                    
                                    btn = ui.button(
                                        service_name,
                                        icon="settings"
                                    ).props("flat").classes(f"w-full justify-start text-left").style(f"""
                                        border-radius: 8px;
                                        padding: 10px 12px;
                                        background: {'rgba(59, 130, 246, 0.2)' if is_selected else 'rgba(255,255,255,0.03)'};
                                        color: {'#60a5fa' if is_selected else 'white'};
                                        border-left: 3px solid {'#3b82f6' if is_selected else 'transparent'};
                                    """)
                                    btn.on_click(lambda e, name=service_name: on_service_select(name))
                        else:
                            with services_list:
                                ui.label("No services found").classes("text-gray-400 text-sm p-2")
                    except Exception as e:
                        with services_list:
                            ui.label(f"Error: {str(e)}").classes("text-red-400 text-sm p-2")
                
                refresh_services_button.on_click(lambda: ui.timer(0.1, refresh_services, once=True))
        
        ui.timer(0.1, refresh_files, once=True)
        ui.timer(0.2, refresh_services, once=True)
        
        return file_list, services_list


    """Create modern graph visualization"""
    with ui.card().classes("w-full shadow-lg border-0").style("""
        border-radius: 16px;
        overflow: hidden;
        background: white;
    """):
        with ui.row().classes("w-full items-center p-6 gap-4").style("""
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        """):
            ui.icon("account_tree", size="2rem").classes("text-white")
            with ui.column().classes("flex-1 gap-1"):
                title_label = ui.label("Architecture Graph").classes("text-2xl font-bold text-white m-0")
                subtitle_label = ui.label("").classes("text-sm text-white opacity-90 m-0")
            
            refresh_btn = ui.button("Refresh", icon="refresh").props("outline").classes("text-white border-white hover:bg-white hover:text-blue-600")
        
        with ui.column().classes("p-6 gap-4"):
            status_container = ui.column().classes("w-full")
            graph_container_ref = {"container": None}
            
            async def render_graph():
                status_container.clear()
                
                try:
                    mode = ui_manager.graph_mode

                    if mode == "compose":
                        subtitle_label.text = "Services + Dependencies (from docker-compose.yml)"
                        ir = await ui_manager.fetch_ir()
                        if not ir:
                            with status_container:
                                with ui.card().classes("w-full bg-orange-50 border-l-4 border-orange-400"):
                                    with ui.row().classes("items-center gap-3 p-4"):
                                        ui.icon("warning", color="orange")
                                        ui.label("No project found. Make sure you're in a directory with docker-compose.yml").classes("text-orange-800")
                            if graph_container_ref["container"]:
                                graph_container_ref["container"].set_visibility(False)
                            return

                        services = ir.get("services", [])
                        if not services:
                            with status_container:
                                with ui.card().classes("w-full bg-gray-50"):
                                    with ui.row().classes("items-center gap-3 p-4"):
                                        ui.icon("info", color="grey")
                                        ui.label("No services found in docker-compose.yml").classes("text-gray-600")
                            if graph_container_ref["container"]:
                                graph_container_ref["container"].set_visibility(False)
                            return

                        svg_content = generate_svg_compose_graph(services)

                    else:
                        subtitle_label.text = "Generated Resources (from output_dir manifests)"
                        resources = await ui_manager.fetch_k8s_resources()
                        if not resources:
                            with status_container:
                                with ui.card().classes("w-full bg-blue-50 border-l-4 border-blue-400"):
                                    with ui.row().classes("items-center gap-3 p-4"):
                                        ui.icon("info", color="blue")
                                        ui.label("No generated Kubernetes manifests found yet. Run conversion to populate output_dir.").classes("text-blue-800")
                            if graph_container_ref["container"]:
                                graph_container_ref["container"].set_visibility(False)
                            return

                        svg_content = generate_svg_k8s_graph(resources)

                    if graph_container_ref["container"] is None:
                        graph_container_ref["container"] = ui.html("", sanitize=False).classes("w-full")
                    graph_container_ref["container"].set_visibility(True)

                    graph_container_ref["container"].content = f"""
                        <div style="
                            width: 100%;
                            height: 600px;
                            border: 2px solid #e5e7eb;
                            border-radius: 12px;
                            background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
                            overflow: auto;
                            padding: 20px;
                            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
                        ">
                            {svg_content}
                        </div>
                    """
                    graph_container_ref["container"].update()
                    
                except Exception as e:
                    with status_container:
                        with ui.card().classes("w-full bg-red-50 border-l-4 border-red-400"):
                            with ui.row().classes("items-center gap-3 p-4"):
                                ui.icon("error", color="red")
                                ui.label(f"Error loading graph: {str(e)}").classes("text-red-800")
                    if graph_container_ref["container"]:
                        graph_container_ref["container"].set_visibility(False)
            
            ui.timer(0.3, render_graph, once=True)
            
            refresh_btn.on_click(lambda: ui.timer(0.1, render_graph, once=True))
            
            graph_container_ref["render"] = render_graph
            
        return graph_container_ref


def generate_svg_compose_graph(services: list) -> str:
    """Enhanced Compose graph with modern styling"""
    if not services:
        return '<text x="50%" y="50%" text-anchor="middle" fill="#6b7280" font-size="16">No services found</text>'
    
    num_services = len(services)
    cols = min(4, num_services)
    rows = (num_services + cols - 1) // cols
    
    width = 800
    height = 600
    node_width = 160
    node_height = 110
    padding = 60
    
    svg_parts = []
    
    svg_parts.append('''
        <defs>
            <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
                <feOffset dx="0" dy="2" result="offsetblur"/>
                <feComponentTransfer>
                    <feFuncA type="linear" slope="0.3"/>
                </feComponentTransfer>
                <feMerge>
                    <feMergeNode/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <marker id="arrowhead" markerWidth="10" markerHeight="10" 
                    refX="9" refY="3" orient="auto">
                <polygon points="0 0, 10 3, 0 6" fill="#6b7280"/>
            </marker>
            <linearGradient id="deploymentGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#059669;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="serviceGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#d97706;stop-opacity:1" />
            </linearGradient>
        </defs>
    ''')
    
    for idx, service in enumerate(services):
        col = idx % cols
        row = idx // cols
        
        x = padding + col * (width // cols)
        y = padding + row * (height // rows)
        
        service_name = service["name"]
        workload_cfg = service.get("workload_config") or {}
        controller = workload_cfg.get("controller") or "Deployment"
        replicas = workload_cfg.get("replicas") or 1
        svc_cfg = service.get("service_config") or {}
        has_service = svc_cfg.get("enabled", True)
        
        color = "url(#deploymentGrad)" if has_service else "url(#serviceGrad)"
        
        svg_parts.append(f'''
            <rect x="{x}" y="{y}" width="{node_width}" height="{node_height}" 
                  fill="{color}" stroke="none" rx="8" filter="url(#shadow)"/>
            <text x="{x + node_width/2}" y="{y + 30}" text-anchor="middle" 
                  font-weight="700" font-size="14" fill="white">{service_name}</text>
            <text x="{x + node_width/2}" y="{y + 55}" text-anchor="middle" 
                  font-size="12" fill="white" opacity="0.9">{controller}</text>
            <text x="{x + node_width/2}" y="{y + 75}" text-anchor="middle" 
                  font-size="11" fill="white" opacity="0.8">⚙️ {replicas} replica{'s' if replicas != 1 else ''}</text>
        ''')
        
        depends_on = service.get("depends_on", [])
        for dep_name in depends_on:
            dep_idx = next((i for i, s in enumerate(services) if s["name"] == dep_name), None)
            if dep_idx is not None:
                dep_col = dep_idx % cols
                dep_row = dep_idx // cols
                dep_x = padding + dep_col * (width // cols) + node_width / 2
                dep_y = padding + dep_row * (height // rows) + node_height
                
                from_x = x + node_width / 2
                from_y = y
                
                svg_parts.append(f'''
                    <line x1="{dep_x}" y1="{dep_y}" x2="{from_x}" y2="{from_y}" 
                          stroke="#6b7280" stroke-width="2" stroke-dasharray="5,5" 
                          marker-end="url(#arrowhead)" opacity="0.6"/>
                ''')
    
    return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">{"".join(svg_parts)}</svg>'


def generate_svg_k8s_graph(resources: List[Dict[str, Any]]) -> str:
    """Enhanced K8s graph with modern styling"""
    if not resources:
        return '<text x="50%" y="50%" text-anchor="middle" fill="#6b7280" font-size="16">No Kubernetes resources found</text>'

    services = [r for r in resources if str(r.get("kind", "")).lower() == "service"]
    workloads = [r for r in resources if str(r.get("kind", "")).lower() in ("deployment", "statefulset")]

    width = 900
    height = max(300, 120 + max(len(services), len(workloads)) * 140)
    node_w = 250
    node_h = 80
    left_x = 60
    right_x = 600

    svg_parts: List[str] = []
    
    svg_parts.append('''
        <defs>
            <filter id="shadow-k8s" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur in="SourceAlpha" stdDeviation="4"/>
                <feOffset dx="0" dy="3" result="offsetblur"/>
                <feComponentTransfer>
                    <feFuncA type="linear" slope="0.25"/>
                </feComponentTransfer>
                <feMerge>
                    <feMergeNode/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
            <marker id="arrowhead-k8s" markerWidth="12" markerHeight="12"
                    refX="10" refY="3" orient="auto">
                <polygon points="0 0, 12 3, 0 6" fill="#3b82f6"/>
            </marker>
            <linearGradient id="serviceGradK8s" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#1d4ed8;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="deploymentGradK8s" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#10b981;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#047857;stop-opacity:1" />
            </linearGradient>
            <linearGradient id="statefulsetGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#8b5cf6;stop-opacity:1" />
                <stop offset="100%" style="stop-color:#6d28d9;stop-opacity:1" />
            </linearGradient>
        </defs>
    ''')

    def node(x: int, y: int, title: str, subtitle: str, gradient: str, key: str, icon: str) -> None:
        svg_parts.append(f'''
            <rect id="{key}" x="{x}" y="{y}" width="{node_w}" height="{node_h}"
                  fill="{gradient}" stroke="none" rx="10" filter="url(#shadow-k8s)"/>
            <text x="{x + 20}" y="{y + 32}" font-weight="700" font-size="15" fill="white">{icon} {title}</text>
            <text x="{x + 20}" y="{y + 56}" font-size="11" fill="white" opacity="0.85">{subtitle}</text>
        ''')

    svc_pos: Dict[str, Dict[str, int]] = {}
    wl_pos: Dict[str, Dict[str, int]] = {}

    for i, s in enumerate(services):
        y = 60 + i * 140
        name = s.get("name", "service")
        subtitle = f"Service • {s.get('file', 'manifest.yaml')}"
        node(left_x, y, str(name), subtitle, "url(#serviceGradK8s)", f"svc-{name}", "🌐")
        svc_pos[str(name)] = {"x": left_x + node_w, "y": y + node_h // 2}

    for i, w in enumerate(workloads):
        y = 60 + i * 140
        name = w.get("name", "workload")
        kind = w.get("kind", "Workload")
        subtitle = f"{kind} • {w.get('file', 'manifest.yaml')}"
        gradient = "url(#deploymentGradK8s)" if str(kind).lower() == "deployment" else "url(#statefulsetGrad)"
        icon = "🚀" if str(kind).lower() == "deployment" else "💾"
        node(right_x, y, str(name), subtitle, gradient, f"wl-{name}", icon)
        wl_pos[str(name)] = {"x": right_x, "y": y + node_h // 2}

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
                      stroke="#3b82f6" stroke-width="3" marker-end="url(#arrowhead-k8s)" opacity="0.7"/>
            ''')

    return f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">{"".join(svg_parts)}</svg>'


    """Create modern action buttons"""
    with ui.card().classes("w-full shadow-lg border-0").style("""
        border-radius: 16px;
        background: linear-gradient(135deg, #f9fafb 0%, #ffffff 100%);
    """):
        with ui.row().classes("w-full gap-4 p-6"):
            convert_btn = ui.button(
                "Run Conversion",
                icon="play_circle"
            ).props("unelevated").classes("flex-1").style("""
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                color: white;
                font-weight: 600;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
            """)
            
            async def run_convert():
                success = await ui_manager.trigger_conversion()
                if success and graph_refresh_callback:
                    await graph_refresh_callback()
            
            convert_btn.on_click(lambda: ui.timer(0.1, run_convert, once=True))
            
            preview_btn = ui.button(
                "Preview YAML",
                icon="visibility"
            ).props("outline").classes("flex-1").style("""
                border: 2px solid #3b82f6;
                color: #3b82f6;
                font-weight: 600;
                padding: 16px;
                border-radius: 12px;
                font-size: 16px;
            """)
            
            preview_dialog = ui.dialog()
            with preview_dialog:
                with ui.card().classes("w-full max-w-4xl border-0 shadow-2xl").style("border-radius: 16px;"):
                    with ui.row().classes("w-full items-center p-6 gap-3").style("""
                        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                    """):
                        ui.icon("code", size="2rem").classes("text-white")
                        ui.label("Generated YAML Preview").classes("text-2xl font-bold text-white")
                    
                    with ui.column().classes("p-6"):
                        preview_content = ui.code().classes("w-full").style("max-height: 500px; overflow-y: auto;")
                        
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
                            ui.button("Close", on_click=preview_dialog.close).props("flat").classes("text-indigo-600")
        
        return convert_btn, preview_btn


    """Create modern main UI layout with improved navigation"""
    
    # Reference to properties panel for scrolling
    properties_panel_ref = {"element": None}
    
    with ui.header().classes("shadow-lg").style("""
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 16px 24px;
    """):
        with ui.row().classes("w-full items-center"):
            with ui.row().classes("items-center gap-4"):
                ui.icon("layers", size="2rem").classes("text-blue-400")
                ui.label("Dock2K8s").classes("text-3xl font-bold text-white")
            
            ui.space()
            
            with ui.row().classes("items-center gap-3"):
                workspace_badge = ui.badge("", color="blue").classes("text-sm px-3 py-1")
                
                async def load_workspace_info():
                    workspace = await ui_manager.get_workspace()
                    if workspace:
                        workspace_badge.text = f"📁 {workspace.get('name', 'Unknown')}"
                
                ui.timer(0.1, load_workspace_info, once=True)
                
                ui.button("Change Project", icon="folder_open").props("flat dense").classes("text-white hover:bg-white/10").style("""
                    border-radius: 8px;
                    padding: 8px 16px;
                """).on_click(lambda: ui.navigate.to("/"))
    
    # Main layout with two columns
    properties_container = ui.column().classes("w-full")
    graph_refresh_callback = {"callback": None}
    
    def update_properties_panel():
        properties_container.clear()
        with properties_container:
            panel = create_properties_panel(ui_manager, ui_manager.selected_service, graph_refresh_callback["callback"])
            properties_panel_ref["element"] = properties_container
        
        # Auto-scroll to properties panel when service is selected
        if properties_panel_ref["element"]:
            ui.run_javascript("""
                setTimeout(() => {
                    const element = document.querySelector('.properties-panel-container');
                    if (element) {
                        element.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }, 100);
            """)
    
    def on_service_select(name: str):
        ui_manager.selected_service = name
        update_properties_panel()
    
    with ui.row().classes("w-full").style("height: calc(100vh - 80px);"):
        def on_view_change(_mode: str):
            if graph_refresh_callback["callback"]:
                ui.timer(0.1, graph_refresh_callback["callback"], once=True)

        create_sidebar(ui_manager, on_service_select, on_view_change)
        
        # Main content area - single scrollable column
        with ui.column().classes("flex-1 overflow-y-auto").style("""
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        """):
            with ui.column().classes("p-6 gap-6"):
                # Graph view at top
                graph_ref = create_graph_view(ui_manager)
                
                async def refresh_graph():
                    if graph_ref and graph_ref.get("render"):
                        await graph_ref["render"]()
                
                graph_refresh_callback["callback"] = refresh_graph
                
                # Properties panel directly below (scrolls into view)
                with ui.column().classes("w-full properties-panel-container"):
                    properties_container
                
                # Action buttons at bottom
                create_action_buttons(ui_manager, refresh_graph)
    
    return ui_manager

def create_home_page(ui_manager: UIManager, on_project_open: Optional[Callable] = None):
    """Create a modern, visually stunning home page"""
    
    ui.query('body').style('margin: 0; padding: 0;')
    
    with ui.column().classes("w-full items-center").style("""
        min-height: 100vh;
        background: linear-gradient(-45deg, #667eea, #764ba2, #f093fb, #4facfe);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        padding: 0;
        margin: 0;
    """):
        with ui.row().classes("w-full items-center shadow-lg").style("""
            background: rgba(30, 41, 59, 0.95);
            backdrop-filter: blur(10px);
            padding: 20px 40px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        """):
            with ui.row().classes("items-center gap-4"):
                ui.icon("layers", size="2.5rem").classes("text-blue-400")
                ui.label("Dock2K8s").classes("text-4xl font-black text-white").style("""
                    letter-spacing: -1px;
                    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
                """)
            
            ui.space()
            
            with ui.row().classes("gap-3"):
                ui.badge("v1.0", color="blue").classes("text-sm px-3 py-1")
        
        with ui.column().classes("w-full items-center justify-center flex-1 px-8 py-12").style("""
            animation: fadeIn 1s ease-out;
        """):
            with ui.column().classes("items-center gap-8 mb-12 text-center"):
                with ui.card().classes("border-0 shadow-2xl").style("""
                    width: 160px;
                    height: 160px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    animation: float 3s ease-in-out infinite;
                """):
                    ui.icon("transform", size="5rem").classes("text-purple-600")
                
                ui.label("Transform Docker Compose").classes("text-5xl font-black text-white m-0").style("""
                    text-shadow: 0 4px 20px rgba(0,0,0,0.4);
                    animation: slideInDown 0.8s ease-out;
                """)
                
                ui.label("into Kubernetes Manifests").classes("text-5xl font-black m-0").style("""
                    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    text-shadow: 0 4px 20px rgba(251, 191, 36, 0.3);
                    animation: slideInDown 0.8s ease-out 0.2s both;
                """)
                
                ui.label("Seamlessly convert your Docker Compose projects to production-ready Kubernetes resources").classes("text-xl text-white opacity-95 max-w-3xl mt-4").style("""
                    text-shadow: 0 2px 10px rgba(0,0,0,0.3);
                    line-height: 1.6;
                    animation: slideInDown 0.8s ease-out 0.4s both;
                """)
            
            with ui.card().classes("w-full max-w-5xl border-0 shadow-2xl").style("""
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.5);
                animation: scaleIn 0.6s ease-out 0.6s both;
            """):
                with ui.row().classes("w-full items-center p-8 border-b").style("border-color: rgba(0,0,0,0.05);"):
                    with ui.column().classes("flex-1"):
                        ui.label("Select a Project").classes("text-3xl font-bold text-gray-900 m-0")
                        ui.label("Browse your files and select a folder containing docker-compose.yml").classes("text-gray-600 mt-2")
                    
                    with ui.row().classes("gap-4"):
                        for stat in [("⚡", "Fast"), ("🎨", "Visual"), ("🚀", "Easy")]:
                            with ui.card().classes("border-0").style("""
                                background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
                                padding: 12px 20px;
                                border-radius: 12px;
                            """):
                                with ui.row().classes("items-center gap-2"):
                                    ui.label(stat[0]).classes("text-2xl")
                                    ui.label(stat[1]).classes("font-semibold text-blue-900")
                
                with ui.column().classes("w-full p-8"):
                    current_project_container = ui.column().classes("w-full mb-6")
                    
                    async def check_current_project():
                        workspace = await ui_manager.get_workspace()
                        current_project_container.clear()
                        
                        if workspace:
                            with current_project_container:
                                with ui.card().classes("w-full border-0").style("""
                                    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                                    border-left: 6px solid #10b981;
                                    border-radius: 16px;
                                    padding: 0;
                                """):
                                    with ui.row().classes("w-full items-center p-6 gap-6"):
                                        with ui.avatar(size="xl").style("""
                                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                                            box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
                                        """):
                                            ui.icon("check_circle", size="2rem", color="white")
                                        
                                        with ui.column().classes("flex-1 gap-1"):
                                            ui.label("Current Project").classes("text-sm font-semibold text-green-800 uppercase tracking-wide opacity-80")
                                            ui.label(workspace.get('name', 'Unknown')).classes("text-2xl font-bold text-green-900")
                                            ui.label(workspace.get('path', '')).classes("text-sm text-green-700 opacity-75 font-mono")
                                        
                                        ui.button("OPEN PROJECT", icon="launch").props("unelevated").classes("px-8").style("""
                                            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                                            color: white;
                                            font-weight: 700;
                                            padding: 14px 32px;
                                            border-radius: 12px;
                                            font-size: 15px;
                                            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
                                            transition: all 0.3s;
                                        """).on_click(lambda: on_project_open() if on_project_open else None)
                    
                    ui.timer(0.1, check_current_project, once=True)
                    
                    with ui.row().classes("w-full items-center gap-4 my-6"):
                        ui.separator().classes("flex-1")
                        ui.label("OR BROWSE FOR A PROJECT").classes("text-sm font-bold text-gray-400 tracking-wider")
                        ui.separator().classes("flex-1")
                    
                    create_file_browser(ui_manager, on_project_open, show_create_options=True)
            
            with ui.row().classes("w-full max-w-5xl gap-6 mt-12").style("""
                animation: fadeInUp 0.8s ease-out 0.8s both;
            """):
                features = [
                    {
                        "icon": "account_tree",
                        "title": "Visual Graphs",
                        "desc": "See your service dependencies and K8s resources",
                        "color": "#3b82f6"
                    },
                    {
                        "icon": "settings",
                        "title": "Easy Config",
                        "desc": "Customize replicas, controllers, and service types",
                        "color": "#8b5cf6"
                    },
                    {
                        "icon": "speed",
                        "title": "Instant Conversion",
                        "desc": "Generate production-ready manifests in seconds",
                        "color": "#10b981"
                    }
                ]
                
                for feature in features:
                    with ui.card().classes("flex-1 border-0 shadow-xl transition-all cursor-pointer").style(f"""
                        background: rgba(255, 255, 255, 0.9);
                        backdrop-filter: blur(10px);
                        border-radius: 20px;
                        border-top: 4px solid {feature['color']};
                        padding: 24px;
                    """).on("mouseenter", lambda e: e.sender.style.add("transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,0,0,0.15);")).on("mouseleave", lambda e: e.sender.style.remove("transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,0,0,0.15);")):
                        with ui.column().classes("items-center text-center gap-3"):
                            with ui.avatar(size="xl").style(f"background: linear-gradient(135deg, {feature['color']} 0%, {feature['color']}dd 100%);"):
                                ui.icon(feature['icon'], size="lg", color="white")
                            ui.label(feature['title']).classes("text-xl font-bold text-gray-900")
                            ui.label(feature['desc']).classes("text-gray-600 leading-relaxed")
        
        with ui.row().classes("w-full justify-center items-center gap-3 py-6").style("""
            background: rgba(30, 41, 59, 0.8);
            backdrop-filter: blur(10px);
        """):
            ui.label("Built with").classes("text-white text-sm opacity-70")
            ui.icon("favorite", size="sm").classes("text-red-400")
            ui.label("for DevOps Engineers").classes("text-white text-sm opacity-70")
    
    ui.add_head_html("""
        <style>
            @keyframes gradientShift {
                0% { background-position: 0% 50%; }
                50% { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(-20px); }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            
            @keyframes slideInDown {
                from {
                    opacity: 0;
                    transform: translateY(-40px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(40px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            @keyframes scaleIn {
                from {
                    opacity: 0;
                    transform: scale(0.9);
                }
                to {
                    opacity: 1;
                    transform: scale(1);
                }
            }
        </style>
    """)

"""Clean and organized layout improvements for Dock2K8s UI"""

# Replace the create_layout function in your ui_components_final.py with this:

def create_layout(ui_manager: UIManager):
    """Create clean, organized main UI layout"""
    
    properties_panel_ref = {"element": None}
    
    # Fixed header
    with ui.header().classes("shadow-lg").style("""
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 16px 32px;
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        z-index: 1000;
        height: 72px;
    """):
        with ui.row().classes("w-full items-center"):
            # Logo and title
            with ui.row().classes("items-center gap-3"):
                ui.icon("layers", size="2rem").classes("text-blue-400")
                ui.label("Dock2K8s").classes("text-2xl font-bold text-white")
            
            ui.space()
            
            # Workspace info and actions
            with ui.row().classes("items-center gap-4"):
                workspace_badge = ui.badge("", color="blue").classes("px-4 py-2")
                
                async def load_workspace_info():
                    workspace = await ui_manager.get_workspace()
                    if workspace:
                        workspace_badge.text = f"📁 {workspace.get('name', 'Unknown')}"
                
                ui.timer(0.1, load_workspace_info, once=True)
                
                ui.button("Change Project", icon="folder_open").props("flat").classes("text-white").style("""
                    border-radius: 8px;
                    padding: 8px 16px;
                    font-weight: 600;
                """).on_click(lambda: ui.navigate.to("/"))
    
    # Main container with fixed positioning
    with ui.row().classes("w-full").style("margin-top: 72px; height: calc(100vh - 72px);"):
        
        properties_container = ui.column().classes("w-full")
        graph_refresh_callback = {"callback": None}
        
        def update_properties_panel():
            properties_container.clear()
            with properties_container:
                create_properties_panel(ui_manager, ui_manager.selected_service, graph_refresh_callback["callback"])
                properties_panel_ref["element"] = properties_container
            
            # Smooth scroll to properties
            if properties_panel_ref["element"]:
                ui.run_javascript("""
                    setTimeout(() => {
                        const element = document.querySelector('.properties-section');
                        if (element) {
                            element.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }
                    }, 150);
                """)
        
        def on_service_select(name: str):
            ui_manager.selected_service = name
            update_properties_panel()
        
        def on_view_change(_mode: str):
            if graph_refresh_callback["callback"]:
                ui.timer(0.1, graph_refresh_callback["callback"], once=True)
        
        # Sidebar - fixed width
        create_sidebar(ui_manager, on_service_select, on_view_change)
        
        # Main content area - clean single column layout
        with ui.column().classes("flex-1 overflow-y-auto").style("""
            background: #f8fafc;
        """):
            # Container with max width for better readability
            with ui.column().classes("w-full max-w-7xl mx-auto p-6 gap-6"):
                
                # Section 1: Architecture Graph
                with ui.card().classes("w-full border-0 shadow-lg").style("border-radius: 12px;"):
                    graph_ref = create_graph_view(ui_manager)
                
                async def refresh_graph():
                    if graph_ref and graph_ref.get("render"):
                        await graph_ref["render"]()
                
                graph_refresh_callback["callback"] = refresh_graph
                
                # Section 2: Service Configuration (appears when service selected)
                with ui.column().classes("w-full properties-section"):
                    properties_container
                
                # Section 3: Action Buttons
                with ui.card().classes("w-full border-0 shadow-lg").style("border-radius: 12px;"):
                    create_action_buttons(ui_manager, refresh_graph)
                
                # Footer spacing
                ui.space().style("height: 40px;")
    
    return ui_manager


# Also update the sidebar to be cleaner:

def create_sidebar(ui_manager: UIManager, on_service_select: Callable, on_view_change: Optional[Callable] = None):
    """Create clean, organized sidebar"""
    with ui.column().classes("h-full border-r").style("""
        width: 280px;
        background: #ffffff;
        box-shadow: 2px 0 8px rgba(0,0,0,0.05);
    """):
        # Sidebar header
        with ui.row().classes("w-full items-center p-4 border-b").style("background: #f8fafc;"):
            ui.icon("dashboard", size="md").classes("text-blue-600")
            ui.label("Dashboard").classes("text-lg font-bold text-gray-800 ml-2")
        
        # Scrollable content
        with ui.column().classes("flex-1 p-4 gap-4 overflow-y-auto"):
            
            # Visualization Mode Section
            with ui.column().classes("w-full gap-2"):
                ui.label("View Mode").classes("text-xs font-bold text-gray-500 uppercase tracking-wide")
                view_toggle = ui.toggle(
                    {"compose": "Compose", "k8s": "Kubernetes"},
                    value=ui_manager.graph_mode,
                ).classes("w-full")

                def _on_toggle_change(e):
                    ui_manager.graph_mode = e.value
                    if on_view_change:
                        on_view_change(e.value)

                view_toggle.on_value_change(_on_toggle_change)
            
            ui.separator()
            
            # Project Files Section
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Project Files").classes("text-xs font-bold text-gray-500 uppercase tracking-wide")
                    refresh_button = ui.button(icon="refresh").props("flat round dense").classes("text-gray-400")
                
                file_list = ui.column().classes("w-full gap-1")
                
                async def refresh_files():
                    files = await ui_manager.fetch_files()
                    file_list.clear()
                    with file_list:
                        if not files:
                            ui.label("No files").classes("text-gray-400 text-xs p-2")
                        else:
                            for file_info in files:
                                icon = "📁" if file_info["type"] == "directory" else "📄"
                                with ui.row().classes("w-full items-center p-2 rounded-lg hover:bg-gray-50 cursor-pointer transition-colors"):
                                    ui.label(f"{icon}").classes("text-base")
                                    ui.label(file_info['name']).classes("text-sm text-gray-700 ml-2 truncate")
                
                refresh_button.on_click(lambda: ui.timer(0.1, refresh_files, once=True))
            
            ui.separator()
            
            # Services Section
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label("Services").classes("text-xs font-bold text-gray-500 uppercase tracking-wide")
                    refresh_services_button = ui.button(icon="refresh").props("flat round dense").classes("text-gray-400")
                
                services_list = ui.column().classes("w-full gap-1")
                
                async def refresh_services():
                    services_list.clear()
                    try:
                        ir = await ui_manager.fetch_ir()
                        if ir and ir.get("services"):
                            with services_list:
                                for service in ir.get("services", []):
                                    service_name = service["name"]
                                    is_selected = ui_manager.selected_service == service_name
                                    
                                    btn = ui.button(
                                        service_name,
                                        icon="settings"
                                    ).props("flat").classes(f"w-full justify-start text-left").style(f"""
                                        border-radius: 8px;
                                        padding: 10px 12px;
                                        background: {'#eff6ff' if is_selected else 'transparent'};
                                        color: {'#1e40af' if is_selected else '#374151'};
                                        border-left: 3px solid {'#3b82f6' if is_selected else 'transparent'};
                                        font-weight: {'600' if is_selected else '500'};
                                    """)
                                    btn.on_click(lambda e, name=service_name: on_service_select(name))
                        else:
                            with services_list:
                                ui.label("No services found").classes("text-gray-400 text-xs p-2")
                    except Exception as e:
                        with services_list:
                            ui.label(f"Error: {str(e)}").classes("text-red-400 text-xs p-2")
                
                refresh_services_button.on_click(lambda: ui.timer(0.1, refresh_services, once=True))
        
        # Initial load
        ui.timer(0.1, refresh_files, once=True)
        ui.timer(0.2, refresh_services, once=True)
        
        return file_list, services_list


# Update graph view for cleaner look:

def create_graph_view(ui_manager: UIManager):
    """Create clean graph visualization"""
    # Remove the outer card wrapper since we have it in layout now
    with ui.column().classes("w-full"):
        # Header
        with ui.row().classes("w-full items-center justify-between p-6 border-b").style("background: #f8fafc;"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("account_tree", size="lg").classes("text-blue-600")
                with ui.column().classes("gap-0"):
                    title_label = ui.label("Architecture Visualization").classes("text-xl font-bold text-gray-900 m-0")
                    subtitle_label = ui.label("").classes("text-sm text-gray-600 m-0")
            
            refresh_btn = ui.button("Refresh", icon="refresh").props("flat").classes("text-blue-600 font-semibold")
        
        # Content
        with ui.column().classes("p-6 gap-4"):
            status_container = ui.column().classes("w-full")
            graph_container_ref = {"container": None}
            
            async def render_graph():
                status_container.clear()
                
                try:
                    mode = ui_manager.graph_mode

                    if mode == "compose":
                        subtitle_label.text = "Docker Compose Services & Dependencies"
                        ir = await ui_manager.fetch_ir()
                        if not ir:
                            with status_container:
                                with ui.card().classes("w-full bg-orange-50 border-l-4 border-orange-400"):
                                    with ui.row().classes("items-center gap-3 p-4"):
                                        ui.icon("warning", color="orange")
                                        ui.label("No project loaded. Please select a project from the home page.").classes("text-orange-800")
                            if graph_container_ref["container"]:
                                graph_container_ref["container"].set_visibility(False)
                            return

                        services = ir.get("services", [])
                        if not services:
                            with status_container:
                                with ui.card().classes("w-full bg-gray-50 border-l-4 border-gray-300"):
                                    with ui.row().classes("items-center gap-3 p-4"):
                                        ui.icon("info", color="grey")
                                        ui.label("No services found in docker-compose.yml").classes("text-gray-600")
                            if graph_container_ref["container"]:
                                graph_container_ref["container"].set_visibility(False)
                            return

                        svg_content = generate_svg_compose_graph(services)

                    else:
                        subtitle_label.text = "Kubernetes Resources"
                        resources = await ui_manager.fetch_k8s_resources()
                        if not resources:
                            with status_container:
                                with ui.card().classes("w-full bg-blue-50 border-l-4 border-blue-400"):
                                    with ui.row().classes("items-center gap-3 p-4"):
                                        ui.icon("info", color="blue")
                                        ui.label("No manifests generated yet. Click 'Run Conversion' to create Kubernetes resources.").classes("text-blue-800")
                            if graph_container_ref["container"]:
                                graph_container_ref["container"].set_visibility(False)
                            return

                        svg_content = generate_svg_k8s_graph(resources)

                    if graph_container_ref["container"] is None:
                        graph_container_ref["container"] = ui.html("", sanitize=False).classes("w-full")
                    graph_container_ref["container"].set_visibility(True)

                    graph_container_ref["container"].content = f"""
                        <div style="
                            width: 100%;
                            min-height: 500px;
                            border: 1px solid #e5e7eb;
                            border-radius: 8px;
                            background: #ffffff;
                            overflow: auto;
                            padding: 20px;
                        ">
                            {svg_content}
                        </div>
                    """
                    graph_container_ref["container"].update()
                    
                except Exception as e:
                    with status_container:
                        with ui.card().classes("w-full bg-red-50 border-l-4 border-red-400"):
                            with ui.row().classes("items-center gap-3 p-4"):
                                ui.icon("error", color="red")
                                ui.label(f"Error: {str(e)}").classes("text-red-800")
                    if graph_container_ref["container"]:
                        graph_container_ref["container"].set_visibility(False)
            
            ui.timer(0.3, render_graph, once=True)
            refresh_btn.on_click(lambda: ui.timer(0.1, render_graph, once=True))
            graph_container_ref["render"] = render_graph
            
        return graph_container_ref


# Update properties panel for cleaner look:

def create_properties_panel(ui_manager: UIManager, selected_service: Optional[str] = None, on_save_callback: Optional[Callable] = None):
    """Create clean properties panel"""
    # Remove outer card since it's in layout
    with ui.column().classes("w-full"):
        # Header
        with ui.row().classes("w-full items-center p-6 border-b").style("background: #f8fafc;"):
            ui.icon("tune", size="lg").classes("text-purple-600")
            ui.label("Service Configuration").classes("text-xl font-bold text-gray-900 ml-3")
        
        with ui.column().classes("p-6 gap-6"):
            if not selected_service:
                with ui.column().classes("w-full items-center justify-center py-12"):
                    ui.icon("touch_app", size="3rem").classes("text-gray-300")
                    ui.label("Select a service from the sidebar").classes("text-gray-500 mt-4")
                    ui.label("Configure replicas, controllers, and service types").classes("text-gray-400 text-sm")
                return
            
            # Service badge
            with ui.row().classes("items-center gap-2 mb-2"):
                ui.badge("CONFIGURING", color="purple").classes("text-xs font-bold")
                ui.label(selected_service).classes("text-2xl font-bold text-gray-900")
            
            # Workload section
            with ui.card().classes("w-full border-l-4 border-blue-500").style("background: #eff6ff; border-radius: 8px;"):
                with ui.column().classes("p-5 gap-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("settings", color="blue")
                        ui.label("Workload Configuration").classes("text-lg font-semibold text-blue-900")
                    
                    replicas_input = ui.number(
                        label="Replicas",
                        value=1,
                        min=1,
                        max=100
                    ).classes("w-full").props("outlined dense")
                    
                    controller_select = ui.select(
                        ["Deployment", "StatefulSet"],
                        label="Controller Type",
                        value="Deployment"
                    ).classes("w-full").props("outlined dense")
            
            # Service section
            with ui.card().classes("w-full border-l-4 border-green-500").style("background: #f0fdf4; border-radius: 8px;"):
                with ui.column().classes("p-5 gap-4"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("cloud", color="green")
                        ui.label("Kubernetes Service").classes("text-lg font-semibold text-green-900")
                    
                    service_enabled = ui.checkbox("Enable Kubernetes Service", value=True).classes("text-base")
                    
                    service_type_select = ui.select(
                        ["ClusterIP", "NodePort", "LoadBalancer", "ExternalName"],
                        label="Service Type",
                        value="ClusterIP"
                    ).classes("w-full").props("outlined dense")
            
            # Load config
            async def load_service_config():
                try:
                    ir = await ui_manager.fetch_ir()
                    if not ir:
                        ui.notify("Failed to load configuration", type="warning")
                        return
                    
                    service_data = next(
                        (s for s in ir.get("services", []) if s["name"] == selected_service),
                        None
                    )
                    if service_data:
                        workload_cfg = service_data.get("workload_config", {})
                        svc_cfg = service_data.get("service_config", {})
                        defaults = ir.get("defaults", {})
                        
                        replicas_input.value = workload_cfg.get("replicas") or defaults.get("replicas") or 1
                        controller_select.value = workload_cfg.get("controller") or defaults.get("controller") or "Deployment"
                        service_enabled.value = svc_cfg.get("enabled", True)
                        service_type_select.value = svc_cfg.get("type", "ClusterIP")
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
                        await on_save_callback()
                except Exception as e:
                    ui.notify(f"Error saving config: {str(e)}", type="negative")
            
            with ui.row().classes("w-full gap-3"):
                save_btn = ui.button("Save Configuration", icon="save").props("unelevated").classes("flex-1").style("""
                    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                    color: white;
                    font-weight: 600;
                    padding: 12px;
                    border-radius: 8px;
                """)
                save_btn.on_click(lambda: ui.timer(0.1, save_config, once=True))
                
                reset_btn = ui.button("Reset", icon="refresh").props("outline").classes("text-gray-600")
                reset_btn.on_click(lambda: ui.timer(0.1, load_service_config, once=True))


# Update action buttons:

def create_action_buttons(ui_manager: UIManager, graph_refresh_callback: Optional[Callable] = None):
    """Create clean action buttons"""
    # Remove outer card since it's in layout
    with ui.column().classes("w-full"):
        # Header
        with ui.row().classes("w-full items-center p-6 border-b").style("background: #f8fafc;"):
            ui.icon("play_circle", size="lg").classes("text-blue-600")
            ui.label("Actions").classes("text-xl font-bold text-gray-900 ml-3")
        
        with ui.column().classes("p-6 gap-4"):
            with ui.row().classes("w-full gap-4"):
                # Convert button
                convert_btn = ui.button(
                    "Run Conversion",
                    icon="play_circle"
                ).props("unelevated").classes("flex-1").style("""
                    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                    color: white;
                    font-weight: 700;
                    padding: 16px;
                    border-radius: 10px;
                    font-size: 16px;
                """)
                
                async def run_convert():
                    success = await ui_manager.trigger_conversion()
                    if success and graph_refresh_callback:
                        await graph_refresh_callback()
                
                convert_btn.on_click(lambda: ui.timer(0.1, run_convert, once=True))
                
                # Preview button
                preview_btn = ui.button(
                    "Preview YAML",
                    icon="visibility"
                ).props("outline").classes("flex-1").style("""
                    border: 2px solid #3b82f6;
                    color: #3b82f6;
                    font-weight: 600;
                    padding: 16px;
                    border-radius: 10px;
                    font-size: 16px;
                """)
                
                # Preview dialog
                preview_dialog = ui.dialog()
                with preview_dialog:
                    with ui.card().classes("w-full max-w-4xl").style("border-radius: 12px;"):
                        with ui.row().classes("w-full items-center p-6 border-b").style("background: #f8fafc;"):
                            ui.icon("code", size="lg").classes("text-indigo-600")
                            ui.label("YAML Preview").classes("text-xl font-bold text-gray-900 ml-3")
                        
                        with ui.column().classes("p-6"):
                            preview_content = ui.code().classes("w-full").style("max-height: 500px; overflow-y: auto;")
                            
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
                            
                            with ui.row().classes("w-full justify-end mt-4 gap-2"):
                                ui.button("Close", on_click=preview_dialog.close).props("flat")
            
            # Info text
            ui.label("Convert your Docker Compose project to Kubernetes manifests").classes("text-sm text-gray-600 text-center")