from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from ..db import db
from ..auth import hash_password, require_admin, require_user
from ..utils import new_id, now_iso, serialize_doc, serialize_list

router = APIRouter(prefix='/users', tags=['Admin'])


class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    first_name: Optional[str] = ''
    last_name: Optional[str] = ''
    is_admin: bool = False
    is_active: bool = True


class UserUpdate(BaseModel):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


@router.get('')
async def list_users(user: Dict[str, Any] = Depends(require_user)):
    docs = await db.users.find({}, {'_id': 0, 'password_hash': 0}).to_list(length=1000)
    return {'total': len(docs), 'results': serialize_list(docs)}


@router.post('')
async def create_user(payload: UserCreate, admin: Dict[str, Any] = Depends(require_admin)):
    existing = await db.users.find_one({'username': payload.username})
    if existing:
        raise HTTPException(400, 'Username already exists')
    u = {
        'id': new_id(), 'username': payload.username, 'email': payload.email,
        'first_name': payload.first_name or '', 'last_name': payload.last_name or '',
        'is_admin': payload.is_admin, 'is_active': payload.is_active,
        'password_hash': hash_password(payload.password),
        'created': now_iso(), 'last_updated': now_iso(),
    }
    await db.users.insert_one(u)
    return serialize_doc({k: v for k, v in u.items() if k != 'password_hash'})


@router.patch('/{id}')
async def update_user(id: str, payload: UserUpdate, admin: Dict[str, Any] = Depends(require_admin)):
    existing = await db.users.find_one({'id': id})
    if not existing:
        raise HTTPException(404, 'User not found')
    update = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None and k != 'password'}
    if payload.password:
        update['password_hash'] = hash_password(payload.password)
    update['last_updated'] = now_iso()
    await db.users.update_one({'id': id}, {'$set': update})
    fresh = await db.users.find_one({'id': id}, {'_id': 0, 'password_hash': 0})
    return serialize_doc(fresh)


@router.delete('/{id}')
async def delete_user(id: str, admin: Dict[str, Any] = Depends(require_admin)):
    if id == admin['id']:
        raise HTTPException(400, 'Cannot delete self')
    await db.users.delete_one({'id': id})
    return {'deleted': id}


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = ''
    permissions: Optional[List[str]] = []


groups_router = APIRouter(prefix='/groups', tags=['Admin'])


@groups_router.get('')
async def list_groups():
    docs = await db.groups.find({}, {'_id': 0}).to_list(length=1000)
    return {'total': len(docs), 'results': serialize_list(docs)}


@groups_router.post('')
async def create_group(payload: GroupCreate, admin: Dict[str, Any] = Depends(require_admin)):
    g = {'id': new_id(), **payload.model_dump(), 'created': now_iso(), 'last_updated': now_iso()}
    await db.groups.insert_one(g)
    return serialize_doc(g)


@groups_router.delete('/{id}')
async def delete_group(id: str, admin: Dict[str, Any] = Depends(require_admin)):
    await db.groups.delete_one({'id': id})
    return {'deleted': id}


class TokenCreate(BaseModel):
    description: Optional[str] = ''
    write_enabled: bool = True


tokens_router = APIRouter(prefix='/api-tokens', tags=['Admin'])


@tokens_router.get('')
async def list_tokens(user: Dict[str, Any] = Depends(require_user)):
    docs = await db.api_tokens.find({'user_id': user['id']}, {'_id': 0}).to_list(length=1000)
    return {'total': len(docs), 'results': serialize_list(docs)}


@tokens_router.post('')
async def create_token(payload: TokenCreate, user: Dict[str, Any] = Depends(require_user)):
    import secrets
    t = {
        'id': new_id(),
        'user_id': user['id'],
        'username': user['username'],
        'key': secrets.token_hex(20),
        'description': payload.description,
        'write_enabled': payload.write_enabled,
        'created': now_iso(),
        'last_updated': now_iso(),
    }
    await db.api_tokens.insert_one(t)
    return serialize_doc(t)


@tokens_router.delete('/{id}')
async def delete_token(id: str, user: Dict[str, Any] = Depends(require_user)):
    await db.api_tokens.delete_one({'id': id, 'user_id': user['id']})
    return {'deleted': id}
