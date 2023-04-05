import discord

from discord.ext import commands
from discord import FFmpegPCMAudio
import os
import io
import asyncio
import aiohttp
from pydub import AudioSegment
from google.cloud import speech_v1p1beta1 as speech
from google.oauth2 import service_account
import io
from google.cloud import storage
import nacl.secret
import nacl.utils
from typing import Tuple
import pyaudio
import wave

import numpy as np
p = pyaudio.PyAudio()
if not discord.opus.is_loaded():
    discord.opus.load_opus("/opt/homebrew/Cellar/opus/1.3.1/lib/libopus.dylib")


# Discord bot token
TOKEN = 'MTA5MDY5Mjk2NjY1NTQ2NzU0MA.GsjN7W.R5EB-7gtkoUyyV1Z7ld5TgQg99annFVo51d9EY'

# Google Cloud credentials
CREDENTIALS_FILE = '/Users/ddh/Downloads/ferrous-cursor-382416-e82b6801430d.json'
credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_FILE)

# Language codes supported by Google Cloud Speech-to-Text
LANGUAGES = {
    'en-US': 'English (United States)',
    'es-ES': 'Spanish (Spain)',
    'fr-FR': 'French (France)',
    'de-DE': 'German (Germany)',
    'it-IT': 'Italian (Italy)',
    'ja-JP': 'Japanese (Japan)',
    'ko-KR': 'Korean (South Korea)',
    'pt-BR': 'Portuguese (Brazil)',
    'ru-RU': 'Russian (Russia)',
    'zh-CN': 'Chinese (Simplified, China)',
    'zh-TW': 'Chinese (Traditional, Taiwan)'
}

# Maximum recording duration in seconds
MAX_RECORDING_DURATION = 300

# Voice channels where the bot is allowed to join and record
ALLOWED_CHANNELS = ['voice_channel_1', 'voice_channel_2']

# Google Cloud Speech-to-Text configuration
client = speech.SpeechClient(credentials=credentials)
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code="en-US",
    enable_word_time_offsets=True
)
connections = {}

async def start_recording(ctx):
    # Check if the bot is already recording
    if ctx.voice_client and ctx.voice_client.listen():
        await ctx.send('I am already recording!')
        return

    # Check if the user is in a voice channel
    if not ctx.author.voice:
        await ctx.send('You are not in a voice channel.')
        return

    # Check if the bot is allowed to join the user's voice channel
    if ctx.author.voice.channel.name not in ALLOWED_CHANNELS:
        await ctx.send('I am not allowed to join this voice channel.')
        return

    # Join the user's voice channel
    print("1")
    # await ctx.author.voice.channel.connect()
    # print("3")
    # # Start recording the user's audio
    # ctx.bot.voice_client = ctx.guild.voice_client
    # print("4")
   
    # source = discord.PCMVolumeTransformer(ctx.bot.voice_client.listen())
    # print("5")
    # audio_data = io.BytesIO()
    # while True:
    #     try:
    #         # Read audio data from the stream and write it to a buffer
    #         data = await asyncio.wait_for(source.read(), timeout=10.0)
    #         audio_data.write(data)
    #     except asyncio.TimeoutError:
    #         # Stop listening if there is no audio data for 10 seconds
    #         break

    voice = ctx.author.voice

    if not voice:
        await ctx.send("You aren't in a voice channel!")

    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.
    
    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx  # The channel to disconnect from.
    )
   

    # Send a message to the user
    await ctx.send('I am now recording your audio. Say something!')

    # # Wait for the maximum recording duration
    # await asyncio.sleep(MAX_RECORDING_DURATION)

    # # Stop recording the user's audio
    # ctx.voice_client.is_recording = False
    # ctx.voice_client.stop()

    # # Process the user's audio
    # await process_audio(ctx)

