# Milestone 2: KVS Partitions & Load-Balancing

## Relevant Files

* kvstore.p4: manages in-network KVS
* s1-runtime.json: control-plane file for Switch 1
* topology.json: configures network topology with one host and one switch
* send.py: scapy-based client for sending requests
* receive.py: scapy-based client for receiving responses

## Test Scripts

* send.py:
* receive.py

## Usage

The following command performs GET(5):
./send.py 10.0.1.1 g “5”

The following command performs PUT(5, 18):
./send.py 10.0.1.1 p “5 18”

The following command performs RANGE(3, 9):
./send.py 10.0.1.1 r “3 9”

The following command performs SELECT(k <= 6):
./send.py 10.0.1.1 s “k <= 6”

In order to test the functionality of our load balanced kvstore, run the
following commands:
  To test keys < 512:
    ./send.py 10.0.1.1 a p “5 18”
    ./send.py 10.0.1.1 a g "5" => Return Value: 18
    ./send.py 10.0.1.1 a p “10 11”
    ./send.py 10.0.1.1 a r "5 10"
      Return Values: 18, 0, 0, 0, 11
    ./send.py 10.0.1.1 a s "k <= 10"
      Return Values: 0, 0, 0, 0, 0, 18, 0, 0, 0, 11
    ./send.py 10.0.1.1 a p "200 300"
    ./send.py 10.0.1.1 a g "200" => Return Value: 300
    ./send.py 10.0.1.1 a s "k == 200" => Return Value: 300

  To test keys 512 - 1023:
    ./send.py 10.0.1.1 a p 512 10”
    ./send.py 10.0.1.1 a g "512" => Return Value: 10
    ./send.py 10.0.1.1 a p “515 18”
    ./send.py 10.0.1.1 a g "515" => Return Value: 18
    ./send.py 10.0.1.1 a r "512 516"
      Return Values: 10, 0, 0, 18, 0
    ./send.py 10.0.1.1 a s "k <= 520"
      Return Values: 10, 0, 0, 18, 0, 0, 0, 0, 0

  To test ping/pong:
    Our program generates a random integer from 0 - 9. When the chosen integer
    is 9, we send a custom request indicating the packet is a "ping" packet.
    The frontend switch (s0) will clone this packet twice. The original packet
    is sent to its indented destination to perform the request, and the
    cloned packets are sent to switch 1 and switch 2, respectively. At switches
    1 and 2, the cloned packets are modified to "pong" packets, sent back to
    the frontend switch, where we will update the packet to store the difference
    between the ping requests sent and pongs received. Ultimately the packet is
    sent back to the host where, our receive scapy script prints the difference
    between the ping and pong packets for failure detection.


## Project Report



## Relevant Documentation

The documentation for P4_16 and P4Runtime is available [here](https://p4.org/specs/)

All excercises in this repository use the v1model architecture, the documentation for which is available at:
1. The BMv2 Simple Switch target document accessible [here](https://github.com/p4lang/behavioral-model/blob/master/docs/simple_switch.md) talks mainly about the v1model architecture.
2. The include file `v1model.p4` has extensive comments and can be accessed [here](https://github.com/p4lang/p4c/blob/master/p4include/v1model.p4).
