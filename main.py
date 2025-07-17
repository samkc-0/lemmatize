from fastapi import FastAPI, HTTPException, status
from routers import lemmatizer, auth

app = FastAPI()
app.include_router(lemmatizer.router, prefix="/lemmatize")
app.include_router(auth.router, prefix="/auth")
