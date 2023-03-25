#!/usr/bin/env python3
import os
import sys

from scapy.all import *
from scapy.layers.inet import _IPOption_HDR

class Request(Packet):
    name = "request"
    fields_desc=[BitField("exists", 0, 8),
                 BitField("reqType", 0, 8),
                 IntField("key1", 0),
                 IntField("key2", 0),
                 IntField("val", 0),
                 BitField("op", 0, 8)]

class Response(Packet):
    name = "response"
    fields_desc=[IntField("ret_val", 0),
                 BitField("same", 0, 8)]

bind_layers(Ether, Request, type = 0x0801)
bind_layers(Request, IP, exists = 1)

bind_layers(TCP, Response, urgptr = 1)

def get_if():
    ifs=get_if_list()
    iface=None
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
    if Request in pkt or Response in pkt:
        pkt.show2()
    #    hexdump(pkt)
        sys.stdout.flush()


def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()
