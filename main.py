import os
import random

import discord
import youtube_dl
from discord import VoiceClient
from discord.ext import commands
from discord.ext.commands import Cog
from discord.utils import get

from config import TOKEN
from utils import save_json, load_json, get_yt_info

try:
    from config import COMMAND_PREFIX
except ImportError:
    COMMAND_PREFIX = "!"

bot = commands.Bot(command_prefix=COMMAND_PREFIX)

playlists = load_json('playlists.json')


class Music(Cog):
    def __init__(self, _bot):
        self.bot = _bot
        self.playlist = []
        self.current_playlist = list(playlists.keys())[0]
        self.current_channel = None

    @commands.command()
    async def add(self, ctx, playlist, link):
        if playlist not in playlists:
            playlists[playlist] = []
        info = get_yt_info(link)
        if info['_type'] == 'playlist':
            for song in info['entries']:
                playlists[playlist].append(f"http://youtu.be/{song['url']}")
            await ctx.send(f'Added YT playlist {info["title"]} to playlist {playlist}!')
        else:
            playlists[playlist].append(link)
            if playlist == self.current_playlist:
                self.playlist.append(link)
            await ctx.send(f'Added song {info["title"]} to playlist {playlist}!')
        save_json(playlists, 'playlists.json')

    @commands.command()
    async def remove(self, ctx, playlist, link):
        if playlist not in playlists:
            await ctx.send("Playlist does not exist!")
            return
        playlists[playlist].remove(link)
        save_json(playlists, 'playlists.json')
        await ctx.send(f'Successfully removed link `{link}` from playlist `{playlist}`.')

    @commands.command('list')
    async def list_(self, ctx, playlist):
        pl = playlists[playlist]
        embed = discord.Embed(title=f"Playlist {playlist}")
        for link in pl:
            info = get_yt_info(link)
            embed.add_field(name=info["title"], value=link, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def select(self, ctx, playlist):
        if playlist in playlists:
            self.current_playlist = playlist
            ctx.send(f"Successfully changed playlist to `{playlist}`!")
        else:
            ctx.send("Playlist does not exist!")

    @commands.command('channel')
    async def channel_(self, ctx):
        self.current_channel = ctx.message.channel
        await ctx.send(f"Current channel set to {self.current_channel.mention}!")

    @commands.command()
    async def queue(self, ctx, playlist=None):
        if playlist is None:
            playlist = self.current_playlist
        # set the current playlist so we can loop
        self.current_playlist = playlist
        plst = playlists[playlist]
        random.shuffle(plst)
        self.playlist = plst
        voice = await self.get_voice_client(ctx.message)
        self.play_song(voice, self.get_next_song())

    @commands.command()
    async def playlist(self, ctx, playlist=None):
        if playlist in playlists:
            self.current_playlist = playlist
            ctx.send(f"Successfully set playlist to {playlist}!")
        else:
            ctx.send("Playlist does not exist!")

    @commands.command()
    async def skip(self, ctx):
        voice = await self.get_voice_client(ctx.message)
        voice.stop()

    @commands.command()
    async def stop(self, ctx):
        voice = await Music.get_voice_client(ctx.message)
        await voice.disconnect()

    @staticmethod
    async def get_voice_client(message):
        voice = get(bot.voice_clients, guild=message.channel.guild)
        print(voice)
        if voice is not None:
            print("Connected:", voice.is_connected())
        if voice is None or not voice.is_connected():
            voice = await message.author.voice.channel.connect()
        return voice

    def get_next_song(self):
        if len(self.playlist) == 0:
            self.playlist = playlists[self.current_playlist]
            random.shuffle(self.playlist)
        return self.playlist.pop(0)

    def play_song(self, client: VoiceClient, url):
        if not client.is_connected():
            return
        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            print('error')
            return
        print("Someone wants to play music let me get that ready for them...")
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        for file in os.listdir("./"):
            if file.endswith(".mp3"):
                os.rename(file, 'song.mp3')

        def after_playing(err):
            song = self.get_next_song()
            print(song, self.playlist)
            self.play_song(client, song)

        client.play(discord.FFmpegPCMAudio("song.mp3"), after=after_playing)
        client.volume = 100

    @commands.command(pass_context=True, brief="This will play a song 'play [url]'", aliases=['pl'])
    async def play(self, ctx, url: str):
        await self.play_song(ctx.channel, url)

    @commands.command(pass_context=True)
    async def join(self, ctx):
        author = ctx.message.author
        channel = author.voice.channel
        await channel.connect()

    @staticmethod
    def get_url_from_playlist(playlist, idx):
        return playlist[idx]


bot.add_cog(Music(bot))
bot.run(TOKEN)
