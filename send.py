#!/usr/bin/env python3
import random
import socket
import sys
import math

from scapy.all import *

#constant for determining how many keys can be included in range/select requests
ttlConst = 64
maxKeysPerPacket = ttlConst - 2


class Request(Packet):
    name = "request"
    fields_desc=[BitField("exists", 0, 8),
                 BitField("reqType", 0, 8),
                 IntField("key1", 0),
                 IntField("key2", 0),
                 IntField("val", 0),
                 BitField("op", 0, 8),
                 BitField("current", 1, 8),
                 BitField("small_key", 0, 8),
                 BitField("ping", 0, 8),
                 IntField("rando", 0),
                 IntField("pingpong_diff", 0)]

bind_layers(Ether, Request, type = 0x0801)
bind_layers(Request, IP, exists = 1)

class Response(Packet):
    name = "response"
    fields_desc=[IntField("ret_val", 0),
                 BitField("same", 1, 8)]

# class ResponseList(Packet):
#     name = "responseList"
#     fields_desc = [PacketListField("response", [], Response)]

bind_layers(TCP, Response, urgptr = 1)
bind_layers(Response, Response, same = 1)

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
    rand_tag = random.randint(0, 9)
    print("RAND: ", rand_tag)

    # GET request
    if sys.argv[2] == "g":
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        kv_list = sys.argv[3].split()
        if len(kv_list) != 1:
            print('GET requires 1 key')
            exit(1)
        k = int(sys.argv[3])
        if k < 512:
            small = 1
        else:
            small = 0
        pkt2 = pkt / Request(reqType=0, key1=k, current=1, small_key=small, rando=rand_tag) / IP(dst=addr, ttl = ttlConst) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1) / Response()
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
        if k1 < 512:
            small = 1
        else:
            small = 0
        pkt2 = pkt / Request(reqType=1, key1=k1, val=v, current=1, small_key=small, rando=rand_tag) / IP(dst=addr, ttl = ttlConst) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1) / Response()
        sendp(pkt2, iface=iface, verbose=False)

    # RANGE request
    elif sys.argv[2] == "r":
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        kv_list = sys.argv[3].split()
        if len(kv_list) != 2:
            print('RANGE requires 2 keys')
            exit(1)
        k1 = int(kv_list[0])
        k2 = int(kv_list[1])
        if k2 < k1:
            print('Second key must be >= first key')
            exit(1)
        same_bool = (k1 != k2)
        num_responses = k2 - k1 + 1
        if k2 < 512:
            small = 1
        else:
            small = 0
        if num_responses <= maxKeysPerPacket:
            pkt2 = pkt / Request(reqType=2, key1=k1, key2=k2, current=0, small_key=small, rando=rand_tag) / IP(dst=addr, ttl = ttlConst) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1)
            for _ in range(num_responses):
                pkt2 = pkt2 / Response(same = 1)
            sendp(pkt2, iface=iface, verbose=False)
        else:
            split_k1 = k1
            for i in range(math.ceil(num_responses/maxKeysPerPacket)):
                split_k1 = split_k1 + (maxKeysPerPacket * i)
                split_k2 = min(k2, split_k1 + (maxKeysPerPacket * (i + 1)) - 1)
                # print("in split, k1: {} and k2: {}".format(split_k1, split_k2))
                pkt2 = pkt / Request(reqType=2, key1=split_k1, key2=split_k2, current=0, small_key=small, rando=rand_tag) / IP(dst=addr, ttl = ttlConst) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1)
                for _ in range(split_k2 - split_k1 + 1):
                    pkt2 = pkt2 / Response(same = 1)
                print("in split, k1: {} and k2: {}".format(split_k1, split_k2))
                sendp(pkt2, iface=iface, verbose=False)

    # SELECT request
    elif sys.argv[2] == "s":
        # USAGE: ./send.py 10.0.1.1 s "k < 9"
        # TODO split if necessary, check if same=1
        tcp_sport = random.randint(49152,65535)
        tcp_dport = random.randint(1000, 2000)
        kv_list = sys.argv[3].split()
        if len(kv_list) != 3:
            print('SELECT requires k, operand, and value')
            exit(1)
        op = kv_list[1]
        value = int(kv_list[2])

        if op == ">":
            k1 = value + 1
            k2 = 1023
            small = 0
        elif op == ">=":
            k1 = value
            k2 = 1023
            small = 0
        elif op == "==":
            k1 = value
            k2 = value
            if k1 < 512:
                small = 1
            else:
                small = 0
        elif op == "<":
            k1 = 0
            k2 = value - 1
            small = 1
        elif op == "<=":
            k1 = 0
            k2 = value
            small = 1
        else:
            print('Invalid operand for SELECT')
            exit(1)

        num_responses = k2 - k1 + 1
        if num_responses <= maxKeysPerPacket:
            pkt2 = pkt / Request(reqType=3, key1=k1, key2=k2, current=0, small_key=small, rando=rand_tag) / IP(dst=addr, ttl = ttlConst) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1)
            for _ in range(num_responses):
                pkt2 = pkt2 / Response(same = 1)
            pkt2.show2()
            sendp(pkt2, iface=iface, verbose=False)
        else:
            split_k1 = k1
            for i in range(math.ceil(num_responses/maxKeysPerPacket)):
                split_k1 = split_k1 + (maxKeysPerPacket* i)
                split_k2 = min(k2, split_k1 + (maxKeysPerPacket * (i + 1)) - 1)
                # print("in split, k1: {} and k2: {}".format(split_k1, split_k2))
                pkt2 = pkt / Request(reqType=3, key1=split_k1, key2=split_k2, current=0, small_key=small, rando=rand_tag) / IP(dst=addr, ttl = ttlConst) / TCP(dport=tcp_dport, sport=tcp_sport, urgptr=1)
                for _ in range(split_k2 - split_k1 + 1):
                    pkt2 = pkt2 / Response(same = 1)
                print("in split, k1: {} and k2: {}".format(split_k1, split_k2))
                sendp(pkt2, iface=iface, verbose=False)


if __name__ == '__main__':
    main()
