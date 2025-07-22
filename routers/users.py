from fastapi import APIRouter, Depends
from typing import List, Optional
from models import Headword, User, Word, UserRead, Lexicon, Document
from db import get_session
from routers.auth import get_current_active_user
from routers import lexicography
from routers.lexicography import TextIn, HeadwordOut
from sqlmodel import Session, col, select
import hashlib
import re
from pydantic import BaseModel
from utils import normalize_text, hash_lexicon, hash_document


router = APIRouter()


class UploadResponse(BaseModel):
    reused_input: bool
    reused_lexicon: bool
    new_headwords_added: int
    words_linked: int
    lexicon_id: Optional[int]  # useful for debugging, linking, etc


@router.get("/words")
async def get_headwords(
    session: Session = Depends(get_session), user=Depends(get_current_active_user)
) -> List[Headword]:
    words = session.exec(select(Headword).join(Word, Word.user_id == user.id)).all()
    return list(words)


@router.post("/upload")
async def save_text(
    text_in: TextIn,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> UploadResponse:
    # if someone has submitted this text before, just copy the word list for the user
    document_hash = hash_document(normalize_text(text_in.text))
    existing_input = session.exec(
        select(Document).where(col(Document.hash) == document_hash)
    ).first()
    if existing_input:
        lexicon = session.exec(
            select(Lexicon).where(col(Lexicon.id) == existing_input.lexicon_id)
        ).one()
        words_linked = copy_words_to_user(session, lexicon, current_user)
        return UploadResponse(
            reused_input=True,
            reused_lexicon=False,
            new_headwords_added=0,
            words_linked=words_linked,
            lexicon_id=lexicon.id,
        )
    # if someone has submitted a text with exactly the same vocabulary before,
    # copy the word list for the user
    headwords_out = await lexicography.analyze_text(text_in)
    lexicon_hash = hash_lexicon(headwords_out)
    existing_lexicon = session.exec(
        select(Lexicon).where(Lexicon.hash == lexicon_hash)
    ).first()
    if existing_lexicon:
        words_copied = copy_words_to_user(session, existing_lexicon, current_user)
        return UploadResponse(
            reused_input=False,
            reused_lexicon=True,
            new_headwords_added=0,
            words_linked=words_copied,
            lexicon_id=existing_lexicon.id,
        )
    # else, do the inserts manually
    lexicon = Lexicon(hash=lexicon_hash)
    session.add(lexicon)
    session.commit()
    session.refresh(lexicon)
    input_ = Document(hash=document_hash, lexicon_id=lexicon.id)
    session.add(input_)
    session.commit()
    session.refresh(input_)
    new_headwords_in_db_count = 0
    new_words_linked = 0
    for headword in headwords_out:
        exists_in_db = session.exec(
            select(Headword).where(
                Headword.text == headword.text,
                Headword.tag == headword.tag,
                Headword.language == headword.language,
            )
        ).first()
        if not exists_in_db:
            exists_in_db = Headword(**headword.model_dump())
            session.add(exists_in_db)
            new_headwords_in_db_count += 1
            session.commit()
            session.refresh(exists_in_db)
        exists_for_user = session.exec(
            select(Word)
            .where(Word.user_id == current_user.id)
            .where(Word.headword_id == exists_in_db.id)
        ).first()
        if not exists_for_user:
            word_in = Word(
                user_id=current_user.id,
                headword_id=exists_in_db.id,
                first_lexicon_id=lexicon.id,
            )
            session.add(word_in)
            new_words_linked += 1
            session.commit()
            session.refresh(word_in)

    return UploadResponse(
        reused_input=False,
        reused_lexicon=False,
        new_headwords_added=new_headwords_in_db_count,
        words_linked=new_words_linked,
        lexicon_id=lexicon.id,
    )


def copy_words_to_user(session: Session, lexicon: Lexicon, user: User) -> int:
    statement = select(Word).where(col(Word.first_lexicon_id) == lexicon.id)
    to_copy = session.exec(statement).all()
    words_copied: int = 0
    for being_copied in to_copy:
        existing = session.exec(
            select(Word)
            .where(col(Word.user_id) == user.id)
            .where(col(Word.headword_id) == being_copied.id)
        )
        if existing:
            continue
        user_copy = Word(
            headword_id=being_copied.headword_id,
            first_lexicon_id=being_copied.first_lexicon_id,
            user_id=user.id,
        )
        session.add(user_copy)
        words_copied += 1
    session.commit()
    return words_copied
