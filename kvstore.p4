/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

#define NUM_KEYS 1024

const bit<8> RECIRC_FL_1 = 0;
const bit<8> CLONE_FL_1  = 1;

const bit<16> TYPE_IPV4 = 0x800;
const bit<16> TYPE_REQ = 0x801;
const bit<2> TYPE_GET = 0b00;
const bit<2> TYPE_PUT = 0b01;
const bit<2> TYPE_RANGE = 0b10;
const bit<2> TYPE_SELECT = 0b11;

register<bit<32>>(NUM_KEYS) kvstore;

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
    bit<8> ping;
    // Normal requests are ping 0, ping 1, pong 2
    bit<32> random;
}

header response_t {
    bit<32> ret_val;
    bit<8> keepGoing;
}

struct recirculate_metadata_t {
   @field_list(RECIRC_FL_1)
   bit<8> i;
}

struct clone_metadata_t {
  @field_list(CLONE_FL_1)
  bit<8> f;
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



    action drop() {
        mark_to_drop(standard_metadata);
    }

    action get(egressSpec_t port) {
        kvstore.read(hdr.response[0].ret_val, hdr.request.key1);
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action put(egressSpec_t port) {
        kvstore.write(hdr.request.key1, hdr.request.val);
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action rangeReq(egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    action selectReq(egressSpec_t port) {
        standard_metadata.egress_spec = port;
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }

    table kvs {
        key = {
            hdr.request.reqType: exact;
        }
        actions = {
            get;
            put;
            rangeReq;
            selectReq;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    apply {
        if (hdr.request.ping == 0) {
            if (hdr.ipv4.isValid() && hdr.ipv4.ttl > 0) {
                kvs.apply();
                hdr.request.small_key = 2;
            }
        }


    }
}

/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/

control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {

       action add_response() {
           hdr.response.push_front(1);
           hdr.response[0].setValid();
           hdr.response[0].keepGoing = 1;
           kvstore.read(hdr.response[0].ret_val, (bit<32>)((bit<8>) hdr.request.key1 + meta.nextInd.i));
       }

       apply {
           if (meta.nextInd.i <= ((bit<8>) hdr.request.key2 - (bit<8>) hdr.request.key1)) {
             if (hdr.ipv4.isValid() && hdr.request.reqType > 1) {
                 add_response();
                 recirculate_preserving_field_list(RECIRC_FL_1);
             }
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
