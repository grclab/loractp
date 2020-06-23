import json
import random
import socket
import string
import sys
import time
import threading

import emuloractp
PROXYPORT = 38180


def debug_print(*msg):
    print ("tlp_server: ", end = '')
    for m in msg:
        print (m, end = ' ')
    print()

def loractp_send(addr, pload):
    try:
        addr, quality, result = ctpc.sendit(addr, pload)
        # print("ACK from {} (quality = {}, result {})".format(addr, quality, result))
    except Exception as e:
        print ("EXCEPTION when sending -> ", e)
        sys.exit()

def loractp_recv(rcvraddr):
    try:
        rcvd_data, addr = ctpc.recvit(rcvraddr)
        # print("got {} from {}".format(rcvd_data, addr))
        return rcvd_data
    except Exception as e:
        print ("EXCEPTION when receiving ->", e)
        sys.exit()

def fromservertoloractp(sock):
    while True:
        BUFF_SIZE = 128
        data = []
        while True:
            chunk = sock.recv(BUFF_SIZE)
            data.append(chunk)
            if len(chunk) < BUFF_SIZE:
                # either 0 or end of data
                break
        indata = b"".join(data)
        # debug_print('received {!r}'.format(indata))

        # debug_print('sending ', bdata)
        loractp_send(rcvraddr, indata)


if __name__ == "__main__":

    ctpc = emuloractp.CTPendpoint()
    myaddr, rcvraddr, status = ctpc.listen()
    if (status == 0):
        debug_print("connection from {} to me ({})".format(rcvraddr, myaddr))
    else:
        debug_print("failed connection from {} to me ({})".format(rcvraddr, myaddr))

    # start handshake
    # waiting remote server data in the format:
    # {"IP": <IPaddr>, "port": <port>}  
    rcvd_data = loractp_recv(rcvraddr)
    debug_print("got {}".format(rcvd_data))
    conndata = json.loads(rcvd_data)
    debug_print("handshake data:", conndata["IP"], int(conndata["port"]))

    # Connect the socket to the request IP and port
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (conndata["IP"], int(conndata["port"]))
        debug_print('connecting to {} port {}'.format(*server_address))
        sock.connect(server_address)
        debug_print("CONNECTED")
        # loractp_send(rcvraddr, b"CONNECTED\n")
    except Exception as e:
        debug_print("Exception connecting to requested server!", e)
        debug_print("FAILED")
        # loractp_send(rcvraddr, b"FAILED\n")
    # end handshake

    # handling data in two seprate threads    
    t = threading.Thread(target=fromservertoloractp, args=(sock,))
    t.start()
    while True:
        rcvd_data = loractp_recv(rcvraddr)
        sock.sendall(rcvd_data)