import socket
import struct

ANY_ADDR = 'ANY_ADDR'
FAKE_LORA_RCV_ADDR = '_lora_fake_addr_1965_'

class CTPendpoint:

    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_addr = ('localhost', 38100)
        self.WAI = '' # what am I: CLIENT or SERVER
        self.client_s = ''
        self.client_address = ''

    def _csend(self, pload, sock, myaddr='', destaddr=''):
        lpload = struct.pack('I', len(pload)) + pload   # adding packet length
        sock.sendall(lpload)
        # original code
        # return rcvr_addr, stats_psent, stats_retrans, FAILED
        return FAKE_LORA_RCV_ADDR, 0, 0, 0

    def _crecv(self, sock, myaddr='', sndraddr=''):
        BUFF_SIZE = 128
        data = []
        chunk = sock.recv(BUFF_SIZE)
        psize = struct.unpack('I', chunk[:4])
        chunk = chunk[4:]
        if (len(chunk)+4) < BUFF_SIZE:
            return chunk, 'snd_addr'
        else:
            data.append(chunk)
            while True:
                chunk = sock.recv(BUFF_SIZE)
                data.append(chunk)
                if len(chunk) < BUFF_SIZE:
                    # either 0 or end of data
                    break
            return b"".join(data), 'snd_addr'


    def connect(self, dest=ANY_ADDR):
        self.WAI = 'CLIENT'
        # Connect the socket to the port where the server is listening
        server_address = self.my_addr
        print('emuloractp: connecting to %s port %s' % server_address)
        self.s.connect(server_address)
        rcvr_addr, stats_psent, stats_retrans, FAILED = self._csend(b"CONNECT", self.s)
        return self.my_addr, rcvr_addr, stats_retrans, FAILED


    def listen(self, sender='ANY_ADDR'):
        self.WAI = 'SERVER'
        # Bind the socket to the port
        server_address = self.my_addr
        print('emuloractp: starting up on %s port %s' % server_address)
        self.s.bind(server_address)
        # Listen for incoming connections
        self.s.listen(1)

        print("emuloractp: listening for...", sender)
        self.client_s, self.client_address = self.s.accept()

        rcvd_data, snd_addr = self._crecv(self.client_s)
        # not necessary but
        snd_addr = self.client_address
        if (rcvd_data==b"CONNECT"):
            return self.my_addr, snd_addr, 0
        else:
            return self.my_addr, snd_addr, -1

    def sendit(self, addr=ANY_ADDR, payload=b''):
        if (self.WAI == 'CLIENT'): 
            rcvr_addr, stats_psent, stats_retrans, FAILED = self._csend(payload, self.s)
        else:
            rcvr_addr, stats_psent, stats_retrans, FAILED = self._csend(payload, self.client_s)
        return rcvr_addr, stats_retrans, FAILED

    def recvit(self, addr=ANY_ADDR):
        if (self.WAI == 'CLIENT'): 
            rcvd_data, snd_addr = self._crecv(self.s)
        else:
            rcvd_data, snd_addr = self._crecv(self.client_s)
        return rcvd_data, snd_addr
