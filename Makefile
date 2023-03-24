BMV2_SWITCH_EXE = simple_switch_grpc
TOPO = topology.json
P4C_ARGS = --p4runtime-files $(basename $@).p4.p4info.txt

include ../../utils/Makefile
