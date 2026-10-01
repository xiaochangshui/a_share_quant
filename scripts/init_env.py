"""Create the project's Python environment on Linux or Windows."""

import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
ENV = ROOT / ".venv"


def main():
    if sys.version_info < (3, 10):
        print("ERROR: Python 3.10 or newer is required.", file=sys.stderr)
        return 1

    python = ENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    try:
        if ENV.exists():
            if not (ENV / "pyvenv.cfg").is_file() or not python.is_file():
                print(
                    "ERROR: .venv exists but is not a usable environment for this OS.\n"
                    "Rename it to keep a backup, then run this script again.",
                    file=sys.stderr,
                )
                return 1
            print("Reusing environment: " + str(ENV), flush=True)
        else:
            print("Creating environment: " + str(ENV), flush=True)
            subprocess.run([sys.executable, "-m", "venv", str(ENV)], check=True)

        subprocess.run(
            [str(python), "-m", "pip", "install", "-r", str(ROOT / "requirements.txt")],
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--editable",
                str(ROOT),
                "--no-deps",
                "--no-build-isolation",
            ],
            check=True,
        )
        subprocess.run(
            [
                str(python),
                "-c",
                "import a_share_quant; import pandas as pd; "
                "print('Pandas:', pd.__version__); "
                "print('a_share_quant:', a_share_quant.__version__)",
            ],
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as error:
        print("ERROR: Initialization failed: " + str(error), file=sys.stderr)
        print(
            "Check the Python installation, venv/pip support and network access, "
            "then rerun the script. On Debian/Ubuntu, missing venv support "
            "can usually be installed with: sudo apt install python3-venv",
            file=sys.stderr,
        )
        return 1

    print("Environment ready.")
    print("From the project root, activate it with:")
    if os.name == "nt":
        print(r"  PowerShell: .\.venv\Scripts\Activate.ps1")
        print(r"  cmd: .venv\Scripts\activate.bat")
        print(r'No activation needed: .\.venv\Scripts\python.exe -c "import pandas; print(pandas.__version__)"')
    else:
        print("  source .venv/bin/activate")
        print('No activation needed: .venv/bin/python -c "import pandas; print(pandas.__version__)"')
    return 0


if __name__ == "__main__":
    sys.exit(main())
