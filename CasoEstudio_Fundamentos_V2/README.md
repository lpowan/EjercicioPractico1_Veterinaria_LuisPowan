# Caso de Estudio – Fundamentos V2 · Solución (Packet Tracer)

- `Caso_de_Estudio-Fundamentos_V2_RESUELTO.pkt`: archivo resuelto. Tiene los 9 equipos Cisco configurados, los servidores en la red del enunciado y las PCs listas.
- `configuraciones/`: scripts CLI de cada equipo. Sirven de respaldo si algún equipo abre sin configuración: se pegan en su pestaña CLI.
- `herramientas/`: scripts con los que se descifró y regeneró el `.pkt` (`build.py`, `model.py`, `ptcodec.py`) y se validó el enrutamiento (`simulate.py`).

## Direccionamiento (según el enunciado)

| Red | Dirección | Uso |
|---|---|---|
| VLAN 10 Clientes / 20 Administrativo / 30 Finanzas | 192.168.10.0/24, 192.168.20.0/24, 192.168.30.0/24 | Hosts por DHCP. Gateway `.1` en el multicapa |
| Red Servidores | 10.10.1.0/29 | Router0 `.1`, DHCP `.3`, DNS `.4`, WEB `.5` |
| Intranet | 172.16.0.0, subredes /30 | Enlaces I–V |
| HSRP (red TI) | 192.168.1.0/29 | IP virtual `.1`, Router1 `.2`, Router2 `.3`, PC0–PC2 `.4`–`.6` |

> El diagrama del enunciado rotula la red de servidores como 10.10.10.0/29 y la red TI como 172.16.99.0/24. Se usó la lista de direccionamiento del texto, y las notas del `.pkt` se actualizaron para que coincidan.

### Tabla routers

| Dispositivo | Interfaz | Dirección IP | Máscara |
|---|---|---|---|
| Router 0 (RouterServidores) | Gig0/0 | 10.10.1.1 | 255.255.255.248 |
| | Gig0/1 | 172.16.0.13 | 255.255.255.252 |
| | Gig0/2 | 172.16.0.10 | 255.255.255.252 |
| | Gig0/0/0 | 172.16.0.17 | 255.255.255.252 |
| Router 1 (RouterRedundancia2) | Gig0/0 | 192.168.1.2 (HSRP activo, prioridad 200) | 255.255.255.248 |
| | Gig0/1 | 172.16.0.6 | 255.255.255.252 |
| | Gig0/2 | 172.16.0.1 | 255.255.255.252 |
| | Gig0/0/0 | 172.16.0.18 | 255.255.255.252 |
| Router 2 (RouterRedundancia1) | Gig0/0 | 192.168.1.3 (HSRP standby, prioridad 100) | 255.255.255.248 |
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

- **Hostname:** en todos los routers y switches.
- **Solo en el switch multicapa:**
  - Banner MOTD.
  - Contraseña `CISCO` en consola y VTY.
  - `enable secret CLASS` y `service password-encryption`.
  - Descripciones de interfaz (troncal Fa0/24, enlaces G0/1 y G0/2, SVI de las VLAN).
  - El resto de los equipos no tiene banner ni contraseñas.
- **Nivel de acceso:**
  - VLAN 10, 20 y 30 en los Switches 1, 2 y 3. Los puertos de acceso son Fa0/1-10 en el Switch 1 y Fa0/10-20 en los Switches 2 y 3.
  - EtherChannel LACP: Po1 entre Switch1 y Switch2 (Fa0/21-22) y Po2 entre Switch2 y Switch3 (Fa0/1-2), ambos troncales.
- **Nivel de distribución:** el multicapa usa `ip routing` y tiene un troncal dot1q hacia el Switch2. Tiene SVI `192.168.x.1` con `ip helper-address 10.10.1.3` y puertos enrutados hacia Router0 (enlace IV) y Router1 (enlace I).
- **Nivel core:**
  - Rutas estáticas con una ruta flotante de respaldo (AD 10) por el camino alterno.
  - HSRP v2, grupo 1, entre Router1 y Router2.
  - `config-register 0x2102`: estaba en 0x2142 y hacía que los routers perdieran la configuración al reiniciar.
- **Servidores:** DHCP con pools para las VLAN 10/20/30 (gateway `.1`, DNS 10.10.1.4). El DNS resuelve `www.web.com` → 10.10.1.5.

`herramientas/simulate.py` comprueba que hay conectividad entre todas las redes en operación normal, con Router1 o Router2 apagado y con cualquier enlace I–V caído.

## Al abrir el `.pkt`

1. Espera de 30 a 60 s, o usa *Fast Forward Time*, para que levanten STP, EtherChannel y HSRP.
2. En las PCs de las VLAN (PC3–PC11), entra a *Desktop → IP Configuration* y presiona **DHCP**, o ejecuta `ipconfig /renew`.
3. En *Scenario 0* hay pruebas PDU listas:
   - Las 3 originales: servidores → 172.16.0.14.
   - PC3 → WEB
   - PC6 → DNS
   - PC9 → DHCP
   - PC0 → WEB
   - PC4 → PC0
   - PC1 → IP virtual HSRP

> El `.pkt` se generó editando el XML interno del archivo y no se pudo abrir en Packet Tracer durante su preparación. Si algún equipo aparece sin configuración, pégale su script de `configuraciones/`.
