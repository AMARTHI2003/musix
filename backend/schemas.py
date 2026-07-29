from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SongBase(BaseModel):
    id: str
    title: str
    artist: Optional[str] = None
    thumbnail: Optional[str] = None
    duration: Optional[int] = None
    stream_url: Optional[str] = None

class Song(SongBase):
    class Config:
        from_attributes = True

class PlaylistBase(BaseModel):
    name: str

class PlaylistCreate(PlaylistBase):
    pass

class Playlist(PlaylistBase):
    id: int
    owner_id: str
    created_at: datetime
    songs: List[Song] = []

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    id: str # Firebase UID

class User(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    playlists: List[Playlist] = []

    class Config:
        from_attributes = True
