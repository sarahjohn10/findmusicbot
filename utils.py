import yt_dlp
import asyncio
import os
from functools import partial
from ytmusicapi import YTMusic

# Initialize YTMusic once for speed
yt_music = YTMusic()

def search_music(query, limit=10):
    try:
        # Ultra-fast API search (0.5s)
        results = yt_music.search(query, filter="songs")
        extracted = []
        for i in results[:limit]:
            vid = i.get('videoId')
            if vid and len(vid) == 11: # Validate 11-char YouTube ID
                extracted.append({
                    'id': vid,
                    'title': i.get('title'),
                    'uploader': i['artists'][0]['name'] if i.get('artists') else 'Artist',
                    'duration': i.get('duration_seconds', 0)
                })
        if extracted: return extracted
    except: pass
    
    # Fallback to yt-dlp if API fails
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'extract_flat': True,
        'quiet': True,
        'default_search': 'ytsearch'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
        return info.get('entries', [])

async def search_music_async(query, limit=10):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(search_music, query, limit))

def download_audio(video_url):
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'quiet': True, 
        'noplaylist': True,
        'extractor_args': {'youtube': ['player_client=android_music,web']},
        'extractor_retries': 2,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        path = ydl.prepare_filename(info).rsplit('.', 1)[0] + '.m4a'
        return {'filepath': path, 'title': info.get('title'), 'artist': info.get('uploader'), 'duration': info.get('duration')}


async def download_audio_async(url):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(download_audio, url))
