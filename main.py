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
from src.cogs.speech import MyMessageCog
from src.config import get_config

# Silence useless bug reports messages
youtube_dl.utils.bug_reports_message = lambda: 'error'

if __name__ == '__main__':
    config = get_config('config.yaml')
    TOKEN = config.general.discord_token
    intents = discord.Intents.default()  # Подключаем "Разрешения"
    intents.message_content = True
    bot = commands.Bot('|', description='Yet another music bot.', intents=intents)


    async def setup():
        await bot.wait_until_ready()
        await bot.add_cog(Music(bot))
        await bot.add_cog(MyMessageCog(bot, config))


    @bot.event
    async def on_ready():
        bot.loop.create_task(setup())
        print('Logged in as:\n{0.user.name}\n{0.user.id}'.format(bot))


    bot.run(TOKEN)
