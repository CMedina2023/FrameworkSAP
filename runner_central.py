"""Orquestador Maestro de Automatización SAP GUI."""
import argparse
import subprocess
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Orquestador Maestro de Automatización SAP GUI")
    parser.add_argument(
        "--suite",
        choices=["EWM", "all"],
        default="EWM",
        help="Suite a ejecutar (ej. EWM o all)."
    )
    parser.add_argument(
        "--tag",
        type=str,
        default=None,
        help="Filtrar por etiqueta de Gherkin o marcador de pytest (ej. smoke, arribo, cortina, chocolate, PC-534)."
    )
    args = parser.parse_args()

    root_dir = os.path.dirname(os.path.abspath(__file__))
    reports_dir = os.path.join(root_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    tests_dir = os.path.join(root_dir, "tests", "bdd")
    app_dir = os.path.join(root_dir, "apps", "ewm")

    report_name = f"report_SAP_{args.suite}.html"
    report_path = os.path.join(reports_dir, report_name)

    print(f"\n==============================================")
    print(f">> INICIANDO EJECUCIÓN BDD SAP: {args.suite.upper()} <<")
    if args.tag:
        print(f">> FILTRANDO POR TAG/MARCADOR: @{args.tag} <<")
    print(f"==============================================")

    env = os.environ.copy()
    env["PYTHONPATH"] = f"{root_dir}{os.pathsep}{app_dir}"
    env["ENV_FILE"] = os.path.join(root_dir, ".env")

    cmd = [
        sys.executable, "-m", "pytest",
        tests_dir,
        f"--html={report_path}",
        "--self-contained-html",
        "-v"
    ]

    if args.tag:
        cmd.extend(["-m", args.tag])

    subprocess.run(cmd, env=env, cwd=root_dir)


if __name__ == "__main__":
    main()
