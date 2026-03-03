"""
Phase S — Security: Encryption & Credential Management
security.py — Centralized security utilities for Finsang V2.0

Responsibilities:
  - Parquet encryption/decryption via Fernet symmetric key
  - Centralized Supabase client factory (single source of truth)
  - Environment security audit (detect leaked credentials)
"""

import os
import subprocess
from pathlib import Path
from cryptography.fernet import Fernet


# ─── Fernet Symmetric Encryption ─────────────────────────────────────────────

def get_cipher() -> Fernet | None:
    """Returns a Fernet cipher using FINSANG_ENCRYPTION_KEY, or None if not set."""
    key = os.getenv("FINSANG_ENCRYPTION_KEY")
    if not key:
        return None
    return Fernet(key.encode("utf-8"))


def generate_key() -> str:
    """Generates a new base64url-encoded Fernet key."""
    return Fernet.generate_key().decode("utf-8")


def add_key_to_env(env_path: str):
    """Generates a Fernet key and appends it to the .env file if not present."""
    key = generate_key()
    with open(env_path, "a") as f:
        f.write(f"\nFINSANG_ENCRYPTION_KEY={key}\n")
    print(f"🔑 Generated new encryption key and saved to {env_path}")
    return key


# ─── Centralized Supabase Client Factory ─────────────────────────────────────

def get_supabase_client():
    """
    Returns an authenticated Supabase client.
    Single source of truth — avoids duplicating credential-loading logic
    across pipeline.py, sync_supabase.py, metrics.py, etc.

    Raises:
        RuntimeError: if SUPABASE_URL or SUPABASE_KEY are missing.
        ImportError:  if supabase-py is not installed.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "❌ SUPABASE_URL / SUPABASE_KEY not found in environment.\n"
            "   Check your .env file or OS environment variables."
        )
    try:
        from supabase import create_client
    except ImportError:
        raise ImportError("supabase-py not installed. Run: pip install supabase")

    return create_client(url, key)


# ─── Environment Security Audit ──────────────────────────────────────────────

def audit_env_security(project_root: Path | None = None) -> list[str]:
    """
    Scans for common security misconfigurations and returns a list of warnings.

    Checks:
      1. SUPABASE_KEY / FINSANG_ENCRYPTION_KEY present in env (good)
      2. .env file is NOT tracked by git (critical check)
      3. .gitignore contains .env entry

    Returns:
        List of warning strings. Empty list = all clear.
    """
    warnings: list[str] = []
    root = project_root or Path(__file__).parent.parent.parent
    env_file = root / ".env"
    gitignore = root / ".gitignore"

    # Check 1: Required secrets present
    for key_name in ("SUPABASE_URL", "SUPABASE_KEY", "FINSANG_ENCRYPTION_KEY"):
        if not os.getenv(key_name):
            warnings.append(f"⚠️  {key_name} is not set in environment")

    # Check 2: .env is NOT git-tracked (most critical)
    if env_file.exists():
        try:
            result = subprocess.run(
                ["git", "ls-files", "--error-unmatch", str(env_file)],
                capture_output=True, text=True, cwd=str(root)
            )
            if result.returncode == 0:
                warnings.append(
                    "🚨 CRITICAL: .env is tracked by git! Run: git rm --cached .env"
                )
        except FileNotFoundError:
            pass  # git not available, skip check

    # Check 3: .gitignore has .env entry
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if ".env" not in content:
            warnings.append("⚠️  .gitignore does not contain .env — secrets may be committed")
    else:
        warnings.append("⚠️  No .gitignore found at project root")

    return warnings


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from pathlib import Path

    print("\n🔐 Finsang Security Check")
    print("─" * 40)

    # Run audit
    issues = audit_env_security()
    if issues:
        for w in issues:
            print(f"  {w}")
    else:
        print("  ✅ No security issues detected.")

    print()

    # Key management
    env_file = Path(__file__).parent.parent / ".env"
    if get_cipher() is None:
        add_key_to_env(str(env_file))
    else:
        print("  ✅ FINSANG_ENCRYPTION_KEY is set.")
    print()

