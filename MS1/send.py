#!/usr/bin/env python3
import random
import socket
import sys

from scapy.all import *

class Request(Packet):
    name = "request"
    fields_desc=[BitField("bool", 0, 2),
                 BitField("reqType", 0, 2)]

bind_layers(Ether, Request, type = 0x0801)
bind_layers(Request, IP, bool = 0)

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

def main():

    if len(sys.argv)<4:
        print('pass 2 arguments: <destination> "<message>" <o/n/p>')
        exit(1)

    addr = socket.gethostbyname(sys.argv[1])
    iface = get_if()

    print("sending on interface %s to %s" % (iface, str(addr)))
    pkt =  Ether(src=get_if_hwaddr(iface), dst='ff:ff:ff:ff:ff:ff')

    # Send a normal packet, per-flow load balancing
    if sys.argv[3] == "f":
        for size in [10, 106, 200]:
            payload = '\0x00' * size
            for _ in range(100):
                tcp_sport = random.randint(49152,65535)
                tcp_dport = random.randint(1000, 2000)
                pkt2 = pkt / First() / IP(dst=addr) / TCP(dport=tcp_dport, sport=tcp_sport) / payload
                sendp(pkt2, iface=iface, verbose=False)

    # Send a normal packet, per-packet load balancing
    elif sys.argv[3] == "o":
        #for size in [10, 106, 200]:
        for size in [10]:
            payload = '\0x00' * size
            pkts = []
            for i in range(100):
                tcp_sport = random.randint(49152,65535)
                tcp_dport = random.randint(1000, 2000)
                pkt2 = pkt / First(per_packet=1) / IP(dst=addr, id=i) / TCP(dport=tcp_dport, sport=tcp_sport) / payload
                pkts.append(pkt2)
            sendp(pkts, iface=iface, verbose=False)

    # Send a probe/query packet
    elif sys.argv[3] == "p":
        pkt = pkt / Probe() / IP(dst=addr) / TCP(dport=1234, sport=random.randint(49152,65535)) / sys.argv[2]
        pkt.show2()
        sendp(pkt, iface=iface, verbose=False)


if __name__ == '__main__':
    main()
