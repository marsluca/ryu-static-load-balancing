from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet.ether_types import ETH_TYPE_IP
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import ethernet
from ryu.lib.packet import tcp, arp, ipv4, icmp
from ryu.topology.api import get_all_host


class LoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    VIRTUAL_IP = '10.0.1.100'
    VIRTUAL_MAC = '00:00:00:00:01:00'
    SERVER_NUMBER = 2
    # Enable consistent hashing on source port
    HASH_ON_PORT = 1  # True = 1, False = 0

    # CONFIG_DISPATCHER, Handle Features Reply
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Send all packet to the controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=1,
            match=match,
            instructions=inst
        )
        datapath.send_msg(mod)

    # MAIN_DISPATCHER, handle packet-In
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        # Obtain packet headers
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_tcp = pkt.get_protocol(tcp.tcp)
        pkt_icmp = pkt.get_protocol(icmp.icmp)

        macsrc = pkt_eth.src

        # Handle ARP packets
        if pkt_eth.ethertype == ether_types.ETH_TYPE_ARP:
            pkt_arp = pkt.get_protocol(arp.arp)
            if pkt_arp.opcode == arp.ARP_REQUEST:
                if pkt_arp.dst_ip == self.VIRTUAL_IP:
                    mac_dst_arp = self.VIRTUAL_MAC
                else:
                    hosts = get_all_host(self)
                    for host in hosts:
                        if pkt_arp.dst_ip in host.ipv4:
                            mac_dst_arp = host.mac
                            break
                    else:
                        self.logger.info("[ARP] MAC address not found")
                        return
                self.logger.info("[ARP] Request received")
                self.logger.info("[ARP] MAC destination is: " + mac_dst_arp)
                reply_packet = packet.Packet()
                reply_packet.add_protocol(
                    ethernet.ethernet(
                        dst=pkt_arp.src_mac,
                        src=mac_dst_arp,
                        ethertype=ether_types.ETH_TYPE_ARP
                    )
                )
                reply_packet.add_protocol(
                    arp.arp(
                        opcode=arp.ARP_REPLY,
                        src_mac=mac_dst_arp,
                        src_ip=pkt_arp.dst_ip,
                        dst_mac=pkt_arp.src_mac,
                        dst_ip=pkt_arp.src_ip
                    )
                )
                reply_packet.serialize()
                actions = [parser.OFPActionOutput(in_port)]
                packet_out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=ofproto.OFPP_CONTROLLER,
                    data=reply_packet.data,
                    actions=actions
                )
                datapath.send_msg(packet_out)
                self.logger.info("[ARP] Reply sent!")
                return

        # Handle IPv4 packets
        if pkt_ipv4 is not None:
            # Handle TCP packets
            if pkt_tcp is not None:
                if self.HASH_ON_PORT == 1:  # Consistent hashing on IPv4 source and TCP source port
                    server = hash((pkt_ipv4.src, pkt_tcp.src_port)) % self.SERVER_NUMBER
                else:  # Deterministic routing via consistent hashing only on IPv4 source
                    server = hash((pkt_ipv4.src)) % self.SERVER_NUMBER
                server = server + 1
                ipdst = "10.0.1." + str(server)
                macdst = "00:00:00:00:01:0" + str(server)
                out_port = server  # IMPORTANT: Servers must be plugged in port 1 and 2
                # Inbound FlowMod
                match = parser.OFPMatch(
                    eth_type=ETH_TYPE_IP,
                    ip_proto=pkt_ipv4.proto,
                    eth_src=macsrc,
                    tcp_src=pkt_tcp.src_port,
                    eth_dst=self.VIRTUAL_MAC
                )
                self.logger.info("server is: " + str(server))
                actions = [parser.OFPActionSetField(eth_dst=macdst),
                           parser.OFPActionSetField(ipv4_dst=ipdst),
                           parser.OFPActionOutput(out_port)]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                ofmsg = parser.OFPFlowMod(
                    datapath=datapath,
                    hard_timeout=120,
                    priority=50,
                    match=match,
                    instructions=inst,
                )
                datapath.send_msg(ofmsg)

                # Outbound FlowMod
                match = parser.OFPMatch(
                    eth_type=ETH_TYPE_IP,
                    ip_proto=pkt_ipv4.proto,
                    eth_src=macdst,
                    tcp_dst=pkt_tcp.src_port,
                    eth_dst=macsrc
                )
                actions = [
                    parser.OFPActionSetField(eth_src=self.VIRTUAL_MAC),
                    parser.OFPActionSetField(ipv4_src=self.VIRTUAL_IP),
                    parser.OFPActionOutput(in_port)
                ]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
                ofmsg = parser.OFPFlowMod(
                    datapath=datapath,
                    hard_timeout=120,
                    priority=50,
                    match=match,
                    instructions=inst,
                )
                datapath.send_msg(ofmsg)

                # Change packet data
                pkt_eth.dst = macdst
                pkt_ipv4.dst = ipdst
                pkt_tcp.csum = 0
                pkt.serialize()

                # Packet-Out
                actions = [parser.OFPActionOutput(out_port)]
                out = parser.OFPPacketOut(
                    datapath=datapath,
                    buffer_id=ofproto.OFP_NO_BUFFER,
                    in_port=in_port,
                    actions=actions,
                    data=msg.data
                )
                datapath.send_msg(out)
            # Handle ICMP packets
            elif pkt_icmp is not None:
                if pkt_icmp.type == icmp.ICMP_ECHO_REQUEST:
                    if pkt_ipv4.dst == self.VIRTUAL_IP:
                        mac_icmp = self.VIRTUAL_MAC
                        self.logger.info("[ICMP] Request received")
                        reply_icmp = packet.Packet()
                        reply_icmp.add_protocol(
                            ethernet.ethernet(
                                ethertype=pkt_eth.ethertype,
                                dst=pkt_eth.src,
                                src=mac_icmp
                            )
                        )
                        reply_icmp.add_protocol(
                            ipv4.ipv4(
                                dst=pkt_ipv4.src,
                                src=pkt_ipv4.dst,
                                proto=pkt_ipv4.proto
                            )
                        )
                        reply_icmp.add_protocol(
                            icmp.icmp(
                                type_=icmp.ICMP_ECHO_REPLY,
                                code=icmp.ICMP_ECHO_REPLY_CODE,
                                csum=0,
                                data=pkt_icmp.data
                            )
                        )
                        reply_icmp.serialize()
                        actions = [parser.OFPActionOutput(in_port)]
                        packet_out = parser.OFPPacketOut(
                            datapath=datapath,
                            buffer_id=ofproto.OFP_NO_BUFFER,
                            in_port=ofproto.OFPP_CONTROLLER,
                            data=reply_icmp.data,
                            actions=actions
                        )
                        datapath.send_msg(packet_out)
                        self.logger.info("[ICMP] Reply sent!")
                        return
                    else:
                        return
            else:
                return
        # Drop packet types not in the specifications
        else:
            return