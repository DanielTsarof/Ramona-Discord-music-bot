import discord
from discord.ext import commands
from src.handlers.speech_api import SpeechModel
from src.config import IConfig


class Speech(commands.Cog):
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

    @commands.command(name='personality')
    async def _song_bl(self, ctx: commands.Context, *, arg: str):
        '''This command allows to change or manage bot personality (watch help)

        personality -l
        personality -s name
        flags:
            -l (list): shows all personalities
            -s (set): choose new personality
            '''
        args = arg.split(' ')
        flag = args[0]
        num_args = len(args)
        # list
        if flag == '-l' and num_args == 1:
            await ctx.send(self.speech_model.show_personalities())
        # set
        elif flag == '-s' and num_args == 2:
            name = args[1]
            try:
                self.speech_model.change_prompt(name)
                await ctx.send(f'Bot personality changed to {name}. Have fun!')
            except FileNotFoundError:
                await ctx.send('Invalid personality name')
        else:
            raise commands.CommandError('Invalid command')
