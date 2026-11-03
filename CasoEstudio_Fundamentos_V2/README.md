# Caso de Estudio – Fundamentos V2 · Solución (Packet Tracer)

- `Caso_de_Estudio-Fundamentos_V2.pkt`: el mismo archivo entregado, ya resuelto. Conserva los nombres de equipos, las notas, las pruebas PDU y el nombre de archivo originales.
- `configuraciones/`: scripts CLI de cada equipo. Sirven de respaldo si alguno abre sin configuración.
- `herramientas/`: scripts para regenerar el `.pkt` y validar el enrutamiento (`simulate.py`).

## Direccionamiento (según el enunciado)

| Red | Dirección | Uso |
|---|---|---|
| VLAN 10 Clientes / 20 Administrativo / 30 Finanzas | 192.168.10.0/24, 192.168.20.0/24, 192.168.30.0/24 | Hosts por DHCP. Gateway `.1` en el multicapa |
| Red Servidores | 10.10.1.0/29 | Router0 `.1`, DHCP `.3`, DNS `.4`, WEB `.5` |
| Intranet | 172.16.0.0, subredes /30 | Enlaces entre routers y multicapa |
| HSRP | 192.168.1.0/29 | IP virtual `.1`, Router1 `.2`, Router2 `.3`, PC0–PC2 `.4`–`.6` |

### Tabla routers

| Dispositivo | Interfaz | Dirección IP | Máscara |
|---|---|---|---|
| Router 0 | Gig0/0 | 10.10.1.1 | 255.255.255.248 |
| | Gig0/1 | 172.16.0.13 | 255.255.255.252 |
| | Gig0/2 | 172.16.0.10 | 255.255.255.252 |
| | Gig0/0/0 | 172.16.0.17 | 255.255.255.252 |
| Router 1 | Gig0/0 | 192.168.1.2 (HSRP activo, prioridad 200) | 255.255.255.248 |
| | Gig0/1 | 172.16.0.6 | 255.255.255.252 |
| | Gig0/2 | 172.16.0.1 | 255.255.255.252 |
| | Gig0/0/0 | 172.16.0.18 | 255.255.255.252 |
| Router 2 | Gig0/0 | 192.168.1.3 (HSRP standby, prioridad 100) | 255.255.255.248 |
| | Gig0/1 | 172.16.0.5 | 255.255.255.252 |
| | Gig0/2 | 172.16.0.9 | 255.255.255.252 |
| Multicapa | Gig0/1 | 172.16.0.14 | 255.255.255.252 |
| | Gig0/2 | 172.16.0.2 | 255.255.255.252 |

### Tabla de servidores

| Servidor | IP | Máscara | Gateway |
|---|---|---|---|
| DHCP | 10.10.1.3 | 255.255.255.248 | 10.10.1.1 |
| DNS | 10.10.1.4 | 255.255.255.248 | 10.10.1.1 |
| WEB | 10.10.1.5 | 255.255.255.248 | 10.10.1.1 |

## Qué quedó configurado

- **Solo en el switch multicapa:** banner MOTD, contraseña `CISCO` en consola y VTY, `enable secret CLASS`, `service password-encryption` y descripciones de interfaz.
- **Nivel de acceso:**
  - VLAN 10, 20 y 30 en los Switches 1, 2 y 3. Los puertos de acceso son Fa0/1-10 en el Switch 1 y Fa0/10-20 en los Switches 2 y 3.
  - EtherChannel LACP: Po1 entre Switch1 y Switch2 (Fa0/21-22) y Po2 entre Switch2 y Switch3 (Fa0/1-2), ambos troncales.
- **Nivel de distribución:** el multicapa usa `ip routing` y tiene un troncal dot1q hacia el Switch2. Tiene SVI `192.168.x.1` con `ip helper-address 10.10.1.3` y puertos enrutados hacia Router0 y Router1.
- **Nivel core:**
  - Rutas estáticas con una ruta flotante de respaldo (AD 10).
  - HSRP v2, grupo 1, entre Router1 y Router2.
  - `config-register 0x2102`: estaba en 0x2142.
- **Servidores:** IPs en 10.10.1.0/29. El DHCP tiene pools para las VLAN 10/20/30 con DNS 10.10.1.4, y el DNS resuelve `www.web.com` → 10.10.1.5.

## Al abrir el `.pkt`

1. Espera de 30 a 60 s, o usa *Fast Forward Time*.
2. En PC3–PC11 entra a *IP Configuration* y presiona **DHCP**, o ejecuta `ipconfig /renew`.

> El `.pkt` se generó editando el XML interno del archivo y no se pudo abrir en Packet Tracer durante su preparación. Si algún equipo aparece sin configuración, pégale su script de `configuraciones/`.
