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
                 BitField("current", 1, 32),
                 BitField("small_key", 0, 8),
                 BitField("ping", 0, 8),
                 IntField("rando", 0),
                 BitField("pingpong_diff", 0, 32)]

class Response(Packet):
    name = "response"
    fields_desc=[IntField("ret_val", 0),
                 BitField("same", 1, 8)]
    # def extract_padding(self, p):
    #     return "", p

# class ResponseList(Packet):
#     name = "responseList"
#     fields_desc = [PacketListField("response", [], Response, length_from=lambda pkt:(40))]

bind_layers(Ether, Request, type = 0x0801)
bind_layers(Request, IP, exists = 1)

bind_layers(TCP, Response, urgptr = 1)
bind_layers(Response, Response, same = 1)

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
    if (Request in pkt and (pkt[IP].ttl < 64)):
        print("response in pkt")
        # pkt.raw()
        # pkt.show2()
        if pkt[Request].ping != 2:
            data_layers = [l for l in expand(pkt) if l.name=='response']
            ret_array = []
            for sw in data_layers:
                ret_array.insert(0, sw.ret_val)
            for ret in ret_array:
                print("Return Value: {}".format(ret))
        if pkt[Request].pingpong_diff > 10 and pkt[Request].ping == 2:
            print("PING request detected potential switch failure!")
            print("Difference between pings/pongs: " + str(pkt[Request].pingpong_diff))
        sys.stdout.flush()


def main():
    ifaces = [i for i in os.listdir('/sys/class/net/') if 'eth0' in i]
    iface = ifaces[0]
    print("sniffing on %s" % iface)
    sys.stdout.flush()
    sniff(iface = iface,
          prn = lambda x: handle_pkt(x))

if __name__ == '__main__':
    main()