async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):  # Our voice client already passes these in.
    recorded_users = [  # A list of recorded users
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]  # List down the files.
    f=[audio for user_id, audio in sink.audio_data.items()]
    # Pass the audio to Google Cloud Speech-to-Text
    # Convert the audio to a suitable format for Google Cloud Speech-to-Text
    # audio = AudioSegment.from_file(io.BytesIO(), format='ogg')
    # raw_audio_data = f.data
    # Create a storage client
    storage_client = storage.Client(credentials=credentials)

    # Replace with your own GCS bucket name and audio file path
    bucket_name = 'discord_bot123'
    
    
    trans=[]
    for user_id, audio in sink.audio_data.items():
        
        

        # Stop recording and clean up
        await sink.vc.disconnect()
       
        

        
        # audio_segment = AudioSegment.from_file(, format=sink.encoding)
        audio = AudioSegment.from_file(audio.file, format='wav')
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        fln=f'{user_id}-audqw321.wav'
        audio = audio.export(fln,format='wav')
        if os.path.getsize(fln)!=0:
            # Pass the audio to Google Cloud Speech-to-Text
            audio_data = audio.read()
            # Create a blob (object) for the audio file
            bucket = storage_client.get_bucket(bucket_name)
            nfln=f'new-{fln}'
            blob = bucket.blob(nfln)

            # Upload the audio file to GCS
            with open(fln, 'rb') as a:
                blob.upload_from_file(a)
            
            gri=f'gs://discord_bot123/{nfln}'
            audio_config = speech.RecognitionAudio(uri=gri)

            # audio_config = speech.RecognitionAudio(content=audio_data)
            response = client.long_running_recognize(config=config, audio=audio_config)
            res = response.result(timeout=90)
            
            
                
                # time_stamps.append(result.alternatives[0].words.start_time)
            

            # Combine the transcripts into a single string
            # Post the transcript to a text channel
            text_channel = discord.utils.get(channel.guild.text_channels, name='transcripts')
            

            # Post the time stamps to a text channel
        


            await text_channel.send(f'{recorded_users} spoke at:\n ')
            # Get the transcripts and time stamps
            transcripts = []
            time_stamps = []
            for result in res.results:
                transcript = result.alternatives[0]
                print(transcript)
                await text_channel.send('Transcript: {}'.format(transcript.transcript))

                for word_info in transcript.words:
                    word=word_info.word
                    st=word_info.start_time
                    et=word_info.end_time
                    await text_channel.send('Word: {}, start_time: {}, end_time: {}'.format(word, st.seconds,et.seconds))
            await text_channel.send(f"finished recording audio for: {', '.join(recorded_users)}.", files=files)  # Send a message with the accumulated files.

           

async def stop_recording(ctx):
# Check if the bot is currently recording
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        del connections[ctx.guild.id]  # Remove the guild from the cache.
        # await ctx.delete()  # And delete.
    else:
        await ctx.send("I am currently not recording here.")  # Respond with this if we aren't recording.

async def change_language(ctx, language_code):
    # Check if the language code is valid
    if language_code not in LANGUAGES:
        await ctx.send(f'Invalid language code. The supported languages are: {", ".join(LANGUAGES)}.')
        return
    
    # Update the language code in the Google Cloud Speech-to-Text configuration
    config.language_code = language_code
    
    # Send a confirmation message
    await ctx.send(f'The language code has been updated to {LANGUAGES[language_code]}.')





async def run_bot():
    # Create a Discord client
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents)

    @bot.event
    async def on_ready():
        print("Connected as: {0.user}".format(bot))
        text_channel = discord.utils.get(bot.guilds[0].text_channels, name='transcripts')
        await text_channel.send(f'{bot.user.mention} is ready to record!')

    @bot.command(name='start-recording')
    async def start_recording_command(ctx):
        await ctx.send("Starting recording!")
        await start_recording(ctx)

    @bot.command(name='hello')
    async def hello(ctx):
         await ctx.send(f'HELLO!')

    @bot.command(name='stop-recording')
    async def stop_recording_command(ctx):
        await stop_recording(ctx)

    @bot.command(name='change-language')
    async def change_language_command(ctx, language_code):
        await change_language(ctx, language_code)

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        print(f"{message.author}: {message.content}")
        await bot.process_commands(message)

    # Run the bot
    await bot.start(TOKEN)

# Run the bot
asyncio.run(run_bot())



