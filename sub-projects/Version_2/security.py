import os
from cryptography.fernet import Fernet

def get_cipher() -> Fernet | None:
    """Returns a Fernet cipher using FINSANG_ENCRYPTION_KEY, or None if not set."""
    key = os.getenv("FINSANG_ENCRYPTION_KEY")
    if not key:
        return None
    return Fernet(key.encode('utf-8'))

def generate_key() -> str:
    """Generates a new base64url-encoded string key."""
    return Fernet.generate_key().decode('utf-8')

def add_key_to_env(env_path: str):
    """Generates a key and appends it to the .env file if it doesn't exist."""
    key = generate_key()
    with open(env_path, "a") as f:
        f.write(f"\nFINSANG_ENCRYPTION_KEY={key}\n")
    print(f"🔑 Generated new encryption key and saved to {env_path}")
    return key

if __name__ == "__main__":
    import sys
    from pathlib import Path
    env_file = Path(__file__).parent.parent / ".env"
    if get_cipher() is None:
        add_key_to_env(str(env_file))
    else:
        print("✅ FINSANG_ENCRYPTION_KEY already exists in environment.")
