# 📘 DHCP Starvation Attack - Laboratorio de Seguridad de Redes

## 🎯 Descripción del Proyecto

Este proyecto documenta la implementación de un ataque de **DHCP Starvation** en un entorno de laboratorio virtualizado utilizando PNETLab con equipos Cisco vIOS. 

El ataque DHCP Starvation es una técnica de **Denegación de Servicio (DoS)** que busca agotar el pool de direcciones IP disponibles en un servidor DHCP. Lo logré generando múltiples solicitudes DHCP DISCOVER con direcciones MAC falsas, forzando al servidor a asignar todas sus direcciones IP disponibles a clientes inexistentes.

Desarrollé este script en Python utilizando Scapy para entender cómo funcionan estos ataques a nivel de red y cómo protegerse contra ellos mediante configuraciones de seguridad en switches Cisco.

---

## 🔧 Objetivo del Script

El script `dhcp_starvation.py` tiene como objetivo:

1. **Generar direcciones MAC aleatorias** para simular múltiples clientes únicos
2. **Enviar paquetes DHCP DISCOVER** masivos con estas MACs falsas
3. **Consumir todas las direcciones IP** disponibles en el pool DHCP del router
4. **Provocar una denegación de servicio** para clientes legítimos que intenten obtener una IP por DHCP

Este es un ejercicio educativo para comprender las vulnerabilidades del protocolo DHCP y la importancia de implementar medidas de seguridad adecuadas.

---

## 🗺️ Topología del Laboratorio

Mi topología de red está diseñada con la técnica **Router-on-a-Stick** para segmentar el tráfico mediante VLANs:

```
                    [Router vIOS]
                    Gi0/0.10 → 12.0.10.1/24 (VLAN 10)
                    Gi0/0.20 → 12.0.20.1/24 (VLAN 20)
                          |
                     [SW-1 Core]
                     (Trunk 802.1Q)
                    /           \ 
            [SW-2]               [SW-3]
         (Access VLAN 10)    (Access VLAN 20)
                |                   |
          [PC Windows]         [Kali Linux]
          DHCP Client          Atacante
       12.0.10.x/24           12.0.20.2/24
```

### 📋 Detalles de Configuración

#### **Router vIOS:**
- **Gi0/0.10** → 12.0.10.1 255.255.255.0 (Gateway VLAN 10)
- **Gi0/0.20** → 12.0.20.1 255.255.255.0 (Gateway VLAN 20)
- **Servidor DHCP** configurado para ambas VLANs

#### **VLAN 10 - Red Windows (Víctimas):**
- Red: `12.0.10.0/24`
- Gateway: `12.0.10.1`
- DHCP Pool: `12.0.10.10 - 12.0.10.254`
- Clientes: PC Windows (obtiene IP automática)

#### **VLAN 20 - Red Linux (Atacante):**
- Red: `12.0.20.0/24`
- Gateway: `12.0.20.1`
- DHCP Pool: `12.0.20.10 - 12.0.20.254`
- Kali Linux: `12.0.20.2/24` (IP estática)

#### **Switches:**
- **SW-1:** Switch core con enlaces trunk hacia SW-2 y SW-3
- **SW-2:** Switch de acceso, puerto access VLAN 10 para Windows
- **SW-3:** Switch de acceso, puerto access VLAN 20 para Kali

---

## 🚀 Ejecución del Ataque

### **Requisitos Previos:**

Antes de ejecutar el script, me aseguré de tener instalado:

```bash
# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar Python 3 y pip
sudo apt install python3 python3-pip -y

# Instalar Scapy
sudo pip3 install scapy
```

### **Parámetros del Script:**

El script acepta los siguientes argumentos:

- `-i, --interface`: Interfaz de red a utilizar (obligatorio)
- `-c, --count`: Cantidad de paquetes DISCOVER a enviar (default: 254)
- `-d, --delay`: Tiempo de espera entre paquetes en segundos (default: 0.05)

### **Ejemplo de Ejecución Real:**

Desde mi máquina Kali Linux, ejecuté el ataque contra el pool DHCP de VLAN 20:

```bash
sudo python3 dhcp_starvation.py -i eth0 -c 500 -d 0.01
```

