from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database import get_db
from auth import get_current_user
from models import User, Playlist, Song, playlist_song_association
from schemas import PlaylistCreate, Playlist as PlaylistSchema

router = APIRouter(prefix="/playlists", tags=["Playlists"])


@router.get("/", response_model=list[PlaylistSchema])
async def get_playlists(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all playlists for the current user."""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.owner_id == user.id)
        .options(selectinload(Playlist.songs))
    )
    return result.scalars().all()


@router.post("/favorites/toggle")
async def toggle_favorite(
    song_id: str,
    title: str = "Unknown",
    artist: str = "Unknown Artist",
    thumbnail: str = "",
    duration: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Toggle a song in the user's Favorites playlist."""
    # Find or create Favorites playlist
    result = await db.execute(
        select(Playlist)
        .where(Playlist.owner_id == user.id, Playlist.name == "Favorites")
        .options(selectinload(Playlist.songs))
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        playlist = Playlist(name="Favorites", owner_id=user.id)
        db.add(playlist)
        await db.flush()
        
    # Find or create the song
    song_result = await db.execute(select(Song).where(Song.id == song_id))
    song = song_result.scalar_one_or_none()
    if not song:
        song = Song(id=song_id, title=title, artist=artist, thumbnail=thumbnail, duration=duration)
        db.add(song)
        await db.flush()

    # Toggle
    added = False
    if song in playlist.songs:
        playlist.songs.remove(song)
    else:
        playlist.songs.append(song)
        added = True
        
    await db.commit()
    return {"message": "Added to Favorites" if added else "Removed from Favorites", "is_favorite": added}

@router.post("/", response_model=PlaylistSchema)
async def create_playlist(
    data: PlaylistCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new playlist."""
    playlist = Playlist(name=data.name, owner_id=user.id)
    db.add(playlist)
    await db.commit()
    await db.refresh(playlist)
    return playlist


@router.post("/{playlist_id}/songs/{song_id}")
async def add_song_to_playlist(
    playlist_id: int,
    song_id: str,
    title: str = "Unknown",
    artist: str = "Unknown Artist",
    thumbnail: str = "",
    duration: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a song to a playlist. Creates the song record if it doesn't exist."""
    # Verify playlist ownership
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.owner_id == user.id)
        .options(selectinload(Playlist.songs))
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    # Find or create the song
    song_result = await db.execute(select(Song).where(Song.id == song_id))
    song = song_result.scalar_one_or_none()
    if not song:
        song = Song(id=song_id, title=title, artist=artist, thumbnail=thumbnail, duration=duration)
        db.add(song)
        await db.flush()

    # Add to playlist if not already there
    if song not in playlist.songs:
        playlist.songs.append(song)

    await db.commit()
    return {"message": f"Song '{title}' added to '{playlist.name}'"}


@router.delete("/{playlist_id}/songs/{song_id}")
async def remove_song_from_playlist(
    playlist_id: int,
    song_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a song from a playlist."""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id, Playlist.owner_id == user.id)
        .options(selectinload(Playlist.songs))
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    song_result = await db.execute(select(Song).where(Song.id == song_id))
    song = song_result.scalar_one_or_none()
    if song and song in playlist.songs:
        playlist.songs.remove(song)
        await db.commit()

    return {"message": "Song removed from playlist"}


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a playlist."""
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id, Playlist.owner_id == user.id)
    )
    playlist = result.scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    await db.delete(playlist)
    await db.commit()
    return {"message": "Playlist deleted"}
