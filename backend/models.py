from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Association table for Playlists and Songs
playlist_song_association = Table(
    'playlist_song',
    Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlists.id')),
    Column('song_id', String, ForeignKey('songs.id'))
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True) # Firebase UID
    email = Column(String, unique=True, index=True)
    username = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    playlists = relationship("Playlist", back_populates="owner")

class Song(Base):
    __tablename__ = "songs"
    
    id = Column(String, primary_key=True, index=True) # YouTube ID or UUID
    title = Column(String, nullable=False)
    artist = Column(String)
    thumbnail = Column(String)
    duration = Column(Integer) # In seconds
    stream_url = Column(String) # For hosted tracks, if applicable
    
class Playlist(Base):
    __tablename__ = "playlists"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    owner_id = Column(String, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="playlists")
    songs = relationship("Song", secondary=playlist_song_association)
