/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#define NUM_KEYS 1024

const bit<8> RECIRC_FL_1 = 0;
const bit<8> CLONE_FL_1 = 1;

const bit<32> S3_CLONE_SESSION_ID = 5;
const bit<32> S1_CLONE_SESSION_ID = 6;
const bit<32> S2_CLONE_SESSION_ID = 7;

const bit<32> INGRESS_CLONE = 1;

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_REQ = 0x801;
const bit<2> TYPE_GET = 0b00;
const bit<2> TYPE_PUT = 0b01;
const bit<2> TYPE_RANGE = 0b10;
const bit<2> TYPE_SELECT = 0b11;

#define IS_I2E_CLONE(std_meta) (std_meta.instance_type == INGRESS_CLONE)

register<bit<32>>(2) pingpong;


/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/

typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;

header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}

header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}

header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}

header request_t {
    bit<8> exists;
    bit<8> reqType;
    bit<32> key1;
    bit<32> key2;
    bit<32> val;
    bit<8> op;
    bit<8> current;
    bit<8> small_key;
    //small key: 0 = s2, 1 = s1
    bit<8> ping;
    // Normal requests are ping 0, ping 1, pong 2
    bit<32> random;
    bit<32> pingpong_diff;
}

header response_t {
    bit<32> ret_val;
    bit<8> keepGoing;
}

struct recirculate_metadata_t {
   @field_list(RECIRC_FL_1)
   bit<8> i;
}

struct metadata {
    recirculate_metadata_t nextInd;
    bit<8> remaining;
}

struct headers {
    ethernet_t      ethernet;
    request_t       request;
    ipv4_t          ipv4;
    tcp_t           tcp;
    response_t[256]   response;
}

/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/

parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {

    state start {
        transition parse_ethernet;
    }

    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            TYPE_REQ: parse_req;
            default: accept;
        }
    }

    state parse_req {
        packet.extract(hdr.request);
        meta.nextInd.i = hdr.request.current;
        meta.remaining =  hdr.request.current;
        hdr.request.current = hdr.request.current + 1;
        transition parse_ipv4;
    }

    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition parse_tcp;
    }

    state parse_tcp {
        packet.extract(hdr.tcp);
          transition select(hdr.tcp.urgentPtr) {
            1: parse_response;
            default: accept;
        }
    }

    state parse_response {
        packet.extract(hdr.response.next);
        meta.remaining = meta.remaining - 1;
        transition select(meta.remaining) {
            0: accept;
            default: parse_response;
        }
    }
}

/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/

control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}


/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {

    bit<32> pings;
    bit<32> pongs;

    action clone_pkt() {
      clone_preserving_field_list(CloneType.I2E, S3_CLONE_SESSION_ID, CLONE_FL_1);
    }

    action clone_to_s1() {
      clone_preserving_field_list(CloneType.I2E, S1_CLONE_SESSION_ID, CLONE_FL_1);
    }

    action clone_to_s2() {
      clone_preserving_field_list(CloneType.I2E, S2_CLONE_SESSION_ID, CLONE_FL_1);
    }

    action noAction() {
      ;
    }

    table clone_table {
      key = {
          hdr.request.reqType: exact;
      }
      actions = {
          clone_pkt;
          noAction;
      }
      size = 1024;
      default_action = noAction();
    }

    table clone_ping_s1 {
      key = {
          hdr.request.random: exact;
      }
      actions = {
          clone_to_s1;
          noAction;
      }
      size = 1024;
      default_action = noAction();
    }

    table clone_ping_s2 {
      key = {
          hdr.request.random: exact;
      }
      actions = {
          clone_to_s2;
          noAction;
      }
      size = 1024;
      default_action = noAction();
    }


    action drop() {
        mark_to_drop(standard_metadata);
    }

    action ipv4_forward(macAddr_t dstAddr, egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
    }

    table ipv4_lpm {
        key = {
            hdr.request.small_key: exact;
        }
        actions = {
            ipv4_forward;
            drop;
            NoAction;
            noAction;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        if (hdr.request.ping == 0) {
            if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0) {
                clone_table.apply();
                ipv4_lpm.apply();
            }
            if (hdr.request.random == 9) {
                hdr.request.ping = 1;
                pingpong.read(pings, 0);
                pings = pings + 2;
                pingpong.write(0, pings);
                clone_ping_s1.apply();
                clone_ping_s2.apply();
            }
        } else if (hdr.request.ping == 2) {
            pingpong.read(pings, 0);
            pingpong.read(pongs, 1);
            pongs = pongs + 1;
            pingpong.write(1, pongs);
            hdr.request.pingpong_diff = pings - pongs;
            standard_metadata.egress_spec = 1;
        }
    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

       apply {
          if (IS_I2E_CLONE(standard_metadata)) {
              //send out through s0-p4
              //standard_metadata.egress_spec = 4;
              //hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
              //hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
              //hdr.ethernet.dstAddr = 080000000400;

          }
       }
 }

/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/

control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
        update_checksum(
        hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
    }
}

/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/

control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.ethernet);
        packet.emit(hdr.request);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.tcp);
        packet.emit(hdr.response);
    }
}

/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/

V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
