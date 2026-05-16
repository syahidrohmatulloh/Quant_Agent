
import os
from functools import wraps
from fastapi import HTTPException, Header

ROLES = {"viewer": os.getenv("QUANT_VIEWER_TOKEN", ""),
         "operator": os.getenv("QUANT_OPERATOR_TOKEN", ""),
         "admin": os.getenv("QUANT_ADMIN_TOKEN", "")}

def get_role(token: str) -> str:
    for role, env_token in ROLES.items():
        if env_token and token == env_token:
            return role
    raise HTTPException(status_code=401, detail="Invalid token")

def require_role(*roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, token: str = Header(...), **kwargs):
            role = get_role(token)
            if role not in roles:
                raise HTTPException(status_code=403, detail="Forbidden")
            return await func(*args, role=role, **kwargs)
        return wrapper
    return decorator
