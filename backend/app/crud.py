"""Generic CRUD helpers used by routers."""
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
from .db import db
from .utils import new_id, now_iso, serialize_doc, serialize_list, slugify
from .changelog import log_change


class CRUD:
    def __init__(self, collection: str, object_type: str, slug_field: Optional[str] = 'name'):
        self.collection = collection
        self.object_type = object_type
        self.slug_field = slug_field

    @property
    def col(self):
        return db[self.collection]

    async def list(self, filter: Optional[Dict[str, Any]] = None, limit: int = 100, offset: int = 0, sort: Optional[str] = None) -> Dict[str, Any]:
        f = filter or {}
        total = await self.col.count_documents(f)
        cursor = self.col.find(f, {'_id': 0})
        if sort:
            direction = -1 if sort.startswith('-') else 1
            cursor = cursor.sort(sort.lstrip('-'), direction)
        else:
            cursor = cursor.sort('created', -1)
        cursor = cursor.skip(offset).limit(limit)
        items = await cursor.to_list(length=limit)
        return {'total': total, 'limit': limit, 'offset': offset, 'results': serialize_list(items)}

    async def get(self, id: str) -> Dict[str, Any]:
        doc = await self.col.find_one({'id': id}, {'_id': 0})
        if not doc:
            raise HTTPException(404, f'{self.object_type} not found')
        return serialize_doc(doc)

    async def create(self, data: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        doc = dict(data)
        doc['id'] = doc.get('id') or new_id()
        doc['created'] = now_iso()
        doc['last_updated'] = now_iso()
        if self.slug_field and self.slug_field in doc and not doc.get('slug'):
            doc['slug'] = slugify(str(doc[self.slug_field]))
        await self.col.insert_one(doc)
        doc.pop('_id', None)
        await log_change('create', self.object_type, doc['id'], doc.get('name') or doc.get('display') or doc['id'], user, None, doc)
        return serialize_doc(doc)

    async def update(self, id: str, data: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        existing = await self.col.find_one({'id': id}, {'_id': 0})
        if not existing:
            raise HTTPException(404, f'{self.object_type} not found')
        updated = {**existing, **{k: v for k, v in data.items() if v is not None}, 'last_updated': now_iso()}
        if self.slug_field and self.slug_field in data and data.get(self.slug_field):
            updated['slug'] = slugify(str(data[self.slug_field]))
        await self.col.update_one({'id': id}, {'$set': updated})
        await log_change('update', self.object_type, id, updated.get('name') or id, user, existing, updated)
        return serialize_doc(updated)

    async def delete(self, id: str, user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        existing = await self.col.find_one({'id': id}, {'_id': 0})
        if not existing:
            raise HTTPException(404, f'{self.object_type} not found')
        await self.col.delete_one({'id': id})
        await log_change('delete', self.object_type, id, existing.get('name') or id, user, existing, None)
        return {'deleted': id}

    async def bulk_delete(self, ids: List[str], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        deleted = 0
        for i in ids:
            try:
                await self.delete(i, user)
                deleted += 1
            except Exception:
                pass
        return {'deleted': deleted}
