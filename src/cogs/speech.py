import discord
from discord.ext import commands
from src.handlers.speech_api import SpeechModel
from src.config import IConfig


class MyMessageCog(commands.Cog):
    def __init__(self, bot, config: IConfig):
        self.bot = bot
        self.speech_model = SpeechModel(config.general.openai_token,
                                        config.speech)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        # Если сообщение начинается с упоминания бота
        if message.content.startswith(f'<@!{self.bot.user.id}>') or \
                message.content.startswith(f'<@{self.bot.user.id}>'):
            response = await self.speech_model.ask(message.content.replace(f'<@{self.bot.user.id}>', ''))
            await message.channel.send(response)
            await self.bot.process_commands(message)
