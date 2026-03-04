import sys, os
from pathlib import Path
print("Starting debug_imports.py...", flush=True)

ROOT = Path(__file__).parent.parent.parent
v2_path = ROOT / "sub-projects" / "Version_2"
sys.path.insert(0, str(v2_path))

print("Importing os, pd, math...", flush=True)
import pandas as pd
import math

print("Importing dotenv...", flush=True)
from dotenv import load_dotenv
load_dotenv(dotenv_path=ROOT / "frontend" / ".env")

print("Importing supabase...", flush=True)
from supabase import create_client

print("Importing sector...", flush=True)
import sector

print("Importing security...", flush=True)
import security

print("Importing pipeline...", flush=True)
import pipeline

print("Importing metrics...", flush=True)
import metrics

print("All imports successful!", flush=True)