**Explicación de los parámetros:**
- `-i eth0`: Utilizo la interfaz eth0 de Kali
- `-c 500`: Envío 500 solicitudes DHCP DISCOVER
- `-d 0.01`: Con un delay de 0.01 segundos entre cada paquete (muy rápido)

### **Salida del Script:**

```
============================================================
 🔥 INICIANDO DHCP STARVATION ATTACK
 [*] Interfaz : eth0
 [*] Objetivos: 500 paquetes
 [*] Delay    : 0.01s
============================================================
[+] DISCOVER enviados: 10
[+] DISCOVER enviados: 20
[+] DISCOVER enviados: 30
...
[+] DISCOVER enviados: 500

============================================================
 [✓] Total enviado: 500
 [!] Verifica en el router con: show ip dhcp binding
============================================================
```

---

## 🔍 Verificación del Ataque en el Router

Una vez ejecutado el ataque, me conecté al router vIOS para verificar el estado del pool DHCP:

### **Comando 1: Verificar Bindings DHCP**

```cisco
Router# show ip dhcp binding
```

**Resultado esperado:**
Observé cientos de asignaciones IP con direcciones MAC aleatorias generadas por mi script:

```
IP address       Client-ID/              Lease expiration        Type
                 Hardware address
12.0.20.10       0200.1a3f.4e21          Feb 11 2026 15:45       Automatic
12.0.20.11       0200.2b4c.5d32          Feb 11 2026 15:45       Automatic
12.0.20.12       0200.3c5d.6e43          Feb 11 2026 15:45       Automatic
...
12.0.20.254      0200.ff9e.8d76          Feb 11 2026 15:46       Automatic
```

### **Comando 2: Verificar Estado del Pool**

```cisco
Router# show ip dhcp pool
```

**Resultado esperado:**

```
Pool VLAN20 :
 Utilization mark (high/low)    : 100 / 0
 Subnet size (first/next)       : 0 / 0 
 Total addresses                : 254
 Leased addresses               : 245
 Pending event                  : none
 1 subnet is currently in the pool :
 Current index        IP address range                    Leased addresses
 12.0.20.255          12.0.20.1        - 12.0.20.254       245
```

Aquí pude confirmar que el pool estaba casi completamente agotado (96%+ de utilización).

### **Comando 3: Verificar Estadísticas DHCP**

```cisco
Router# show ip dhcp server statistics
```

Observé un incremento masivo en los mensajes DHCPDISCOVER recibidos.

---

## 📸 Capturas de Pantalla Sugeridas

Para documentar este ataque, recomiendo incluir las siguientes capturas:

## Captura 1 – Estado inicial del DHCP (Antes del ataque)
<img width="789" height="429" alt="image" src="https://github.com/user-attachments/assets/aa5f688a-b874-48bb-8060-7a5b292e6d46" />

## Captura 2 – Kali ejecutando el ataque
<img width="762" height="421" alt="image" src="https://github.com/user-attachments/assets/c0761228-1b5e-48b1-9f91-b920845fe10d" />
 
---

## 🛡️ Medidas de Mitigación

Después de realizar este ataque, implementé las siguientes medidas de seguridad en los switches para proteger la red:

### **1. DHCP Snooping**

Esta es la defensa más efectiva contra DHCP Starvation. Configuré DHCP Snooping en los switches de acceso:

```cisco
! En SW-2 y SW-3
Switch(config)# ip dhcp snooping
Switch(config)# ip dhcp snooping vlan 10,20
Switch(config)# no ip dhcp snooping information option

! Marcar puertos confiables (hacia el router)
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# ip dhcp snooping trust

! Limitar tasa de paquetes DHCP en puertos de acceso
Switch(config)# interface range GigabitEthernet0/2-24
Switch(config-if-range)# ip dhcp snooping limit rate 10
```

**¿Cómo funciona?**
- Solo permite respuestas DHCP desde puertos "trust" (donde está el servidor legítimo)
- Limita la cantidad de solicitudes DHCP por segundo desde puertos de usuario
- Bloquea automáticamente puertos que excedan el límite configurado

### **2. Port Security**

Limité la cantidad de direcciones MAC que pueden aprender los puertos de acceso:

