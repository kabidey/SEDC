import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from slugify import slugify as _slugify


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify(s: str) -> str:
    return _slugify(s or "")


def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    out = dict(doc)
    out.pop('_id', None)
    for k, v in list(out.items()):
        if isinstance(v, datetime):
            out[k] = v.isoformat()
    return out


def serialize_list(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [serialize_doc(d) for d in docs]


def apply_filters(params: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Build a MongoDB filter from query params."""
    q: Dict[str, Any] = {}
    search = params.get('q') or params.get('search')
    if search:
        q['$text'] = {'$search': search}
    for f in fields:
        v = params.get(f)
        if v is not None and v != "":
            if isinstance(v, list):
                q[f] = {'$in': v}
            else:
                q[f] = v
    return q
