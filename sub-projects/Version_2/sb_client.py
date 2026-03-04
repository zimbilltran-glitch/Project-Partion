import os
from supabase import create_client

_CLIENT = None

def get_sb():
    global _CLIENT
    if _CLIENT is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
             # Fallback to VITE_ prefixes if regular ones aren't set
             url = os.getenv("VITE_SUPABASE_URL")
             key = os.getenv("VITE_SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL/KEY not found in environment.")
            
        _CLIENT = create_client(url, key)
    return _CLIENT
