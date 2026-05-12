"""SMIFS Enterprise Data Centre - FastAPI server entrypoint."""
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from app.db import db, client
from app.auth import init_admin_user
from app.routers.auth_router import router as auth_router
from app.routers.users_router import router as users_router, groups_router, tokens_router
from app.routers.auto_routers import build_all_routers
from app.routers.special_routers import (
    cables_router, prefix_router, rack_tools_router,
    changelog_router, search_router, stats_router,
)
from app.routers.discovery_router import router as discovery_router
from app.graphql_api import graphql_router

app = FastAPI(title='SMIFS Enterprise Data Centre', version='1.0.0')

api_router = APIRouter(prefix='/api')


@api_router.get('/')
async def root():
    return {
        'app': 'SMIFS Enterprise Data Centre',
        'version': '1.0.0',
        'message': 'Network/Datacenter Infrastructure Management Platform',
    }


@api_router.get('/health')
async def health():
    try:
        await db.command('ping')
        return {'status': 'ok'}
    except Exception as e:
        return {'status': 'error', 'detail': str(e)}


# Include auth + admin routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(groups_router)
api_router.include_router(tokens_router)

# Include all auto-generated model routers
for r in build_all_routers():
    api_router.include_router(r)

# Specialized routers
api_router.include_router(cables_router)
api_router.include_router(prefix_router)
api_router.include_router(rack_tools_router)
api_router.include_router(changelog_router)
api_router.include_router(search_router)
api_router.include_router(stats_router)
api_router.include_router(discovery_router)


# Schema introspection: list all available models
@api_router.get('/_schema')
async def list_schema():
    from app.routers.auto_routers import MODEL_DEFS
    return {
        'models': [
            {'path': d[0], 'tags': d[1], 'collection': d[2], 'object_type': d[3]}
            for d in MODEL_DEFS
        ],
        'specials': [
            '/cables', '/prefix-tools/tree', '/rack-tools/{rack_id}/elevation',
            '/changelog', '/search', '/stats', '/graphql',
        ],
    }


app.include_router(api_router)

# GraphQL endpoint at /api/graphql
app.include_router(graphql_router, prefix='/api/graphql')


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=['*'],
    allow_headers=['*'],
)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@app.on_event('startup')
async def on_startup():
    await init_admin_user()
    # Create indexes
    try:
        await db.users.create_index('username', unique=True)
        await db.object_changes.create_index('time')
        await db.object_changes.create_index([('object_type', 1), ('object_id', 1)])
    except Exception as e:
        logger.warning(f'Index init: {e}')
    logger.info('SMIFS Enterprise Data Centre started')


@app.on_event('shutdown')
async def on_shutdown():
    client.close()
