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

- **Dual Graph Views**: Toggle between Compose (services + dependencies) and K8s (generated resources)
- **Project Explorer**: Browse files and services
- **Properties Panel**: Edit service configurations
- **Live Preview**: Preview generated YAML before conversion
- **One-Click Conversion**: Generate Kubernetes manifests

## Usage

1. **Navigate to project** - UI auto-detects project root (looks for `docker-compose.yml`)

2. **Select view mode** - Use sidebar toggle:
   - **Compose**: Shows services from `docker-compose.yml` with `depends_on` relationships
   - **K8s**: Shows generated Kubernetes resources (requires conversion first)

3. **Edit configuration**:
   - Click a service in sidebar
   - Edit workload settings (replicas, controller type)
   - Edit Kubernetes Service settings (enabled, type)
   - Click "Save Configuration" to update `config.yml`

4. **Convert**:
   - Click "Preview YAML" to see generated manifests
   - Click "Run Conversion" to generate Kubernetes manifests

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
