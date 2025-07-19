from fastapi import APIRouter, Depends
from typing import List
from models import Lemma, UserLemma
from db import get_session
from routers.auth import get_current_active_user
from sqlmodel import Session

router = APIRouter()


@router.get("/lemmas")
async def get_lemmas(
    session: Session = Depends(get_session), user=Depends(get_current_active_user)
) -> List[Lemma]:

    return []
