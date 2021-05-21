from mininet.topo import Topo
from mininet.link import TCLink

class Topology(Topo):
 
    def build(self):
 
        # Hosts and switches
        host1 = self.addHost('H1')
        host2 = self.addHost('H2')
        host3 = self.addHost('H3')
        host4 = self.addHost('H4')
        host5 = self.addHost('H5')
        server1 = self.addHost('SRV1', ip='10.0.1.1/8', mac="00:00:00:00:01:01")
        server2 = self.addHost('SRV2', ip='10.0.1.2/8', mac="00:00:00:00:01:02")
        switch1 = self.addSwitch('SW1')
 
        # Links
        self.addLink(server1, switch1, port2=1, cls=TCLink, bw=1000, delay='1ms')
        self.addLink(server2, switch1, port2=2, cls=TCLink, bw=1000, delay='1ms')
        self.addLink(host1, switch1, cls=TCLink, bw=1000, delay='5ms')
        self.addLink(host2, switch1, cls=TCLink, bw=1000, delay='5ms')
        self.addLink(host3, switch1, cls=TCLink, bw=1000, delay='5ms')
        self.addLink(host4, switch1, cls=TCLink, bw=1000, delay='5ms')
        self.addLink(host5, switch1, cls=TCLink, bw=1000, delay='5ms')
 
topos = { 'topology': ( lambda: Topology() ) }
