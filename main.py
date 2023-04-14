# -*- coding: utf-8 -*-

"""
Requirements:
Python 3.7+
pip install -U discord.py pynacl youtube-dl
You also need FFmpeg in your PATH environment variable or the FFmpeg.exe binary in your bot's directory on Windows.
"""

# pip install --user git+https://github.com/ytdl-org/youtube-dl.git#branch=master
import discord
import youtube_dl
from discord.ext import commands

from src.cogs.music import Music

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: 'error'

# Add your token here
TOKEN = 'OTEwNDYwNzg1Njk0NzM2NDM0.GKdPjr.NsOp6vtHuZXEQf0aHLtuiAawdWnhHC6xyBOvUM'

if __name__ == '__main__':
    intents = discord.Intents.default()  # Подключаем "Разрешения"
    intents.message_content = True
    bot = commands.Bot('|', description='Yet another music bot.', intents=intents)


    async def setup():
        await bot.wait_until_ready()
        await bot.add_cog(Music(bot))


    @bot.event
    async def on_ready():
        bot.loop.create_task(setup())
        print('Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))


    bot.run(TOKEN)
