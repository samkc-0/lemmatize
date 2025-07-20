from fastapi import FastAPI
from routers import lemmatizer, auth, users

app = FastAPI()
app.include_router(lemmatizer.router, prefix="/lemmatize")
app.include_router(auth.router, prefix="/auth")
app.include_router(users.router, prefix="/me")
