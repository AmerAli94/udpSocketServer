import random
from random import randrange
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = json.loads(data)
      print(data)
      if addr in clients:
         if data['message'] == 'heartbeat' :
            clients[addr]['lastBeat'] = datetime.now()
            #position is added to data
            clients[addr]['position'] = data['playerPosition']
      else:
         if data['message'] =='connect':
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = {"R": 0, "G": 0, "B": 0}
            clients[addr]['position'] = {'x' : 0, 'y' : 0, 'z' : 0}

            #Create a small list for the players in game (Not for the new client though)
            CurrentPlayers = {"cmd" : 0, "players": []}
            player = {}
            player["id"] = str(addr)
            player["vSpawnPoint"] = clients[addr]['position']
            CurrentPlayers['players'].append(player)
            m = json.dumps(CurrentPlayers)
            for c in clients:
               if c != addr:
                   sock.sendto(bytes(m,'utf8'), (c[0], c[1]))
            #message to send new ID
            m = {"cmd": 3, "ID": str(addr)}
            m2 = json.dumps(m)
            sock.sendto(bytes(m,'utf8'), (addr[0], addr[1]))
            sock.sendto(bytes(m2,'utf8'), (addr[0], addr[1]))

def cleanClients(sock):
   while True:
      CurrentPlayers = {"cmd" : 2, "players": []}
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            player = {}
            player["id"] = str(c)
            CurrentPlayers['players'].append(player)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
      if (CurrentPlayers.get("players") != []):
         clients_lock.acquire()
         m = json.dumps(CurrentPlayers)
         for c2 in clients:
            sock.sendto(bytes(m, 'utf8'), (c2[0],c2[1]))
         print('Dropped Client Successful')
         clients_lock.release()
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         player = {}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['position'] = clients[c]['position']
         GameState['players'].append(player)
      s=json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      clients_lock.release()
      time.sleep(1)


def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