```cisco
Switch(config)# interface range GigabitEthernet0/2-24
Switch(config-if-range)# switchport mode access
Switch(config-if-range)# switchport port-security
Switch(config-if-range)# switchport port-security maximum 2
Switch(config-if-range)# switchport port-security violation restrict
Switch(config-if-range)# switchport port-security mac-address sticky
```

Esto previene que un atacante genere múltiples MACs desde un solo puerto.

### **3. Dynamic ARP Inspection (DAI)**

Complementé DHCP Snooping con DAI para prevenir ataques ARP relacionados:

```cisco
Switch(config)# ip arp inspection vlan 10,20
Switch(config)# interface GigabitEthernet0/1
Switch(config-if)# ip arp inspection trust
```

### **4. Monitoreo y Logging**

Activé logging para detectar intentos de ataque:

```cisco
Switch(config)# logging buffered 64000 informational
Switch(config)# ip dhcp snooping database flash:dhcp-snooping.db
```

---

## ✅ Verificación de Mitigaciones

Después de implementar DHCP Snooping, intenté ejecutar el ataque nuevamente:

```bash
sudo python3 dhcp_starvation.py -i eth0 -c 500 -d 0.01
```

**Resultado en el switch:**

```cisco
Switch# show ip dhcp snooping statistics

 Packets Dropped because:
   DHCP packets on untrusted ports        : 485
   Rate limit exceeded                    : 485
```

El puerto de acceso fue automáticamente puesto en estado "err-disabled" por violar la política de rate-limit.

---

## 📊 Resultados del Experimento

### **Antes de las Mitigaciones:**
- ✅ Logré agotar el pool DHCP en menos de 10 segundos
- ✅ Los clientes legítimos no pudieron obtener direcciones IP
- ✅ El router mostró 245+ bindings con MACs aleatorias

### **Después de las Mitigaciones:**
- ❌ DHCP Snooping bloqueó el 97% de los paquetes maliciosos
- ❌ Port Security deshabilitó el puerto atacante automáticamente
- ✅ Los clientes legítimos continuaron obteniendo IPs normalmente

---

## 🧠 Conclusiones Técnicas

A través de este laboratorio, comprobé que:

1. **El protocolo DHCP es vulnerable por diseño:** No tiene autenticación nativa de clientes, lo que permite que cualquier dispositivo solicite múltiples IPs.

2. **La velocidad del ataque es crítica:** Con un delay de 0.01s pude agotar un pool /24 en segundos. Esto demuestra que los ataques de capa 2 pueden ser devastadores.

3. **DHCP Snooping es esencial:** Esta funcionalidad debe estar activa en todos los switches de acceso en redes de producción. Sin ella, cualquier usuario con acceso físico puede lanzar este ataque.

4. **La segmentación por VLANs no es suficiente:** Aunque el atacante esté en VLAN 20, puede afectar el servicio DHCP de su propia VLAN. En redes convergentes, esto podría afectar VoIP, cámaras IP, etc.

5. **La defensa en profundidad funciona:** La combinación de DHCP Snooping + Port Security + DAI + Rate Limiting crea múltiples capas que dificultan enormemente el éxito del ataque.

6. **El monitoreo es clave:** Los logs de DHCP Snooping me permitieron detectar y analizar el ataque. En un entorno real, estos eventos deberían integrarse con un SIEM.

Este ejercicio me ayudó a entender no solo cómo funcionan los ataques a nivel de capa 2, sino también la importancia de implementar controles de seguridad básicos que a menudo se pasan por alto en redes empresariales.

---

## ⚠️ Disclaimer Legal

Este script y documentación son únicamente para **fines educativos** en entornos controlados de laboratorio. Ejecutar este ataque en redes de producción o sin autorización explícita es **ilegal** y puede resultar en consecuencias legales.

Solo realicé estas pruebas en mi propio laboratorio virtualizado con equipos que yo controlo completamente.

---

## 📚 Referencias

- RFC 2131: Dynamic Host Configuration Protocol
- Cisco IOS Security Configuration Guide - DHCP Snooping
- Scapy Documentation: https://scapy.readthedocs.io/

---

**Autor:** mariana121319  
**Fecha:** 2026-02-11  
**Entorno:** PNETLab con Cisco vIOS  
**Versión:** 1.0
