FROM python:3.6

WORKDIR /app
COPY . /app

RUN pip install discord.py

CMD python bot.py