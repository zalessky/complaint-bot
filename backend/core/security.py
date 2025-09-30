import hmac
import hashlib
import json
from urllib.parse import parse_qs
from fastapi import HTTPException

def validate_telegram_webapp_data(init_data: str, bot_token: str) -> dict:
    try:
        parsed = parse_qs(init_data)
        received_hash = parsed.get('hash', [None])[0]
        if not received_hash:
            raise HTTPException(status_code=401, detail="Missing hash")
        
        data_parts = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                data_parts.append(f"{key}={parsed[key][0]}")
        
        data_string = '\n'.join(data_parts)
        secret = hmac.new("WebAppData".encode(), bot_token.encode(), hashlib.sha256).digest()
        calc_hash = hmac.new(secret, data_string.encode(), hashlib.sha256).hexdigest()
        
        if not hmac.compare_digest(calc_hash, received_hash):
            raise HTTPException(status_code=401, detail="Invalid hash")
        
        user_data = json.loads(parsed.get('user', ['{}'])[0])
        return {'user_id': user_data.get('id'), 'user_data': user_data}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

def get_current_user_id(init_data: str, bot_token: str) -> int:
    validated = validate_telegram_webapp_data(init_data, bot_token)
    return int(validated['user_id'])
