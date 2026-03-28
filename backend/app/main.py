import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from sqlalchemy import text

from app.common.db import engine

logger = logging.getLogger(__name__)
from app.modules.categories.router import router as categories_router
from app.modules.listings.router import router as listings_router
from app.modules.negotiations.router import router as negotiations_router
from app.modules.transactions.router import router as transactions_router
from app.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("PostgreSQL connection verified")
    yield
    await engine.dispose()


app = FastAPI(
    title="Marketplace API",
    version="0.1.0",
    lifespan=lifespan,
)



app.include_router(users_router)
app.include_router(listings_router)
app.include_router(categories_router)
app.include_router(negotiations_router)
app.include_router(transactions_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

mcp = FastApiMCP(app)
mcp.mount_http()

# Patch the HTTP transport to use stateless mode so MCP clients
# can call tools without a session initialization handshake.
_original_ensure = mcp._http_transport._ensure_session_manager_started

async def _ensure_stateless():
    await _original_ensure()
    if mcp._http_transport._session_manager:
        mcp._http_transport._session_manager._stateless = True

mcp._http_transport._ensure_session_manager_started = _ensure_stateless
