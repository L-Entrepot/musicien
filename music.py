import discord
from discord.ext import commands
import os
import random
import asyncio

TOKEN = 'TOKEN'
GUILD_ID = 702856435570311250
VOICE_CHANNEL_ID = 1308106410373943429
TEXT_CHANNEL_ID = 797561414067290152
MUSIC_FOLDER = './musiques'

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='-', intents=intents)

played_songs = []

voice_reconnect_attempts = 0
MAX_RECONNECT_ATTEMPTS = 5

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

@bot.event
async def on_voice_state_update(member, before, after):
    global voice_reconnect_attempts
    if member.id == bot.user.id:
        if before.channel and not after.channel:
            voice_reconnect_attempts = 0
            print("Bot déconnecté du salon vocal, tentative de reconnexion...")
            voice_channel = discord.utils.get(member.guild.voice_channels, id=VOICE_CHANNEL_ID)
            if voice_channel:
                await attempt_reconnect(voice_channel)

async def attempt_reconnect(voice_channel):
    global voice_reconnect_attempts
    if voice_reconnect_attempts >= MAX_RECONNECT_ATTEMPTS:
        print("Nombre maximum de tentatives de reconnexion atteint")
        return

    try:
        voice_reconnect_attempts += 1
        print(f"Tentative de reconnexion {voice_reconnect_attempts}/{MAX_RECONNECT_ATTEMPTS}")
        await join_and_play_random_music(voice_channel)
    except Exception as e:
        print(f"Erreur lors de la reconnexion: {e}")
        await asyncio.sleep(5)
        await attempt_reconnect(voice_channel)

async def join_and_play_random_music(voice_channel):
    global played_songs, voice_reconnect_attempts
    try:
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
                voice_reconnect_attempts = 0
            except Exception as e:
                print(f"Erreur de connexion: {e}")
                raise
        
        await asyncio.sleep(0.5)
        
        if vc.is_playing():
            vc.stop()
        vc.play(discord.FFmpegPCMAudio(file_path), after=lambda e: bot.loop.create_task(play_next(voice_channel)))
    except Exception as e:
        print(f"Erreur dans join_and_play_random_music: {e}")
        if voice_reconnect_attempts < MAX_RECONNECT_ATTEMPTS:
            await asyncio.sleep(5)
            await attempt_reconnect(voice_channel)

async def play_next(voice_channel):
    await join_and_play_random_music(voice_channel)

@bot.command(name='skip')
async def skip(ctx):
    if ctx.channel.id != TEXT_CHANNEL_ID:
        await ctx.send("Cette commande ne peut être utilisée que dans le salon approprié.")
        return

    try:
        vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if not vc or not vc.is_connected():
            await ctx.send("Je ne suis pas connecté à un salon vocal.")
            return

        if vc.is_playing():
            vc.stop()

        await ctx.send("⏩ Passage à la musique suivante...")
    except Exception as e:
        await ctx.send(f"Une erreur est survenue : {str(e)}")
        print(f"Erreur dans la commande skip : {e}")

bot.run(TOKEN)
