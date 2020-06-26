import json
import random
import socket
import string
import sys
import time
import threading

import config
import lsp.loractp as loractp
PROXYPORT = 38180

NOHANDSHAKE = {'IP': 'localhost', 'port': '5001'}
CLOSECONN = b"{'connection': 'CLOSE'}"
# NOHANDSHAKE = {'IP': 'www.grc.upv.es', 'port': '80'}
# from struct import *
# pack('!cc2c4cs', )


def debug_print(*msg):
    print ("tlp_client: ", end = '')
    for m in msg:
        print (m, end = ' ')
    print()

def loractp_send(addr, pload):
    debug_print('loractp_send to {} :  {}'.format(addr, pload))
    try:
        addr, quality, result = ctpc.sendit(addr, pload)
        # print("ACK from {} (quality = {}, result {})".format(addr, quality, result))
    except Exception as e:
        print ("EXCEPTION when sending -> ", e)
        sys.exit()

def loractp_recv(rcvraddr):
    try:
        rcvd_data, addr = ctpc.recvit(rcvraddr)
        return rcvd_data
    except Exception as e:
        print ("EXCEPTION when receiving ->", e)
        sys.exit()


def fromclienttoloractp(sock):
    while True:
        BUFF_SIZE = 128
        data = []
        while True:
            try:  
                chunk = sock.recv(BUFF_SIZE)
            except BrokenPipeError:
                print("BrokenPipeError")
                connection.close()
                sys.exit()
            except Exception as e:
                print ("Exception handling in/out data...", e)
                connection.close()
                sys.exit()

            data.append(chunk)
            if len(chunk) < BUFF_SIZE:
                # either 0 or end of data
                break
        indata = b"".join(data)
        return indata

if __name__ == "__main__":

    ctpc = loractp.CTPendpoint(port=config.serial_port)
    myaddr, rcvraddr, quality, result = ctpc.connect()
    if (result == 0):
        debug_print("connected via LoRa to {} myaddr = {}, quality {}".format(rcvraddr, myaddr, quality))
    else:
        debug_print("failed connection via LoRa to {} myaddr = {}, quality {}".format(rcvraddr, myaddr, quality))

    # Starting socket to receive incoming proxy requests
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', PROXYPORT)
    debug_print('starting up on {} port {}'.format(*server_address))
    sock.bind(server_address)
    sock.listen(1)

    while True:
        # Listen for incoming connections
        debug_print('waiting for a proxy request connection')
        connection, client_address = sock.accept()
        debug_print('got request connection from', client_address)

        # start handshake
        # waiting remote server data in the format:
        # {"IP": <IPaddr>, "port": <port>}  
        try:
            if NOHANDSHAKE:
                handshakedata = json.dumps(NOHANDSHAKE).encode('utf-8')
            else:
                handshakedata = connection.recv(128)
            conndata = json.loads(handshakedata)
            debug_print("handshake data:", conndata["IP"], int(conndata["port"]))
            debug_print('forwarding raw handshakedata', handshakedata)
            loractp_send(rcvraddr, handshakedata)
        except Exception as e:
            print ("Exception during handshake! Data format not correct!", e)
            sys.exit()
        # end handshake

        # handling in/out data in using a request/response pattern    

        while True:
            indata = fromclienttoloractp(connection)
            if indata == CLOSECONN:
                connection.close()
                loractp_send(rcvraddr, CLOSECONN)
                break

            loractp_send(rcvraddr, indata)
            rcvd_data = loractp_recv(rcvraddr)  
            try: 
                connection.sendall(rcvd_data)
            except BrokenPipeError:
                print("BrokenPipeError")
                connection.close()
                break
            except Exception as e:
                print ("Exception handling in/out data...", e)
                connection.close()
                break


