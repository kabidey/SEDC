"""Generic router builder for CRUD models. Allows quick wiring of REST endpoints for any model."""
from typing import Any, Dict, List, Optional, Type
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from .crud import CRUD
from .auth import get_current_user, require_user
from .csv_io import rows_to_csv, csv_to_rows
from .db import db
from .utils import serialize_doc, serialize_list, new_id, now_iso


def build_router(
    prefix: str,
    tags: List[str],
    collection: str,
    object_type: str,
    create_schema: Type[BaseModel],
    update_schema: Type[BaseModel],
    filter_fields: Optional[List[str]] = None,
    slug_field: Optional[str] = 'name',
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)
    crud = CRUD(collection=collection, object_type=object_type, slug_field=slug_field)
    filter_fields = filter_fields or []

    @router.get('')
    async def list_items(
        limit: int = Query(100, le=1000),
        offset: int = 0,
        q: Optional[str] = None,
        sort: Optional[str] = None,
    ):
        f: Dict[str, Any] = {}
        if q:
            f['$or'] = [{'name': {'$regex': q, '$options': 'i'}}, {'slug': {'$regex': q, '$options': 'i'}}, {'description': {'$regex': q, '$options': 'i'}}, {'tags': {'$regex': q, '$options': 'i'}}]
        return await crud.list(filter=f, limit=limit, offset=offset, sort=sort)

    @router.get('/export')
    async def export_csv():
        items = await db[collection].find({}, {'_id': 0}).to_list(length=10000)
        return rows_to_csv(serialize_list(items))

    @router.post('/import')
    async def import_csv(file: UploadFile = File(...), user: Dict[str, Any] = Depends(require_user)):
        content = (await file.read()).decode('utf-8')
        rows = csv_to_rows(content)
        created = 0
        errors = []
        for r in rows:
            try:
                # Remove empty values
                r = {k: v for k, v in r.items() if v not in (None, '', 'None')}
                await crud.create(r, user)
                created += 1
            except Exception as e:
                errors.append(str(e))
        return {'created': created, 'errors': errors[:10]}

    @router.get('/{id}')
    async def get_item(id: str):
        return await crud.get(id)

    @router.post('')
    async def create_item(payload: create_schema, user: Dict[str, Any] = Depends(require_user)):  # type: ignore
        return await crud.create(payload.model_dump(exclude_unset=True), user)

    @router.patch('/{id}')
    async def update_item(id: str, payload: update_schema, user: Dict[str, Any] = Depends(require_user)):  # type: ignore
        return await crud.update(id, payload.model_dump(exclude_unset=True), user)

    @router.put('/{id}')
    async def replace_item(id: str, payload: create_schema, user: Dict[str, Any] = Depends(require_user)):  # type: ignore
        return await crud.update(id, payload.model_dump(exclude_unset=True), user)

    @router.delete('/{id}')
    async def delete_item(id: str, user: Dict[str, Any] = Depends(require_user)):
        return await crud.delete(id, user)

    @router.post('/bulk_delete')
    async def bulk_delete(payload: Dict[str, List[str]], user: Dict[str, Any] = Depends(require_user)):
        return await crud.bulk_delete(payload.get('ids', []), user)

    return router
