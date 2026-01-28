# Dock2K8s UI

A browser-based UI for visualizing and editing Docker Compose to Kubernetes conversion configurations.

## Features

- **Project Explorer**: Browse project files and services
- **Service Graph**: Visual representation of Kubernetes service structure and dependencies
- **Properties Panel**: Edit service configurations (replicas, controller type, service settings)
- **Conversion**: Trigger conversion and view generated manifests
- **YAML Preview**: Preview generated Kubernetes YAML before conversion

## Installation

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the UI

From the project root directory, use one of these methods:

**Recommended:**
```bash
python run_ui.py
```

**Alternative methods:**
```bash
python -m ui.app
```

Or:
```bash
python ui/app.py
```

The UI will start on `http://127.0.0.1:8000/`

## Usage

1. **Navigate to a Dock2K8s project** - The UI will automatically detect the project root (looks for `docker-compose.yml`)

2. **View Services** - The sidebar shows all services from your `docker-compose.yml`

3. **Visualize Structure** - The main graph view shows:
   - Service nodes (green = has Kubernetes Service, orange = workload only)
   - Dependencies (arrows showing `depends_on` relationships)
   - Controller types and replica counts

4. **Edit Configuration**:
   - Click a service in the sidebar
   - Edit workload settings (replicas, controller type)
   - Edit Kubernetes Service settings (enabled, type)
   - Click "Save Configuration" to update `config.yml`

5. **Preview & Convert**:
   - Click "Preview YAML" to see generated manifests for selected service
   - Click "Run Conversion" to generate Kubernetes manifests

## API Endpoints

The UI uses REST API endpoints:

- `GET /api/ir` - Get intermediate representation
- `GET /api/project` - Get project files
- `PUT /api/config` - Update config.yml
- `POST /api/convert` - Trigger conversion
- `GET /api/preview/{service_name}` - Preview generated YAML

## Project Structure

```
ui/
├── __init__.py      # Package init
├── app.py           # FastAPI + NiceGUI main app
├── api.py           # REST API endpoints
├── components.py    # NiceGUI UI components
└── models.py        # Pydantic data models
```

## Requirements

- Python 3.8+
- FastAPI
- NiceGUI
- Existing Dock2K8s project with `docker-compose.yml`
