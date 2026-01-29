# Dock2K8s UI

Browser-based UI for visualizing and editing Docker Compose to Kubernetes conversions.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run UI
python run_ui.py
# Opens at http://127.0.0.1:8000/
```

## Features

- **Jupyter-Style File Browser**: Browse filesystem and discover projects
- **Project Detection**: Folders with `docker-compose.yml` are highlighted as projects
- **Dual Graph Views**: Toggle between Compose (services + dependencies) and K8s (generated resources)
- **Properties Panel**: Edit service configurations
- **Live Preview**: Preview generated YAML before conversion
- **One-Click Conversion**: Generate Kubernetes manifests

## Usage

### 1. Select a Project

When you open the UI, you'll see the **Project Browser** (Jupyter-style):

- Browse your filesystem using the file tree
- Folders containing `docker-compose.yml` are highlighted in green with a "Project" badge
- Click **"Open"** on a project folder to work with it
- Use navigation buttons: Home, Up, Refresh

### 2. Work with Your Project

Once a project is open, you'll see the main UI with:

- **Sidebar**: Toggle between Compose/K8s views, list services
- **Graph View**: Visualize service relationships
- **Properties Panel**: Edit service configurations
- **Action Buttons**: Convert, Preview YAML

### 3. Switch Projects

- Click **"Change Project"** in the header to return to the file browser
- Select a different project folder

## Graph Views

### Compose View
- **Nodes**: Services from `docker-compose.yml`
- **Colors**: Green = has K8s Service, Orange = workload only
- **Edges**: `depends_on` relationships
- **Info**: Controller type, replica count

### K8s View
- **Nodes**: Generated Kubernetes resources (Services, Deployments, StatefulSets)
- **Colors**: Blue = Service, Green = Deployment, Purple = StatefulSet
- **Edges**: Service → Workload (via `selector.app`)
- **Info**: Resource kind, source file

## API Endpoints

**File Browser:**
- `GET /api/browse?path=...` - Browse directory contents
- `GET /api/browse/parent?path=...` - Get parent directory
- `GET /api/browse/home` - Get home directory path
- `GET /api/workspace` - Get current workspace info
- `POST /api/workspace?path=...` - Set current workspace

**Project Data:**
- `GET /api/ir` - Get intermediate representation
- `GET /api/project` - Get project files
- `GET /api/k8s/resources` - Get parsed K8s resources
- `PUT /api/config` - Update config.yml
- `POST /api/convert` - Trigger conversion
- `GET /api/preview/{service_name}` - Preview generated YAML

## Project Structure

```
ui/
├── app.py           # FastAPI + NiceGUI entry point
├── api.py           # REST API endpoints
├── components.py    # UI components (sidebar, graphs, panels)
└── models.py        # Pydantic data models
```

## Requirements

- Python 3.8+
- FastAPI, NiceGUI, httpx, pydantic
- Existing Dock2K8s project with `docker-compose.yml`

## Troubleshooting

**"No project found"**
- Ensure you're in a directory with `docker-compose.yml`

**"No services found"**
- Check that `docker-compose.yml` has a `services` section

**K8s view empty**
- Run conversion first to generate manifests in `output_dir`

**Graph not updating**
- Click "Refresh Graph" button
- Check browser console for errors
