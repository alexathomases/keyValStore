#!/usr/bin/env python3
import random
import socket
import sys

from scapy.all import *

class Request(Packet):
    name = "request"
    fields_desc=[BitField("exists", 0, 3),
                 BitField("reqType", 0, 2),
                 BitField("key1", 0, 32),
                 BitField("key2", 0, 32),
                 BitField("val", 0, 32),
                 BitField("op", 0, 3)]

bind_layers(Ether, Request, type = 0x0801)
bind_layers(Request, IP, exists = 1)

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

    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface_receive = ifaces[0]
    print("sniffing on %s" % iface_receive)
    sys.stdout.flush()
    sniff(iface = iface_receive,
          prn = lambda x: handle_pkt(x))

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print("sending on interface %s to %s" % (iface, str(addr)))
    pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')

    # GET request
    if sys.argv[2] == "g":
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        k = int(sys.argv[3])
        pkt2 = pkt / Request(reqType=0, key1=k) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport)
        sendp(pkt2, iface=iface, verbose=False)

    # PUT request
    elif sys.argv[2] == "p":
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        pkt2 = pkt / Request(reqType=1) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport)
        sendp(pkt2, iface=iface, verbose=False)

    # RANGE request
    elif sys.argv[2] == "r":
        # TODO split if necessary
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        pkt2 = pkt / Request(reqType=2) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport)
        sendp(pkt2, iface=iface, verbose=False)

    # SELECT request
    elif sys.argv[2] == "s":
        # TODO split if necessary
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        pkt2 = pkt / Request(reqType=3) / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport)
        sendp(pkt2, iface=iface, verbose=False)


if __name__ == '__main__':
    main()
