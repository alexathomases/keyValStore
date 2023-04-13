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

## Project Report



## Relevant Documentation

The documentation for P4_16 and P4Runtime is available [here](https://p4.org/specs/)

All excercises in this repository use the v1model architecture, the documentation for which is available at:
1. The BMv2 Simple Switch target document accessible [here](https://github.com/p4lang/behavioral-model/blob/master/docs/simple_switch.md) talks mainly about the v1model architecture.
2. The include file `v1model.p4` has extensive comments and can be accessed [here](https://github.com/p4lang/p4c/blob/master/p4include/v1model.p4).
