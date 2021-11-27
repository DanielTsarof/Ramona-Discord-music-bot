

        In the forks section, I have added my own code which has a search command added to it

    Could you show me the code? If that is possible?

Here is the link to the fork:
https://gist.github.com/guac420/bc612fd3a35cd00ddc1c221c560daa01

The specific lines of code I have added are:
128-186 the code that searches youtube and displays the first 10 results. This is in the YTDLSource Class
367-372 repeats everything the bot hears into the console (for convenience)
567-593 this is the actual search command that starts the code in the YTDLSource Class
614-620 a command to stop the bot from inside discord

Starting at line 189 I have edited the parse_duration function to my preferences

###########################################################################################################



    I've found that if the bot times out when the queue is empty, it cannot play another song. I was able to fix this by adding the following attribute to the VoiceState class:

    self.exists = True
    And then this above the return statement in the exception of the audio_player_task function:
    self.exists = False
    And finally modify this condition in the Music function get_voice_state:
    if not state or not state.exists

Thank you so much for this comment!!! I was pulling my hair out trying all sorts of different things and all I had to do was scroll down to find this answer....

############################################################################################################

