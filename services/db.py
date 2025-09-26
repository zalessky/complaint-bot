import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

COMPLAINTS_FILE = DATA_DIR / "complaints.json"
ADMINS_FILE = DATA_DIR / "admins.json"

def load_complaints():
    if not COMPLAINTS_FILE.exists():
        return []
    with open(COMPLAINTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_complaints(comps):
    with open(COMPLAINTS_FILE, "w", encoding="utf-8") as f:
        json.dump(comps, f, ensure_ascii=False, indent=2)

def get_all_complaints():
    return load_complaints()

def list_complaints(status=None):
    comps = load_complaints()
    if status is None:
        return comps
    return [c for c in comps if c["status"] == status]

def change_complaint_status(complaint_id, new_status, admin_id=None):
    comps = load_complaints()
    for c in comps:
        if c["id"] == complaint_id:
            c["status"] = new_status
            c["admin_id"] = admin_id
            c["status_updated"] = datetime.now().isoformat(" ", "seconds")
            save_complaints(comps)
            return True
    return False

def export_complaints_csv():
    comps = load_complaints()
    rows = [["ID", "Дата", "Категория", "Автор", "Статус", "Обновлено", "Описание"]]
    for c in comps:
        rows.append([
            c.get("id", ""),
            c.get("created", ""),
            c.get("category", ""),
            c.get("user_id", ""),
            c.get("status", ""),
            c.get("status_updated", ""),
            c.get("description", "").replace("\n", " ").replace(",", ";")
        ])
    out = "\ufeff" + "\n".join(",".join(map(str, row)) for row in rows) + "\n"
    return out.encode("utf-8")

def load_admins():
    if not ADMINS_FILE.exists():
        return []
    with open(ADMINS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_admins(admin_list):
    ADMINS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admin_list, f, ensure_ascii=False, indent=2)

def ensure_admins_in_db():
    from services.env import get_admins
    env_admins = set(get_admins())
    current_admins = set(load_admins())
    to_add = env_admins - current_admins
    if to_add:
        combined = list(current_admins | to_add)
        save_admins(combined)
