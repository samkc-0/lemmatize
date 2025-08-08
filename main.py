from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from routers import lexicography

app = FastAPI()
app.include_router(lexicography.router, prefix="/lexicography")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
def serve_demo():
    return FileResponse("static/demo.html")
