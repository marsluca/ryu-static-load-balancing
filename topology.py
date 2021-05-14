from mininet.topo import Topo

class Topology(Topo):
 
    def build(self):
 
        # Hosts and switches
        host1 = self.addHost('H1', ip='10.0.0.1/24', mac="00:00:00:00:00:01")
        host2 = self.addHost('H2', ip='10.0.0.2/24', mac="00:00:00:00:00:02")
        host3 = self.addHost('H3', ip='10.0.0.3/24', mac="00:00:00:00:00:03")
        host4 = self.addHost('H4', ip='10.0.0.4/24', mac="00:00:00:00:00:04")
        host5 = self.addHost('H5', ip='10.0.0.5/24', mac="00:00:00:00:00:05")
        server1 = self.addHost('SRV1', ip='10.0.1.1/24', mac="00:00:00:00:01:01")
        server2 = self.addHost('SRV2', ip='10.0.1.2/24', mac="00:00:00:00:01:02")
        switch1 = self.addSwitch('SW1')
 
        # Links
        self.addLink(host1, switch1, bw=1000, delay='5ms')
        self.addLink(host2, switch1, bw=1000, delay='5ms')
        self.addLink(host3, switch1, bw=1000, delay='5ms')
        self.addLink(host4, switch1, bw=1000, delay='5ms')
        self.addLink(host5, switch1, bw=1000, delay='5ms')
        self.addLink(server1, switch1, bw=1000, delay='5ms')
        self.addLink(server2, switch1, bw=1000, delay='5ms')
 
topos = { 'topology': ( lambda: Topology() ) }