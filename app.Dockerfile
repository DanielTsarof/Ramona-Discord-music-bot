FROM python:3.10-slim

WORKDIR /app

RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y ffmpeg

#RUN apt-get update && \
#    apt-get install -y --no-install-recommends gcc \

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/ytdl-org/youtube-dl.git

COPY src/ ./src
COPY config.yaml .
COPY main.py .

CMD ["python", "main.py"]
