import math
import os
import pickle

# pip install --user git+https://github.com/ytdl-org/youtube-dl.git#branch=master
import discord
from discord.ext import commands

from src.exceptions import VoiceError, YTDLError
from src.handlers.youtube_music import YTDLSource
from src.schemas.music_yt import VoiceState, Song

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

class Music(commands.Cog):

    @staticmethod
    def _path_check(obj, path: str):
        if os.path.exists(path):
            with open(path, 'rb') as f:
                return pickle.load(f)
        return obj

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}
        self.song_blacklist_path = 'song_bl_data.pickle'
        self.user_blacklist_path = 'user_bl_data.pickle'

        self.song_blacklist = self._path_check({}, self.song_blacklist_path)
        self.user_blacklist = self._path_check({}, self.user_blacklist_path)
        # defaul value
        self.subst_url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'

    @staticmethod
    async def _save(object, path: str):
        with open(path, 'wb') as f:
            pickle.dump(object, f)

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        """Joins a voice channel."""
        destination = ctx.author.voice.channel
        print(destination)
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=False)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Summons the bot to a voice channel.
        If no channel was specified, it joins your channel.
        """

        if not channel and not ctx.author.voice:
            raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

        destination = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(destination)
            return

        ctx.voice_state.voice = await destination.connect()

    @commands.command(name='leave', aliases=['disconnect'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        """Clears the queue and leaves the voice channel."""

        if not ctx.voice_state.voice:
            return await ctx.send('Not connected to any voice channel.')

        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, *, volume: int):
        """Sets the volume of the player."""

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        if 0 > volume > 100:
            return await ctx.send('Volume must be between 0 and 100')

        ctx.voice_state.current.source.volume = volume / 100
        await ctx.send('Volume of the player set to {}%'.format(volume))

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        """Displays the currently playing song."""

        await ctx.send(embed=ctx.voice_state.current.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=False)
    async def _pause(self, ctx: commands.Context):
        """Pauses the currently playing song."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=False)
    async def _resume(self, ctx: commands.Context):
        """Resumes a currently paused song."""

        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=False)
    async def _stop(self, ctx: commands.Context):
        """Stops playing song and clears the queue."""

        ctx.voice_state.songs.clear()

        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        """Vote to skip a song. The requester can automatically skip.
        3 skip votes are needed for the song to be skipped.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Not playing any music right now...')

        voter = ctx.message.author
        if voter == ctx.voice_state.current.requester:
            await ctx.message.add_reaction('⏭')
            ctx.voice_state.skip()

        elif voter.id not in ctx.voice_state.skip_votes:
            ctx.voice_state.skip_votes.add(voter.id)
            total_votes = len(ctx.voice_state.skip_votes)

            if total_votes >= 3:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()
            else:
                await ctx.send('Skip vote added, currently at **{}/3**'.format(total_votes))

        else:
            await ctx.send('You have already voted to skip this song.')

    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        """Shows the player's queue.
        You can optionally specify the page to show. Each page contains 10 elements.
        """

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        items_per_page = 10
        pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
            queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

        embed = (discord.Embed(description='**{} tracks:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                 .set_footer(text='Viewing page {}/{}'.format(page, pages)))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        """Shuffles the queue."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        """Removes a song from the queue at a given index."""

        if len(ctx.voice_state.songs) == 0:
            return await ctx.send('Empty queue.')

        ctx.voice_state.songs.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        """Loops the currently playing song.
        Invoke this command again to unloop the song.
        """

        if not ctx.voice_state.is_playing:
            return await ctx.send('Nothing being played at the moment.')

        # Inverse boolean value to loop and unloop.
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    def _search_check(self, search: str, user_name: str):
        if user_name in self.user_blacklist:
            return self.user_blacklist[user_name]
        if search in self.song_blacklist:
            return self.song_blacklist[search]
        return search

    @commands.command(name='play')
    async def _play(self, ctx: commands.Context, *, search: str):
        """Plays a song.
        If there are songs in the queue, this will be queued until the
        other songs finished playing.
        This command automatically searches from various sites if no URL is provided.
        A list of these sites can be found here: https://rg3.github.io/youtube-dl/supportedsites.html
        """

        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        async with ctx.typing():
            try:
                # print(type(ctx.author.name), ctx.author.name)
                search = self._search_check(search, ctx.author.name)
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)

            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                song = Song(source)

                await ctx.voice_state.songs.put(song)
                await ctx.send('Enqueued {}'.format(str(source)))

    @commands.command(name='song_bl')
    async def _song_bl(self, ctx: commands.Context, *, arg: str):
        '''This command allows to add song url to blacklist.
        When trying to play some song from blacklist remove url song is played

        song_bl -flag URl
        flags:
            -ss (set substitute url): set url for substitution
            -a (append): append song url to blacklist
            -r (remove): remove song url from blacklist
            -s (show): show blacklist
            -clear: clears whole blacklist
            '''
        args = arg.split(' ')
        flag = args[0]
        num_args = len(args)
        # append
        if flag == '-a' and num_args == 2:
            if self.subst_url != '':
                self.song_blacklist[args[1]] = self.subst_url
                await self._save(self.song_blacklist, self.song_blacklist_path)
            else:
                await ctx.send('First set the remove url using: song_bl -sr REM_URL')
        # set substitute
        elif flag == '-ss' and num_args == 2:
            self.subst_url = args[1]
        # remove
        elif flag == '-r' and num_args == 2:
            del self.song_blacklist[args[1]]
            await self._save(self.song_blacklist, self.song_blacklist_path)
            await ctx.send(f'url: {args[1]} removed')
        # show
        elif flag == '-s':
            out_str = ''
            for url, rem_url in self.song_blacklist.items():
                out_str += f'{url} -> {rem_url}\n'
            if out_str:
                await ctx.send(out_str)
            else:
                await ctx.send('Song blacklist is empty')
        # clear blacklist
        elif flag == '-clear':
            self.song_blacklist = {}
            await self._save(self.song_blacklist, self.song_blacklist_path)
            await ctx.send('blacklist cleared')

        else:
            raise commands.CommandError('Invalid command')

        # print(self.song_blacklist)

    @commands.command(name='user_bl')
    async def _user_bl(self, ctx: commands.Context, *, arg: str):
        '''This command allows to add user name to blacklist.
        When trying to play some song from this user remove url song is played

        user_bl -flag*user_id
        flags:
            -ss (set substitute url): set url for substitution
            -a (append): append user_name to blacklist
            -r (remove): remove user_name from blacklist
            -s (show): show blacklist
            -clear: clears whole blacklist
            '''
        args = arg.split('*')
        flag = args[0]
        num_args = len(args)
        # append
        if flag == '-a' and num_args == 2:
            if self.subst_url != '':
                self.user_blacklist[str(args[1])] = self.subst_url
                await self._save(self.user_blacklist, self.user_blacklist_path)
            else:
                await ctx.send('First set the remove url using: user_bl -sr REM_URL')
        # set substitute
        elif flag == '-ss' and num_args == 2:
            self.subst_url = args[1]
        # remove
        elif flag == '-r' and num_args == 2:
            del self.user_blacklist[str(args[1])]
            await self._save(self.user_blacklist, self.user_blacklist_path)
            await ctx.send(f'user: {args[1]} removed from blacklist')
        # show
        elif flag == '-s':
            out_str = ''
            for url, rem_url in self.user_blacklist.items():
                out_str += f'{url} -> {rem_url}\n'
            if out_str:
                await ctx.send(out_str)
            else:
                await ctx.send('User blacklist is empty')
        # clear blacklist
        elif flag == '-clear':
            self.user_blacklist = {}
            await self._save(self.user_blacklist, self.user_blacklist_path)
            await ctx.send('blacklist cleared')

        else:
            raise commands.CommandError('Invalid command')

        # print(self.user_blacklist)

    @commands.command(name='ramona')
    async def _ramona(self, ctx: commands.Context):
        '''Ramona
        '''
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)

        source = await YTDLSource.create_source(ctx, 'https://www.youtube.com/watch?v=fdbOkE9AwRY', loop=self.bot.loop)
        song = Song(source)
        await ctx.voice_state.songs.put(song)

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('You are not connected to any voice channel.')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Bot is already in a voice channel.')
