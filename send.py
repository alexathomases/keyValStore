#!/usr/bin/env python3
import random
import socket
import sys

from scapy.all import *

class Request(Packet):
    name = "request"
    fields_desc=[BitField("exists", 0, 8),
                 BitField("reqType", 0, 8),
                 IntField("key1", 0),
                 IntField("key2", 0),
                 IntField("val", 0),
                 BitField("op", 0, 8)]

bind_layers(Ether, Request, type = 0x0801)
bind_layers(Request, IP, exists = 1)

class Response(Packet):
    name = "response"
    fields_desc=[IntField("ret_val", 0)]

bind_layers(TCP, Response, urgptr = 1)

def get_if():
    ifs=get_if_list()
    iface=None # "h1-eth0"
    for i in get_if_list():
        if "eth0" in i:
            iface=i
            break;
    if not iface:
        print("Cannot find eth0 interface")
        exit(1)
    return iface

def handle_pkt(pkt):
    print("got a packet")
    if Ether in pkt:
        pkt.show2()
    #    hexdump(pkt)
        sys.stdout.flush()

def main():

    if len(sys.argv)<4:
        print('pass 2 arguments: <destination> <g/p/r/s> "<message>" ')
        exit(1)

    # ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    # iface_receive = ifaces[0]
    # print("sniffing on %s" % iface_receive)
    # sys.stdout.flush()
    # sniff(iface = iface_receive,
    #       prn = lambda x: handle_pkt(x))

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print("sending on interface %s to %s" % (iface, str(addr)))
    pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')

    # GET request
    if sys.argv[2] == "g":
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        kv_list = sys.argv[3].split()
        if len(kv_list) != 1:
            print('GET requires 1 key')
            exit(1)
        k = int(sys.argv[3])
        pkt2 = pkt / Request(reqType=0, key1=k) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1) / Response()
        # pkt2.show2()
        sendp(pkt2, iface=iface, verbose=False)

    # PUT request
    elif sys.argv[2] == "p":
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        kv_list = sys.argv[3].split()
        if len(kv_list) != 2:
            print('PUT requires 1 key and 1 value')
            exit(1)
        k1 = int(kv_list[0])
        v = int(kv_list[1])
        pkt2 = pkt / Request(reqType=1, key1=k1, val=v) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1) / Response()
        # pkt2.show2()
        sendp(pkt2, iface=iface, verbose=False)

    # RANGE request
    elif sys.argv[2] == "r":
        # TODO split if necessary
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        pkt2 = pkt / Request(reqType=2) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1) / Response()
        sendp(pkt2, iface=iface, verbose=False)

    # SELECT request
    elif sys.argv[2] == "s":
        # TODO split if necessary
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        pkt2 = pkt / Request(reqType=3) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1) / Response()
        sendp(pkt2, iface=iface, verbose=False)


if __name__ == '__main__':
    main()
