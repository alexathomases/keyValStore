# Milestone 1: In-Network Key-Value Store

## Relevant Files

* kvstore.p4: manages in-network KVS
* s1-runtime.json: control-plane file for Switch 1
* topology.json: configures network topology with one host and one switch
* send.py: scapy-based client for sending requests
* receive.py: scapy-based client for receiving responses

## Test Scripts

* send.py:
* receive.py

## Program Design

To implement the in-network key-value store, we designed a topology with one end host and one switch. The client sent and received requests while the switch maintained the internal database. Inside the switch, which runs the program kvstore.p4, we used a register of length 1024 to maintain the data. The register indices corresponded to the keys in the key-value pair and the data in the register corresponded to the values. For instance, the key-value pair (10, 15) would be stored as the integer 15 at index 10 inside the register. We performed the logic for parsing command-line requests inside our Scapy-based Python client scripts. The specific keys and values for each request were stored as custom Request and Response headers inside the packet. In the kvstore.p4 program, we use match/action tables to determine the request type (GET, PUT, RANGE, or SELECT) and perform the appropriate operations. Specifically, the operations involved for each request were reading from or writing to the database register. For RANGE and SELECT requests that queried multiple keys, we used the recirculate_preserving_field_list() functionality to recirculate the packet through the ingress and egress pipelines after dynamically adding a new element to the array of Response headers. 

## Usage

The following command performs GET(5):
./send.py 10.0.1.1 g “5”

The following command performs PUT(5, 18):
./send.py 10.0.1.1 p “5 18”

The following command performs RANGE(3, 9):
./send.py 10.0.1.1 r “3 9”

The following command performs SELECT(k <= 6):
./send.py 10.0.1.1 s “k <= 6”

## Relevant Documentation

The documentation for P4_16 and P4Runtime is available [here](https://p4.org/specs/)

All excercises in this repository use the v1model architecture, the documentation for which is available at:
1. The BMv2 Simple Switch target document accessible [here](https://github.com/p4lang/behavioral-model/blob/master/docs/simple_switch.md) talks mainly about the v1model architecture.
2. The include file `v1model.p4` has extensive comments and can be accessed [here](https://github.com/p4lang/p4c/blob/master/p4include/v1model.p4).
