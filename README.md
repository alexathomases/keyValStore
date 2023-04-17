# Milestone 3: Access Control Lists

## Relevant Files

* frontend.p4: performs load-balancing and cloning for Switch 0
* kvstore.p4: manages in-network KVS for Switches 1 and 2
* backend.p4: manages standby KVS for Switch 3
* s0-runtime.json: control-plane file for Switch 0
* s1-runtime.json: control-plane file for Switch 1
* s2-runtime.json: control-plane file for Switch 2
* s3-runtime.json: control-plane file for Switch 3
* topology.json: configures network topology with one host and one switch
* send.py: scapy-based client for sending requests
* receive.py: scapy-based client for receiving responses

## Test Scripts

* send.py
* receive.py

See usage for comprehensive test commands.

## Usage

The following command performs GET(5) for user Alice:
./send.py 10.0.1.1 a g “5”

The following command performs GET(5) for user Bob:
./send.py 10.0.1.1 b g “5”

The following command performs PUT(5, 18) for user Alice:
./send.py 10.0.1.1 a p “5 18”

The following command performs an inclusive RANGE(3, 9) for user Alice:
./send.py 10.0.1.1 a r “3 9”

The following command performs SELECT(k <= 6) for user Bob:
./send.py 10.0.1.1 b s “k <= 6”

To test Alice's functionality use the following commands:
  We have manually input value 4 into key 1000 for testing.

  To test Alice can read and write values less than or equal to 512:
  ./send.py 10.0.1.1 a p “5 18”
  ./send.py 10.0.1.1 a g "5" => Return Value: 18
  ./send.py 10.0.1.1 a p “10 11”
  ./send.py 10.0.1.1 a r "5 10"
    Return Values: 18, 0, 0, 0, 11
  ./send.py 10.0.1.1 a s "k <= 10"
    Return Values: 0, 0, 0, 0, 0, 18, 0, 0, 0, 11
  ./send.py 10.0.1.1 a p 512 10”
  ./send.py 10.0.1.1 a g "512" => Return Value: 10

  To test Alice cannot write values greater than 512:
  ./send.py 10.0.1.1 a p “550 10”
  ./send.py 10.0.1.1 a g "550" => Return Value: 0
  ./send.py 10.0.1.1 a r "550 560" =>
    Return Values: 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

  To test Alice can read values greater than 512:
  ./send.py 10.0.1.1 a g "1000" => Return Value: 4
  ./send.py 10.0.1.1 a r "1000 1010" =>
    Return Values: 4, 0, 0, 0, 0, 0, 0, 0, 0, 0
  ./send.py 10.0.1.1 a s "k == 1000" => Return Value: 4

To test Bob's functionality use the following commands:
  We have manually input value 4 into key 1000 for testing.

  To test Bob can read and write values less than or equal to 256:
  ./send.py 10.0.1.1 a p “5 18”
  ./send.py 10.0.1.1 a g "5" => Return Value: 18
  ./send.py 10.0.1.1 a p “10 11”
  ./send.py 10.0.1.1 a r "5 10"
    Return Values: 18, 0, 0, 0, 11
  ./send.py 10.0.1.1 a s "k <= 10"
    Return Values: 0, 0, 0, 0, 0, 18, 0, 0, 0, 11
  ./send.py 10.0.1.1 a p “256 10”
  ./send.py 10.0.1.1 a g "256" => Return Value: 10

  To test Bob cannot read/write values greater than 256 on both switches:
  ./send.py 10.0.1.1 a p “300 10”
  ./send.py 10.0.1.1 a g "300" => Return Value: 0
  ./send.py 10.0.1.1 a p 600 10”
  ./send.py 10.0.1.1 a g "600" => Return Value: 0
  ./send.py 10.0.1.1 a r "550 560" =>
    Return Values: 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
  ./send.py 10.0.1.1 a g "1000" => Return Value: 0
  ./send.py 10.0.1.1 a r "1000 1010" =>
    Return Values: 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
  ./send.py 10.0.1.1 a s "k == 1000" => Return Value: 0

## Project Report



## Relevant Documentation

The documentation for P4_16 and P4Runtime is available [here](https://p4.org/specs/)

All excercises in this repository use the v1model architecture, the documentation for which is available at:
1. The BMv2 Simple Switch target document accessible [here](https://github.com/p4lang/behavioral-model/blob/master/docs/simple_switch.md) talks mainly about the v1model architecture.
2. The include file `v1model.p4` has extensive comments and can be accessed [here](https://github.com/p4lang/p4c/blob/master/p4include/v1model.p4).
