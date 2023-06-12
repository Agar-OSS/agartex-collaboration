from simple_websocket_server import WebSocketServer, WebSocket
import json
import random
import logging as log

class SimpleChat(WebSocket):
    def handle(self):
        global document
        global clients

        clientId = clients[self]
        message = json.loads(self.data) 

        log.info(f'[MESSAGE][{clientId}] {message}')
    
        # document delta
        if message['type'] == 3:
            if message['isBackspace']:
                position = message['position']
                document = [char for char in document if char['id'] != position]
            else:
                position = message['position']
                char = message['char']

                if position == None:
                    document.insert(0, char)
                else:
                    idx, = (i for i, val in enumerate(document) if val['id'] == position)
                    document.insert(idx+1, char)

        for client in clients:
            if client != self:
                client.send_message(self.data)

    def connected(self):
        global clientsConnectedIds
        global clients
        global cursorsPositions

        clientId = str(random.randint(0, 10**5))

        log.info(f'[CONNECTED] {clientId}')

        newClient_message = {}
        newClient_message['clientId'] = clientId
        newClient_message['type'] = 1
        
        for client in clients:
            client.send_message(json.dumps(newClient_message, separators=(',', ':')))
        
        clientsConnectedIds.append(clientId)
        cursorsPositions[clientId] = None
        
        hello_message = {}
        hello_message['document'] = document
        hello_message['clientId'] = clientId
        hello_message['clientsConnectedIds'] = clientsConnectedIds
        hello_message['cursorsPositions'] = cursorsPositions
        hello_message['type'] = 0
        self.send_message(json.dumps(hello_message, separators=(',', ':')))

        clients[self] = clientId

    def handle_close(self):
        global clientsConnectedIds
        global clients
        global cursorsPositions

        clientId = clients[self]
        del clients[self]

        disconnected_message = {}
        disconnected_message['clientId'] = clientId
        disconnected_message['type'] = 2
        
        for client in clients:
            client.send_message(json.dumps(disconnected_message, separators=(',', ':')))
        
        clientsConnectedIds.remove(clientId)
        del cursorsPositions[clientId]

        log.info(f'[CLOSED] {clientId}')

log.getLogger().setLevel(log.INFO)

document = []
clientsConnectedIds = []
clients = {}
cursorsPositions = {}

server = WebSocketServer('0.0.0.0', 3400, SimpleChat)

log.info('Listening on port 3400')

server.serve_forever()

