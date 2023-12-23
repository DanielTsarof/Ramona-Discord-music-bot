# Ramona music bot

!!! if you have "ERROR: Unable to extract uploader iderror"
 error try to install youtube-dl directly from github repository:

	`pip uninstall youtube-dl`
	pip install git+https://github.com/ytdl-org/youtube-dl.git

## example config.yaml file:

    general:
      discord_token: '...'
      openai_token: '...'

    speech:
      model: 'gpt-3.5-turbo'
      temperature: 1
      ans_max_length: 70
      max_tokens: 1500
      prompt: 'ramona-classic.txt'

The project continues to improve.

to install pyaudio:

    sudo apt install portaudio19-dev
    pip install PyAudio
