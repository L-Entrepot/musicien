import discord
from discord.ext import commands
import os
import random

TOKEN = 'TOKEN'
GUILD_ID = GUILD_ID
VOICE_CHANNEL_ID = VOICE_CHANNEL_ID
TEXT_CHANNEL_ID = TEXT_CHANNEL_ID
MUSIC_FOLDER = './musiques'

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='+', intents=intents)

played_songs = []

@bot.event
async def on_ready():
    print(f'Bot connecté comme {bot.user}')
    guild = discord.utils.get(bot.guilds, id=GUILD_ID)
    if guild:
        voice_channel = discord.utils.get(guild.voice_channels, id=VOICE_CHANNEL_ID)
        if voice_channel:
            await join_and_play_random_music(voice_channel)

@bot.event
async def on_disconnect():
    print("Bot déconnecté, tentative de reconnexion...")

@bot.event
async def on_resumed():
    print("Connexion rétablie.")

async def join_and_play_random_music(voice_channel):
    global played_songs
    music_files = [f for f in os.listdir(MUSIC_FOLDER) if os.path.isfile(os.path.join(MUSIC_FOLDER, f))]
    if not music_files:
        return
    if len(played_songs) == len(music_files):
        played_songs = []
    remaining_songs = list(set(music_files) - set(played_songs))
    random_music = random.choice(remaining_songs)
    played_songs.append(random_music)
    file_path = os.path.join(MUSIC_FOLDER, random_music)
    print(f"Lecture de {random_music}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=random_music))
    vc = discord.utils.get(bot.voice_clients, guild=voice_channel.guild)
    if not vc or not vc.is_connected():
        try:
            vc = await voice_channel.connect()
        except discord.errors.ConnectionClosed as e:
            print(f"Erreur de connexion: {e}")
            return
    if vc.is_playing():
        vc.stop()
    vc.play(discord.FFmpegPCMAudio(file_path), after=lambda e: bot.loop.create_task(play_next(voice_channel)))

async def play_next(voice_channel):
    await join_and_play_random_music(voice_channel)

@bot.command(name='skip')
async def skip(ctx):
    if ctx.channel.id != TEXT_CHANNEL_ID:
        await ctx.send("Cette commande n'est pas disponible dans ce salon.")
        return
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not vc or not vc.is_connected():
        await ctx.send("Je ne suis pas connecté à un salon vocal.")
        return
    if vc.is_playing():
        vc.stop()
        await ctx.send("⏩ Passage à la musique suivante.")
    else:
        await ctx.send("Aucune musique en cours de lecture.")
    voice_channel = discord.utils.get(ctx.guild.voice_channels, id=VOICE_CHANNEL_ID)
    if voice_channel:
        await play_next(voice_channel)

bot.run(TOKEN)
