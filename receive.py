#!/usr/bin/env python3
import os
import sys

from scapy.all import *
from scapy.layers.inet import _IPOption_HDR

class Probe(Packet):
    name = "probe"
    fields_desc=[BitField("byte_ct_2", 0, 32),
                 BitField("byte_ct_3", 0, 32),
                 BitField("switch_id", 0, 32)]

bind_layers(Ether, Probe, type = 0x0802)
bind_layers(Probe, IP, switch_id = 1)

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
    if Ether in pkt:
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
