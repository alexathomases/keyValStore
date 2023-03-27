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
                 BitField("op", 0, 8),
                 BitField("current", 1, 8)]

class Response(Packet):
    name = "response"
    fields_desc=[IntField("ret_val", 0),
                 BitField("same", 0, 8)]
    def extract_padding(self, p):
        return "", p

class ResponseList(Packet):
    name = "responseList"
    fields_desc = [PacketListField("response", [], Response, length_from=lambda pkt:(40))]

bind_layers(Ether, Request, type = 0x0801)
bind_layers(Request, IP, exists = 1)

bind_layers(TCP, ResponseList, urgptr = 1)
bind_layers(TCP, Response, urgptr = 1)

def expand(x):
    yield x
    while x.payload:
        x = x.payload
        yield x

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
    # if (ResponseList in pkt) and (pkt[IP].ttl < 64):
    #     pkt.show2()
    #     data_layers = [l for l in expand(pkt) if l.name=='response']
    # #    hexdump(pkt)
    #     print(len(data_layers))
    #     for sw in data_layers:
    #         print("Return Value: {}".format(sw.ret_val))
    #     sys.stdout.flush()
    if Request in pkt and pkt[IP].ttl < 64:
        pkt.show2()
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
