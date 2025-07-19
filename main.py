from fastapi import FastAPI, HTTPException, status
from routers import lemmatizer, auth, user

app = FastAPI()
app.include_router(lemmatizer.router, prefix="/lemmatize")
app.include_router(auth.router, prefix="/auth")
app.include_router(user.router, prefix="/me")
