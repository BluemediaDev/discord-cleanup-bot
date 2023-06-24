FROM python:3.11

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

VOLUME ["/data"]
ENV DB_PATH="/data/bot.db"

CMD [ "python", "./bot.py" ]