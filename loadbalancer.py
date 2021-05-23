from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet.ether_types import ETH_TYPE_IP
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ether_types
from ryu.lib.packet import ethernet
from ryu.lib.packet import tcp, arp, ipv4
from ryu.topology.api import get_all_switch, get_all_link, get_all_host


class LoadBalancer(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    VIRTUAL_IP = '10.0.1.100'
    VIRTUAL_MAC = '00:00:00:00:01:00'  # controllare in specifica!!! da aggiungere

    # CONFIG_DISPATCHER, gestione Features Reply
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Manda al controllore tutti i pacchetti
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=1, match=match, instructions=inst)  # priorità inferiore?
        datapath.send_msg(mod)

    # MAIN_DISPATCHER, gestione dell'evento PacketIn
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        # Estraiamo gli header del pacchetto
        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        pkt_ipv4 = pkt.get_protocol(ipv4.ipv4)
        pkt_tcp = pkt.get_protocol(tcp.tcp)

        macsrc = pkt_eth.src

        # Handle ARP
        if pkt_eth.ethertype == ether_types.ETH_TYPE_ARP:
            pkt_arp = pkt.get_protocol(arp.arp)
            if pkt_arp.opcode == arp.ARP_REQUEST:
                if pkt_arp.dst_ip == self.VIRTUAL_IP:
                    mac_dst_arp=self.VIRTUAL_MAC
                else:
                    for host in get_all_host(self):
                        if pkt_arp.dst_ip in host.ipv4:
                            mac_dst_arp = host.mac
                            break # qualcosa di piu' carino del break? Bolchini docet
                    else:
                        print("MAC address" + mac_dst_arp+ "not found")
                        return
                print("macdst arp is: : " + mac_dst_arp)
                self.logger.info("[ARP] Request recived")
                reply_packet = packet.Packet()
                reply_packet.add_protocol(
                    ethernet.ethernet(
                        dst=pkt_arp.src_mac,
                        src=mac_dst_arp,
                        ethertype=ether_types.ETH_TYPE_ARP
                    )
                )
                reply_packet.add_protocol(
                    arp.arp(opcode=arp.ARP_REPLY,
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

        # Consideriamo solo i pacchetti IPv4 TCP
        if pkt_ipv4 is not None and pkt_tcp is not None:
            # gestione pacchetto.. (Lucio)
            server = hash((pkt_ipv4.src, pkt_tcp.src_port)) % 2
            server = server + 1  # per avere 1 o 2 come valori
            ipdst = "10.0.1." + str(server)
            macdst = "00:00:00:00:01:0" + str(server)
            out_port = server  # // IMPORTANTE: i server devono essere collegati alla porta 1 e 2 dello switch

            # FlowMod in ingresso
            match = parser.OFPMatch(
                eth_type=ETH_TYPE_IP,
                ip_proto=pkt_ipv4.proto,
                eth_src=macsrc,
                tcp_src=pkt_tcp.src_port,
                eth_dst=self.VIRTUAL_MAC
            )
            print("macsrc is: " + macsrc)  # debug
            print("macdst is: " + pkt_eth.dst)
            print("server is: " + str(server))
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

            # FlowMod in uscita
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

            # modifichiamo il pacchetto con i nuovi dati
            pkt_eth.dst = macdst
            pkt_ipv4.dst = ipdst
            pkt_tcp.csum = 0
            pkt.serialize()

            # faccio il packet out
            actions = [parser.OFPActionOutput(out_port)]
            out = parser.OFPPacketOut(
                datapath=datapath,
                buffer_id=ofproto.OFP_NO_BUFFER,
                in_port=in_port,
                actions=actions,
                data=msg.data
            )
            datapath.send_msg(out)
        
        # Droppo i pacchetti non inerenti alla specifica
        else:
            return
