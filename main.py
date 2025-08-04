from fastapi import FastAPI
from routers import lexicography

app = FastAPI()
app.include_router(lexicography.router, prefix="/lexicography")
