from simple_websocket_server import WebSocketServer, WebSocket

class SimpleChat(WebSocket):
    def handle(self):
        print(f'[MESSAGE][{self.address}] {self.data}')
        for client in clients:
            if client != self:
                client.send_message(self.data)

    def connected(self):
        print(f'[CONNECTED] {self.address}')
        for client in clients:
            client.send_message(f'[CONNECTED] {self.address}')
        self.send_message(f'[HELLO] {len(clients)}')
        clients.append(self)

    def handle_close(self):
        clients.remove(self)
        print(f'[CLOSED] {self.address}')
        for client in clients:
            client.send_message(f'[CLOSED] {self.address}')

clients = []

server = WebSocketServer('', 6789, SimpleChat)
server.serve_forever()
