FROM python:3.11.3

RUN pip3 install simple-websocket-server requests

WORKDIR /usr/src
COPY . .

RUN adduser user
USER user

EXPOSE 3400
ENTRYPOINT ["python3", "server.py"]
