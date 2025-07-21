from sqlmodel import SQLModel, Field, UniqueConstraint, Relationship
from datetime import datetime, timezone
from typing import Optional, List
from security import hash_password


def utc_now():
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=utc_now)

    @classmethod
    def from_create(cls, user_create: "UserCreate") -> "User":
        return cls(
            username=user_create.username,
            password_hash=hash_password(user_create.password),
        )


class UserCreate(SQLModel):
    username: str
    password: str


class UserLogin(SQLModel):
    username: str
    password: str


class UserRead(SQLModel):
    id: int
    username: str


class Says(SQLModel, table=True):
    story_id: int = Field(foreign_key="story.id", primary_key=True)
    headword_id: int = Field(foreign_key="headword.id", primary_key=True)


class Headword(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    tag: str
    language: str
    __table_args__ = (UniqueConstraint("text", "tag", "language"),)


# used to manage users feeds
# a Word is tied to a source
# and if a user switches sources, they will
# get a feed of stories generated from that source.
class Lexicon(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hash: str


class Word(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    headword_id: int = Field(foreign_key="headword.id")
    first_lexicon_id: int = Field(foreign_key="lexicon.id")
    seen_count: int = Field(default=0)
    learning: bool = Field(default=True)


class Story(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    language: str
    lexicon_hash: str
    title: Optional[str] = None
    rating: Optional[int] = None


class Perusal(SQLModel, table=True):
    story_id: int = Field(foreign_key="story.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    read: bool = Field(default=False)


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hash: str
    lexicon_id: int = Field(foreign_key="lexicon.id")
