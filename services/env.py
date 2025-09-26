import os
from pathlib import Path
import json

DATA_DIR = Path(__file__).parent.parent.parent / "data"
ADMINS_FILE = DATA_DIR / "admins.json"

def get_bot_token():
    return os.getenv("BOT_TOKEN")

def load_admins():
    if not ADMINS_FILE.exists():
        return []
    with open(ADMINS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_admins(admin_list):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admin_list, f, ensure_ascii=False, indent=2)

def get_admins():
    env = os.getenv("ADMINS")
    env_admins = []
    if env:
        env_admins = [int(x) for x in env.replace(';', ',').split(",") if x.strip().isdigit()]
    file_admins = load_admins()
    combined = set(env_admins) | set(file_admins)
    return list(combined)

def ensure_admins_in_db():
    env_admins = set(get_admins())
    current_admins = set(load_admins())
    to_add = env_admins - current_admins
    if to_add:
        combined = list(current_admins | to_add)
        save_admins(combined)
