from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from ..db import db
from ..auth import hash_password, verify_password, create_access_token, get_current_user, require_user, require_admin
from ..utils import new_id, now_iso, serialize_doc

router = APIRouter(prefix='/auth', tags=['Authentication'])


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    first_name: Optional[str] = ''
    last_name: Optional[str] = ''


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    user: Dict[str, Any]


@router.post('/login', response_model=TokenResponse)
async def login(payload: LoginRequest):
    user = await db.users.find_one({'username': payload.username})
    if not user or not verify_password(payload.password, user.get('password_hash', '')):
        raise HTTPException(status_code=401, detail='Invalid credentials')
    if not user.get('is_active', True):
        raise HTTPException(status_code=403, detail='User inactive')
    token = create_access_token({'sub': user['username'], 'uid': user['id']})
    safe = serialize_doc({k: v for k, v in user.items() if k != 'password_hash'})
    return TokenResponse(access_token=token, user=safe)


@router.post('/register', response_model=TokenResponse)
async def register(payload: RegisterRequest):
    existing = await db.users.find_one({'username': payload.username})
    if existing:
        raise HTTPException(status_code=400, detail='Username already exists')
    user_count = await db.users.count_documents({})
    user = {
        'id': new_id(),
        'username': payload.username,
        'email': payload.email,
        'first_name': payload.first_name or '',
        'last_name': payload.last_name or '',
        'is_admin': user_count == 0,  # first user is admin
        'is_active': True,
        'password_hash': hash_password(payload.password),
        'created': now_iso(),
        'last_updated': now_iso(),
    }
    await db.users.insert_one(user)
    token = create_access_token({'sub': user['username'], 'uid': user['id']})
    safe = serialize_doc({k: v for k, v in user.items() if k != 'password_hash'})
    return TokenResponse(access_token=token, user=safe)


@router.get('/me')
async def me(user: Dict[str, Any] = Depends(require_user)):
    return user
