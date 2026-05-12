import os
import jwt
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from .db import db
from .utils import new_id, now_iso, serialize_doc

SECRET_KEY = os.environ.get('JWT_SECRET', 'smifs-edc-secret-key-change-in-production')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/auth/login', auto_error=False)


def hash_password(p: str) -> str:
    return pwd_context.hash(p)


def verify_password(p: str, hp: str) -> bool:
    try:
        return pwd_context.verify(p, hp)
    except Exception:
        return False


def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({'exp': expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get('sub')
        if not username:
            return None
        user = await db.users.find_one({'username': username}, {'_id': 0, 'password_hash': 0})
        return serialize_doc(user)
    except jwt.PyJWTError:
        return None


async def require_user(user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    return user


async def require_admin(user: Dict[str, Any] = Depends(require_user)) -> Dict[str, Any]:
    if not user.get('is_admin'):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Admin required')
    return user


async def init_admin_user():
    """Create default admin user if no users exist."""
    count = await db.users.count_documents({})
    if count == 0:
        admin = {
            'id': new_id(),
            'username': 'admin',
            'email': 'admin@smifs.local',
            'first_name': 'System',
            'last_name': 'Administrator',
            'is_admin': True,
            'is_active': True,
            'password_hash': hash_password('admin'),
            'created': now_iso(),
            'last_updated': now_iso(),
        }
        await db.users.insert_one(admin)
