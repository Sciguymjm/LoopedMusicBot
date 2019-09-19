import os
import random

import discord
import youtube_dl
from discord.ext.commands import Cog
from discord.utils import get

from config import TOKEN
from utils import save_json, load_json

try:
    from config import COMMAND_PREFIX
except ImportError:
    COMMAND_PREFIX = "!"
from discord.ext import commands

bot = commands.Bot(command_prefix=COMMAND_PREFIX)

playlists = load_json('playlists.json')

current_playlist = list(playlists.keys())[0]
current_channel = None


class GuildState:
    """Helper class managing per-guild state."""

    def __init__(self):
        self.volume = 1.0
        self.playlist = []
        self.skip_votes = set()
        self.now_playing = None

    def is_requester(self, user):
        return self.now_playing.requested_by == user


class Music(Cog):

    def __init__(self, _bot):
        self.bot = _bot
        self.states = {}

    def get_state(self, guild):
        """Gets the state for `guild`, creating it if it does not exist."""
        if guild.id in self.states:
            return self.states[guild.id]
        else:
            self.states[guild.id] = GuildState()
            return self.states[guild.id]

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('pong')

    @commands.command()
    async def add(self, ctx, playlist, link):
        if playlist not in playlists:
            playlists[playlist] = []
        playlists[playlist].append(link)
        save_json(playlists, 'playlists.json')
        await ctx.send('thanks')

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
            embed.add_field(name="Song", value=link, inline=True)
        await ctx.send(embed=embed)

    @commands.command()
    async def select(self, ctx, playlist):
        global current_playlist
        if playlist in playlists:
            current_playlist = playlist
            ctx.send(f"Successfully changed playlist to `{playlist}`!")
        else:
            ctx.send("Playlist does not exist!")

    @commands.command('channel')
    async def channel_(self, ctx):
        global current_channel
        current_channel = ctx.message.channel
        await ctx.send(f"Current channel set to {current_channel.mention}!")


    @commands.command()
    async def queue(self, ctx, playlist=current_playlist):
        plst = playlists[playlist]
        while True:
            random.shuffle(plst)
            for song in plst:
                await self.play_song(ctx.message, song)

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

    async def play_song(self, message: discord.Message, url, after=lambda: None):
        channel = message.channel
        song_there = os.path.isfile("song.mp3")
        try:
            if song_there:
                os.remove("song.mp3")
        except PermissionError:
            await channel.send("Wait for the current playing music end or use the 'stop' command")
            return
        await channel.send("Getting everything ready, playing audio soon")
        print("Someone wants to play music let me get that ready for them...")
        voice = await Music.get_voice_client(message)
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
        voice.play(discord.FFmpegPCMAudio("song.mp3"), after=after)
        voice.volume = 100
        while voice.is_playing():
            pass

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
