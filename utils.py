import json
import os

import youtube_dl


def load_json(fn, default=None):
    if default is None:
        default = {}
    if not os.path.isfile(fn):
        with open(fn, 'w') as f:
            json.dump(default, f)
    with open(fn) as f:
        return json.load(f)


def save_json(obj, fn):
    with open(fn, 'w') as f:
        json.dump(obj, f)


def get_yt_info(url):
    YTDL_OPTS = {
        "default_search": "ytsearch",
        "format": "bestaudio/best",
        "quiet": True,
        "extract_flat": "in_playlist"
    }
    with youtube_dl.YoutubeDL(YTDL_OPTS) as ydl:
        try:
            return ydl.extract_info(url, download=False)
        except:
            print("error", url)
