from fastapi import FastAPI

app = FastAPI(debug=True)


@app.get("/")
async def root():
    return {"status": "server is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", reload=True)