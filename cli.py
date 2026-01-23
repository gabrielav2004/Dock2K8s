import argparse
from pathlib import Path
from project import find_project_root
from convert import convert
from config import merge_configs

def main():
    parser = argparse.ArgumentParser(
        description="Convert Docker Compose to Kubernetes manifests"
    )
    parser.add_argument(
        "-p", "--project-dir", default=".",
        help="Project directory (default: current)"
    )
    parser.add_argument(
        "-c", "--config", default="config.yml",
        help="Config file path (default: config.yml)"
    )
    parser.add_argument(
        "-f", "--file", dest="docker_compose_file", default=None,
        help="Docker Compose file name (default: docker-compose.yml)"
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Output directory for K8s manifests (overrides config)"
    )
    parser.add_argument(
        "--docker-compose", dest="docker_compose_file_alt", default=None,
        help="Docker Compose file name (alias for -f/--file)"
    )
    parser.add_argument(
        "--dock2k8s-config", default=None,
        help="Dock2K8s config file name (default: dock2k8s.yaml)"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--format", choices=["yaml", "json"], default=None,
        help="Output format (default: yaml)"
    )
    parser.add_argument(
        "--replicas", type=int, default=None,
        help="Default replicas for all services (overrides config)"
    )
    parser.add_argument(
        "--service-type", default=None,
        help="Default Kubernetes service type (default: ClusterIP)"
    )
    parser.add_argument(
        "--convert-volumes", action="store_true", default=None,
        help="Convert Docker volumes to PersistentVolumeClaims"
    )
    parser.add_argument(
        "--pvc-size", default=None,
        help="Default PVC size for converted volumes (default: 10Gi)"
    )
    parser.add_argument(
        "--no-depends-on", action="store_true",
        help="Don't handle depends_on relationships"
    )
    
    args = parser.parse_args()
    
    # Find project root
    root = find_project_root(args.project_dir)
    
    # Load config file
    config_path = root / args.config if args.config else None
    
    # Handle -f/--file and --docker-compose (use -f if both provided)
    docker_compose_file = args.docker_compose_file or args.docker_compose_file_alt
    
    # Prepare CLI args for merging (only include non-None values)
    cli_args = {
        "output_dir": args.output_dir,
        "docker_compose_file": docker_compose_file,
        "config_file": args.dock2k8s_config,
        "verbose": args.verbose if args.verbose else None,
        "format": args.format,
        "default_replicas": args.replicas,
        "default_service_type": args.service_type,
        "convert_volumes": args.convert_volumes if args.convert_volumes is not None else None,
        "pvc_size": args.pvc_size,
        "handle_depends_on": False if args.no_depends_on else None,
    }
    
    # Merge configs: CLI > config file > defaults
    config = merge_configs(cli_args, config_path)
    
    # Run conversion
    convert(root, config)

if __name__ == "__main__":
    main()
