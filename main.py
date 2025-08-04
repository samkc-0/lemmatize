from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import lexicography

app = FastAPI()
app.include_router(lexicography.router, prefix="/lexicography")
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

templates = Jinja2Templates(directory="templates")


@app.get("/")
def serve_index():
    return FileResponse("static/index.html")
