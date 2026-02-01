import argparse
import sys
from pathlib import Path

from project import find_project_root
from convert import convert
from config import merge_configs
from tui_compose import ComposeVisualizer
from tui_k8s import K8sVisualizer


# -----------------------------
# Visualize Command Handler
# -----------------------------
def cmd_visualize(args):
    try:
        # Resolve project root (best-effort)
        try:
            root = find_project_root(args.project_dir)
        except FileNotFoundError:
            root = Path.cwd()

        # -------------------------
        # K8s Visualization (POST)
        # -------------------------
        if args.mode == "k8s":
            output_dir = args.output_dir or "k8s"
            if not Path(output_dir).is_absolute():
                output_dir = str(root / output_dir)

            visualizer = K8sVisualizer(output_dir)
            visualizer.load_resources()
            visualizer.display_architecture(auto_exit=True)
            return

        # -------------------------
        # Compose Visualization (PRE)
        # -------------------------
        if args.mode == "compose":
            compose_file = args.file
            if compose_file and not Path(compose_file).is_absolute():
                compose_file = str(root / compose_file)

            visualizer = ComposeVisualizer(compose_file)
            visualizer.display_architecture()
            return

    except Exception as e:
        print(f"Error during visualization: {str(e)}", file=sys.stderr)
        sys.exit(1)


# -----------------------------
# Main CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Dock2K8s – Docker Compose to Kubernetes Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest="command")

    # =========================
    # Convert Command
    # =========================
    convert_parser = subparsers.add_parser("convert", help="Convert Docker Compose to Kubernetes")
    convert_parser.add_argument("-p", "--project-dir", default=".")
    convert_parser.add_argument("-c", "--config", default="config.yml")
    convert_parser.add_argument("-f", "--file", dest="docker_compose_file", default=None)
    convert_parser.add_argument("-o", "--output-dir", default=None)
    convert_parser.add_argument("--docker-compose", dest="docker_compose_file_alt", default=None)
    convert_parser.add_argument("--dock2k8s-config", default=None)
    convert_parser.add_argument("-v", "--verbose", action="store_true")
    convert_parser.add_argument("--visualize", action="store_true")
    convert_parser.add_argument("--format", choices=["yaml", "json"], default=None)
    convert_parser.add_argument("--replicas", type=int, default=None)
    convert_parser.add_argument("--service-type", default=None)
    convert_parser.add_argument("--convert-volumes", action="store_true", default=None)
    convert_parser.add_argument("--pvc-size", default=None)
    convert_parser.add_argument("--no-depends-on", action="store_true")

    # =========================
    # Visualize Command
    # =========================
    visualize_parser = subparsers.add_parser(
        "visualize",
        help="Visualize architecture (pre or post conversion)"
    )
    visualize_parser.add_argument(
        "mode",
        choices=["k8s", "compose"],
        help="Visualization mode"
    )
    visualize_parser.add_argument(
        "-p", "--project-dir",
        default=".",
        help="Project directory (default: current)"
    )
    visualize_parser.add_argument(
        "-o", "--output-dir",
        default="k8s",
        help="K8s manifest directory (k8s mode only)"
    )
    visualize_parser.add_argument(
        "-f", "--file",
        help="Docker Compose file (compose mode only)"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # -------------------------
    # Visualize
    # -------------------------
    if args.command == "visualize":
        cmd_visualize(args)
        return

    # -------------------------
    # Convert
    # -------------------------
    if args.command == "convert":
        root = find_project_root(args.project_dir)
        config_path = root / args.config if args.config else None

        docker_compose_file = args.docker_compose_file or args.docker_compose_file_alt

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

        config = merge_configs(cli_args, config_path)
        convert(root, config)

        if args.visualize:
            output_dir = config.get("output_dir", "k8s")
            if not Path(output_dir).is_absolute():
                output_dir = str(root / output_dir)

            visualizer = K8sVisualizer(output_dir)
            visualizer.load_resources()
            visualizer.display_architecture(auto_exit=True)


if __name__ == "__main__":
    main()
