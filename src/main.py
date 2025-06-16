import uvicorn
from fastapi import FastAPI

from .config.settings import config

app = FastAPI(
    title=config.PROJECT_NAME,
    debug=config.DEBUG,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
    )
