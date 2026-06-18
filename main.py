import importlib
import pkgutil
from pathlib import Path

from fastapi import FastAPI
from fastapi_mcp import FastApiMCP

app = FastAPI(title="mcp-claw-utils")
mcp = FastApiMCP(app)

_api_dir = Path(__file__).parent / "app" / "api"


def _discover_routers() -> None:
    """Import every .py module in app/api/ and include its router."""
    if not _api_dir.is_dir():
        return
    for _importer, modname, ispkg in pkgutil.iter_modules([str(_api_dir)]):
        if ispkg or modname.startswith("_"):
            continue
        mod = importlib.import_module(f"app.api.{modname}")
        if hasattr(mod, "router"):
            app.include_router(mod.router)


_discover_routers()
mcp.mount()

@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", reload=True)
