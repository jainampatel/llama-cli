from sqlmodel import create_engine, Field, SQLModel, Session, select, Relationship
from typing import List
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column

EMBED_DIM = 384  


#* User model
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    username: str = Field(index=True, unique=True)
    password: str = Field(min_length=8, max_length=64)
    #For python object mapping
    chats: List["Chat"] = Relationship(back_populates="user")

#* Chat model
class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    #Defined foreign key of user_id 
    user_id: int = Field(foreign_key="user.id")
    #For python object mapping
    user: "User" = Relationship(back_populates="chats")
    #For python object mapping
    interactions: List["Chat_interactions"] = Relationship(back_populates="chat")

#* Chat Interactions model
class Chat_interactions(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_prompt: str
    system_response: str
    #Defined foreign key of chat_id 
    chat_id: int = Field(foreign_key="chat.id")
    #For python object mapping
    chat: "Chat" = Relationship(back_populates="interactions")

#* Chat vectors model
class Chat_vectors(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    chat_interaction_id: int = Field(foreign_key="chat_interactions.id")
    text: str  
    chat_id: int = Field(foreign_key="chat.id")
    embedding: List[float] = Field(sa_column=Column(Vector(EMBED_DIM)))