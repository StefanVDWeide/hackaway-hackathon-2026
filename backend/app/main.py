from fastapi_mcp import FastApiMCP
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from app.common.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="Marketplace API",
    version="0.1.0",
    lifespan=lifespan,
)
mcp = FastApiMCP(app)
mcp.mount()


from app.modules.users.router import router as users_router
from app.modules.listings.router import router as listings_router
from app.modules.categories.router import router as categories_router

app.include_router(users_router)
app.include_router(listings_router)
app.include_router(categories_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
