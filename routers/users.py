from fastapi import APIRouter, Depends
from typing import List, Optional
from models import Lemma, User, UserLemma, UserRead, Origin, Input
from db import get_session
from routers.auth import get_current_active_user
from routers.lemmatizer import lemmatize, TextIn, LemmaOut
from sqlmodel import Session, col, select
import hashlib
import re
from pydantic import BaseModel

router = APIRouter()


class UploadResponse(BaseModel):
    reused_input: bool
    reused_origin: bool
    new_lemmas_added: int
    user_lemmas_linked: int
    origin_id: Optional[int]  # useful for debugging, linking, etc


@router.get("/")
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    user_read = UserRead(**current_user.model_dump())
    return user_read


@router.get("/lemmas")
async def get_lemmas(
    session: Session = Depends(get_session), user=Depends(get_current_active_user)
) -> List[Lemma]:
    lemmas = session.exec(
        select(Lemma).join(UserLemma, UserLemma.user_id == user.id)
    ).all()
    return list(lemmas)


def hash_lemma_list(lemmas: List[LemmaOut]) -> str:
    sorted_lemmas = sorted(lemmas, key=lambda l: (l.lemma, l.pos, l.language))
    serialized = "".join(f"{l.lemma}:{l.pos}:{l.language}" for l in sorted_lemmas)
    return hashlib.sha256(serialized.encode()).hexdigest()


def hash_user_input(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[.,!?;:()\[\]\"']", "", text)  # light punctuation strip
    text = re.sub(r"\s+", " ", text)  # collapse whitespace
    return text


@router.post("/upload")
async def save_text(
    text_in: TextIn,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UploadResponse:
    # if someone has submitted this text before, just copy the lemma list for the user
    text_hash = hash_user_input(normalize_text(text_in.text))
    existing_input = session.exec(
        select(Input).where(col(Input.hash) == text_hash)
    ).first()
    if existing_input:
        origin = session.exec(
            select(Origin).where(col(Origin.id) == existing_input.origin_id)
        ).one()
        lemmas_copied = copy_lemmas_to_user(session, origin, current_user)
        return UploadResponse(
            reused_input=True,
            reused_origin=False,
            new_lemmas_added=0,
            user_lemmas_linked=lemmas_copied,
            origin_id=origin.id,
        )
    # if someone has submitted a text with exactly the same vocabulary before,
    # copy the lemma list for the user
    lemmas_out = await lemmatize(text_in)
    origin_hash = hash_lemma_list(lemmas_out)
    existing_origin = session.exec(
        select(Origin).where(Origin.hash == origin_hash)
    ).first()
    if existing_origin:
        lemmas_copied = copy_lemmas_to_user(session, existing_origin, current_user)
        return UploadResponse(
            reused_input=False,
            reused_origin=True,
            new_lemmas_added=0,
            user_lemmas_linked=lemmas_copied,
            origin_id=existing_origin.id,
        )
    # else, do the inserts manually
    origin = Origin(hash=origin_hash)
    session.add(origin)
    session.commit()
    session.refresh(origin)
    input_ = Input(hash=text_hash, origin_id=origin.id)
    session.add(input_)
    session.commit()
    session.refresh(input_)
    new_lemmas_in_db_count = 0
    new_lemmas_linked = 0
    for lemma in lemmas_out:
        exists_in_db = session.exec(
            select(Lemma).where(
                Lemma.lemma == lemma.lemma,
                Lemma.pos == lemma.pos,
                Lemma.language == lemma.language,
            )
        ).first()
        if not exists_in_db:
            exists_in_db = Lemma(**lemma.model_dump())
            session.add(exists_in_db)
            new_lemmas_in_db_count += 1
            session.commit()
            session.refresh(exists_in_db)
        exists_for_user = session.exec(
            select(UserLemma)
            .where(UserLemma.user_id == current_user.id)
            .where(UserLemma.lemma_id == exists_in_db.id)
        ).first()
        if not exists_for_user:
            user_lemma_in = UserLemma(
                user_id=current_user.id, lemma_id=exists_in_db.id, origin_id=origin.id
            )
            session.add(user_lemma_in)
            new_lemmas_linked += 1
            session.commit()
            session.refresh(user_lemma_in)

    return UploadResponse(
        reused_input=False,
        reused_origin=False,
        new_lemmas_added=new_lemmas_in_db_count,
        user_lemmas_linked=new_lemmas_linked,
        origin_id=origin.id,
    )


def copy_lemmas_to_user(session: Session, origin: Origin, user: User) -> int:
    statement = select(UserLemma).where(col(UserLemma.origin_id) == origin.id)
    to_copy = session.exec(statement).all()
    lemmas_copied: int = 0
    for userlemma in to_copy:
        existing = session.exec(
            select(UserLemma)
            .where(col(UserLemma.user_id) == user.id)
            .where(col(UserLemma.lemma_id) == userlemma.id)
        )
        if existing:
            continue
        user_copy = UserLemma(
            lemma_id=userlemma.lemma_id, origin_id=userlemma.origin_id, user_id=user.id
        )
        session.add(user_copy)
        lemmas_copied += 1
    session.commit()
    return lemmas_copied
