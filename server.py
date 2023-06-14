from simple_websocket_server import WebSocketServer, WebSocket
import json
import random
import logging as log
from enum import Enum 

def generate_client_id():
    return str(random.randint(0, 10**5))

def send_obj_message(client, message):
    client.send_message(json.dumps(message, separators=(',', ':')))

class MessageType(Enum):
    CONNECTED = 0
    NEW_CLIENT_CONNECTED = 1
    CLIENT_DISCONNECTED = 2
    SOURCE_CHANGE = 3
    CURSOR_MOVE = 4
    CLIENT_HANDSHAKE = 999

class Session:
    def __init__(self, projectId):
        self.projectId = projectId
        self.clientToClientId = {}
        self.cursorsPositions = {}

        # TODO: Here we need to pull initial document state from RM. 
        self.document = []
        
        log.info(f'[{projectId}] New session initialized.')
    
    def __del__(self):
        log.info(f'[{self.projectId}] Clossing session.')
    
    def get_clients_count(self):
        return len(self.clientToClientId)
    
    def add_client(self, new_client):
        new_clientId = generate_client_id()
        self.clientToClientId[new_client] = new_clientId
        
        newClient_message = {}
        newClient_message['clientId'] = new_clientId
        newClient_message['type'] = MessageType.NEW_CLIENT_CONNECTED.value

        for client, clientId in self.clientToClientId.items():
            if clientId != new_clientId:
                send_obj_message(client, newClient_message)

        hello_message = {}
        hello_message['document'] = self.document
        hello_message['clientId'] = new_clientId
        hello_message['clientsConnectedIds'] = list(self.clientToClientId.values())
        hello_message['cursorsPositions'] = self.cursorsPositions
        hello_message['type'] = MessageType.CONNECTED.value
        
        send_obj_message(new_client, hello_message)

        log.info(f'[{self.projectId}] Added new client {new_client.address} with clientId {new_clientId}.')

    def remove_client(self, client):
        clientId = self.clientToClientId[client]

        del self.clientToClientId[client]

        if  clientId in self.cursorsPositions:
            del self.cursorsPositions[clientId]

        disconnected_message = {}
        disconnected_message['clientId'] = clientId
        disconnected_message['type'] = MessageType.CLIENT_DISCONNECTED.value
        
        for client in self.clientToClientId:
            send_obj_message(client, disconnected_message)
        
        log.info(f'[{self.projectId}] {clientId} disconnected.')
    
    def handle_document_delta(self, message):
        if message['isBackspace']:
            position = message['position']
            self.document = [char for char in self.document if char['id'] != position]
        else:
            position = message['position']
            char = message['char']
            
            if position == None:
                self.document.insert(0, char)
            else:
                idx, = (i for i, val in enumerate(self.document) if val['id'] == position)
                self.document.insert(idx+1, char)
    
    def handle_message(self, sender_client, message):
        sender_clientId = self.clientToClientId[sender_client]

        log.info(f'[{self.projectId}][{sender_clientId}] {message}.')
        
        if message['type'] == MessageType.SOURCE_CHANGE.value:
            self.handle_document_delta(message)
        
        for client, clientId in self.clientToClientId.items():
            if clientId != sender_clientId:
                send_obj_message(client, message)

class SimpleChat(WebSocket):
    def handle(self):
        global clientToProjectId
        global sessions 

        message = json.loads(self.data)

        if message['type'] == MessageType.CLIENT_HANDSHAKE.value:
            projectId = message['projectId']
                
            if projectId not in sessions:
                sessions[projectId] = Session(projectId)
            
            clientToProjectId[self] = projectId
            sessions[projectId].add_client(self)
        else:
            projectId = clientToProjectId[self]
            sessions[projectId].handle_message(self, message)

    def connected(self):
        # Handling new client has been moved to handle method on CLIENT_HANDSHAKE message.
        return

    def handle_close(self):
        global clientToProjectId
        global sessions 
        
        projectId = clientToProjectId[self]
        sessions[projectId].remove_client(self)

        if sessions[projectId].get_clients_count() == 0:
            del sessions[projectId]

log.getLogger().setLevel(log.INFO)

clientToProjectId = {}
sessions = {}

server = WebSocketServer('0.0.0.0', 3400, SimpleChat)

log.info('[global] The collaboration server is listening on port 3400.')

server.serve_forever()

