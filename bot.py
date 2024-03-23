import discord
from discord.ext import commands
from youtubesearchpython import VideosSearch
from pytube import YouTube
import asyncio
import os

intents = discord.Intents.all()
intents.members = True

client = commands.Bot(command_prefix='.', intents=intents)
ffmpeg_options = {'options':'-vn'}

songs_queue = asyncio.Queue()
is_playing = False
is_paused = False

@client.command(name = 'play',aliases = ['p'], help='Toca uma música pelo youtube.')
async def play(ctx, *args):
    query = ' '.join(args)
    voice_channel = ctx.author.voice.channel

    if not voice_channel:
        ctx.send('Entre em um canal de voz primeiro.')
        return

    videosSearch = VideosSearch(query, limit=1)
    results = videosSearch.result()

    if not results["result"]:
        await ctx.send("Nenhum resultado encontrado.")
        return
    
    if query.startswith('https://youtu.be/'):
       query = query.replace('https://youtu.be/', 'https://www.youtube.com/')

    if query.startswith('https://www.youtube.com/'):
        url = query

    else:
        url = results["result"][0]["link"]
    video = YouTube(url)   

    await ctx.send(f'Música {video.title} adicionado a fila.') 

    audio_stream = video.streams.filter(only_audio=True).first()
    save_path = r'C:\\Users\\pudim\\Music\\Bot'
    audio_stream.download(output_path=save_path)

    file_name = audio_stream.default_filename
    file_path = os.path.join(save_path, file_name)

    if ctx.voice_client and ctx.voice_client.is_playing() and ctx.voice_client.is_connected():
        await songs_queue.put((file_path, ctx))

    await songs_queue.put((file_path, ctx))

    if not is_playing:
        await play_next()

async def play_next():
    global is_playing
    
    while not songs_queue.empty():
        is_playing = True
        file_path, ctx = await songs_queue.get()

    if not ctx.voice_client:  
            voice_channel = ctx.author.voice.channel
            await voice_channel.connect()
    
    ctx.voice_client.play(discord.FFmpegPCMAudio(file_path, **ffmpeg_options), after=lambda e: asyncio.run(play_next()))

    while ctx.voice_client.is_playing():
         await asyncio.sleep(1)

    is_playing = False

@client.command(name = 'skip', aliases = ['s'], help = 'Pula a música atual')
async def skip(ctx):
    global is_playing

    if is_playing:
        ctx.send('Música pulada.')
        ctx.voice_client.stop()
        await play_next()
    else:
        ctx.send('Não estou tocando música no momento.')


@client.event
async def on_ready():
    print(f"Logado como {client.user.name}") 
    await client.change_presence(activity=discord.Game(name='.help'))

client.run('')
