from typing import Dict, Any, Optional
from .db import db
from .utils import new_id, now_iso


async def log_change(
    action: str,  # 'create', 'update', 'delete'
    object_type: str,
    object_id: str,
    object_repr: str = '',
    user: Optional[Dict[str, Any]] = None,
    prechange_data: Optional[Dict[str, Any]] = None,
    postchange_data: Optional[Dict[str, Any]] = None,
):
    def _clean(d):
        if d is None: return None
        out = dict(d)
        out.pop('_id', None)
        return out
    entry = {
        'id': new_id(),
        'action': action,
        'object_type': object_type,
        'object_id': object_id,
        'object_repr': object_repr,
        'user_id': user.get('id') if user else None,
        'username': user.get('username') if user else 'system',
        'prechange_data': _clean(prechange_data),
        'postchange_data': _clean(postchange_data),
        'time': now_iso(),
    }
    await db.object_changes.insert_one(entry)
    entry.pop('_id', None)
    return entry
