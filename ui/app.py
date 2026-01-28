"""Main FastAPI + NiceGUI application entry point"""
import sys
from pathlib import Path

# Add parent directory to path for imports when run directly
# This must happen before any other imports
_parent_dir = Path(__file__).parent.parent
if str(_parent_dir) not in sys.path:
    sys.path.insert(0, str(_parent_dir))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from nicegui import app, ui

# Import UI modules - try absolute first (when run directly), then relative (when run as module)
try:
    from ui.api import router as api_router
    from ui.components import UIManager, create_layout
except ImportError:
    try:
        from .api import router as api_router
        from .components import UIManager, create_layout
    except ImportError as e:
        raise ImportError(
            f"Failed to import UI modules. Make sure you're running from project root. Error: {e}"
        )


def init_ui(fastapi_app: FastAPI):
    """Initialize NiceGUI UI and mount it to FastAPI app"""
    @ui.page("/")
    async def main_page():
        """Main UI page"""
        ui_manager = UIManager()
        create_layout(ui_manager)
    
    # Mount NiceGUI to FastAPI app
    ui.run_with(
        fastapi_app,
        mount_path="/",  # Mount at root
        storage_secret="dock2k8s-ui-secret-change-in-production",
    )


def create_app() -> FastAPI:
    """Create and configure FastAPI app"""
    fastapi_app = FastAPI(
        title="Dock2K8s UI",
        description="Web UI for Dock2K8s - Docker Compose to Kubernetes converter",
        version="0.1.0"
    )
    
    # Add CORS middleware
    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount API router
    fastapi_app.include_router(api_router)
    
    # Initialize and mount NiceGUI UI
    init_ui(fastapi_app)
    
    return fastapi_app


def run(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Run the application"""
    fastapi_app = create_app()
    
    print(f"""
    🚀 Dock2K8s UI starting...
    
    📍 Local:   http://{host}:{port}/
    📍 Network: http://0.0.0.0:{port}/
    
    Press CTRL+C to stop
    """)
    
    uvicorn.run(
        fastapi_app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    run()
