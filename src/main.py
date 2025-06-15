from fastapi import FastAPI

from .config.settings import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )