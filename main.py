from fastapi import FastAPI
from routers import auth, lexicography, users

app = FastAPI()
app.include_router(lexicography.router, prefix="/lexicography")
app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/users")
