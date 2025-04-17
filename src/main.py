from fastapi import FastAPI

from src.api.api_v1.handler.main_handler import main_router
from src.core.errors import register_all_errors
from src.core.middleware.logging import register_middleware

app = FastAPI(debug=True)

register_middleware(app)
register_all_errors(app)
app.include_router(main_router)
from fastapi import BackgroundTasks

@app.get("/")
async def root():
    return {"status": "server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", reload=True)