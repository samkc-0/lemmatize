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


class StoryLemmaLink(SQLModel, table=True):
    story_id: int = Field(foreign_key="story.id", primary_key=True)
    lemma_id: int = Field(foreign_key="lemma.id", primary_key=True)


class Lemma(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    lemma: str
    pos: str
    language: str
    __table_args__ = (UniqueConstraint("lemma", "pos", "language"),)
    stories: List["Story"] = Relationship(
        back_populates="lemmas", link_model=StoryLemmaLink
    )


# used to manage users feeds
# a UserLemma is tied to a source
# and if a user switches sources, they will
# get a feed of stories generated from that source.
class Origin(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hash: str


class UserLemma(SQLModel, table=True):  # optional but useful
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    lemma_id: int = Field(foreign_key="lemma.id")
    origin_id: int = Field(foreign_key="origin.id")
    seen_count: int = Field(default=0)
    learning: bool = Field(default=True)


class Story(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str
    language: str
    lemmas: List["Lemma"] = Relationship(
        back_populates="stories", link_model=StoryLemmaLink
    )
    title: Optional[str]
    rating: Optional[int]


class Input(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hash: str
    origin_id: int = Field(foreign_key="origin.id")
