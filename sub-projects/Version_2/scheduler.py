"""
Phase T — Trigger: Windows Scheduler Wrapper
scheduler.py — Register/remove Finsang pipeline as a Windows scheduled task

Usage:
  python Version_2/scheduler.py install          # Register daily task at 06:00
  python Version_2/scheduler.py install --time 08:30
  python Version_2/scheduler.py remove           # Unregister task
  python Version_2/scheduler.py status           # Check if task is registered
  python Version_2/scheduler.py run-now          # Trigger task immediately via schtasks

Requirements:
  - Must be run as Administrator (for schtasks /Create)
  - Only works on Windows

Design:
  Uses Windows schtasks.exe (built-in) — no external dependencies.
  Task name: "Finsang_DailyPipeline"
  Action: runs run_all.py for all FINSANG_TICKERS from .env
"""

import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).parent.parent
VENV_PY     = ROOT / ".venv" / "Scripts" / "python.exe"
RUN_ALL     = ROOT / "Version_2" / "run_all.py"
TASK_NAME   = "Finsang_DailyPipeline"
LOG_FILE    = ROOT / "Version_2" / "scheduler.log"

def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+07:00")
    line = f"{ts} | {msg}"
    print(f"  {line}")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

# ─── Install ──────────────────────────────────────────────────────────────────
def install(run_time: str = "06:00"):
    """Register the Finsang pipeline as a daily Windows scheduled task."""
    if not VENV_PY.exists():
        print(f"  ❌ Virtual env not found: {VENV_PY}")
        sys.exit(1)

    cmd = [
        "schtasks", "/Create",
        "/F",                                          # Force: overwrite if exists
        "/TN", TASK_NAME,
        "/TR", f'"{VENV_PY}" "{RUN_ALL}"',
        "/SC", "DAILY",
        "/ST", run_time,
        "/RL", "HIGHEST",                              # Run with highest privileges
        "/RU", "SYSTEM",                               # Run as SYSTEM account
    ]

    print(f"\n  📅 Installing scheduled task: {TASK_NAME}")
    print(f"  ⏰ Runs daily at {run_time}")
    print(f"  📂 Script: {RUN_ALL}")
    print(f"  🐍 Python: {VENV_PY}\n")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            _log(f"INSTALL | Task '{TASK_NAME}' registered | Daily @{run_time} | SUCCESS")
            print(f"  ✅ Task registered successfully!")
        else:
            _log(f"INSTALL | Task '{TASK_NAME}' registration FAILED | {result.stderr.strip()}")
            print(f"  ❌ schtasks error:\n{result.stderr}")
            print("  💡 Tip: Run as Administrator for schtasks /Create")
    except FileNotFoundError:
        print("  ❌ schtasks.exe not found — only works on Windows")

# ─── Remove ───────────────────────────────────────────────────────────────────
def remove():
    """Unregister the scheduled task."""
    cmd = ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            _log(f"REMOVE  | Task '{TASK_NAME}' deleted | SUCCESS")
            print(f"  ✅ Task '{TASK_NAME}' removed.")
        else:
            _log(f"REMOVE  | Task '{TASK_NAME}' delete FAILED | {result.stderr.strip()}")
            print(f"  ❌ Could not remove: {result.stderr.strip()}")
    except FileNotFoundError:
        print("  ❌ schtasks.exe not found — only works on Windows")

# ─── Status ───────────────────────────────────────────────────────────────────
def status():
    """Check if the scheduled task exists and show its next run time."""
    cmd = ["schtasks", "/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            # Extract key lines
            for line in result.stdout.splitlines():
                if any(k in line for k in ("Task Name", "Next Run", "Status", "Run As")):
                    print(f"  {line.strip()}")
        else:
            print(f"  ℹ️  Task '{TASK_NAME}' is NOT registered.")
    except FileNotFoundError:
        print("  ❌ schtasks.exe not found — only works on Windows")

# ─── Run Now ──────────────────────────────────────────────────────────────────
def run_now():
    """Trigger the scheduled task immediately."""
    cmd = ["schtasks", "/Run", "/TN", TASK_NAME]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            _log(f"RUN_NOW | Manual trigger '{TASK_NAME}' | SUCCESS")
            print(f"  ✅ Task '{TASK_NAME}' triggered.")
        else:
            print(f"  ❌ {result.stderr.strip()}")
    except FileNotFoundError:
        print("  ❌ schtasks.exe not found — only works on Windows")

# ─── CLI ──────────────────────────────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(description="Finsang V2.0 — Windows Scheduler")
    sub = parser.add_subparsers(dest="command", required=True)

    p_install = sub.add_parser("install", help="Register daily scheduled task")
    p_install.add_argument("--time", default="06:00",
                           help="Run time in HH:MM 24h format (default: 06:00)")

    sub.add_parser("remove",  help="Unregister scheduled task")
    sub.add_parser("status",  help="Show task registration status")
    sub.add_parser("run-now", help="Trigger task immediately")
    return parser.parse_args()

def main():
    print(f"\n{'━'*55}")
    print(f"  🦁 FINSANG V2.0 — Windows Scheduler")
    print(f"  Task: {TASK_NAME}")
    print(f"{'━'*55}")

    args = parse_args()
    if args.command == "install":
        install(args.time)
    elif args.command == "remove":
        remove()
    elif args.command == "status":
        status()
    elif args.command == "run-now":
        run_now()

if __name__ == "__main__":
    main()
