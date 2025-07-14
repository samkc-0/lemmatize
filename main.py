from fastapi import FastAPI, HTTPException, status
from routers import lemmatizer

app = FastAPI()
app.include_router(lemmatizer.router, prefix="/lemmatize")
