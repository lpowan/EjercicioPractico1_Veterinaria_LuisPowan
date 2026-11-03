# Caso de Estudio – Fundamentos V2 · Solución

| Archivo | Para qué sirve |
|---|---|
| `Caso_de_Estudio-Fundamentos_V2_RESUELTO.pkt` | El mismo archivo original, con los 9 equipos Cisco ya configurados, las PCs en DHCP y pruebas PDU agregadas. |
| `configuraciones/00_TODOS_LOS_EQUIPOS.txt` | Scripts CLI de todos los equipos (uno por archivo en la misma carpeta) para pegar en Packet Tracer. |
| `herramientas/` | Scripts con los que se descifró y regeneró el `.pkt` y se validó el enrutamiento (`simulate.py`). |

---

## 1. Qué había en el archivo original

- La topología está completa y cableada, y los **servidores ya estaban bien configurados**: DHCP `10.10.10.3`, DNS `10.10.10.4` (`www.web.com` → `10.10.10.5`) y WEB `10.10.10.5`, todos con gateway `10.10.10.1`.
- **Los 9 equipos Cisco estaban en configuración de fábrica.** El historial de comandos guardado en el `.pkt` muestra que hubo un intento anterior y que se perdió por estas razones:
  - En los 3 routers se ejecutó `config-register 0x2142` seguido de `reload`. Con ese valor, el router **ignora la NVRAM** al arrancar. La solución lo deja en `config-register 0x2102`.
  - Los switches se reiniciaron sin guardar.
- Errores del intento anterior que se corrigieron:
  - `ip helper-address 172.16.0.6`: debe apuntar al servidor DHCP `10.10.10.3`.
  - Ruta por defecto a `172.160.21.22`: esa dirección no existe en la red.
  - El router de TI tenía la `.1`, que es la que corresponde a la IP virtual HSRP.
  - Le faltaba `standby ip` a HSRP.

## 2. Supuestos (el enunciado no viene dentro del `.pkt`)

Todo se tomó de las notas del diagrama y del intento anterior:

| Nota en el diagrama | Interpretación aplicada |
|---|---|
| `Intranet 172.16.0.0/24` + enlaces **I, II, III, IV, V** | Se divide en subredes /30 y se asignan en el orden de los números romanos: I = `.0/30`, II = `.4/30`, III = `.8/30`, IV = `.12/30`, V = `.16/30`. |
| `HSRP`, `100` (junto a Router2), `200` (junto a Router1) | HSRP v2, grupo 1, IP virtual `172.16.99.1`. Router1 es el activo (prioridad 200, preempt) y Router2 el standby (prioridad 100). |
| `VLAN 10 Clientes Fa0/1-Fa0/10`, `VLAN 20 Administrativo Fa0/10-Fa0/20`, `VLAN 30 Finanzas Fa0/10-Fa0/20` | Puertos de acceso de Switch1, Switch2 y Switch3 respectivamente. |
| `RED Servidores 10.10.10.0/29 Fa0/1-Fa0/10`, `RED TI 172.16.99.0/24 Fa0/1-Fa0/10` | Puertos de acceso de Switch0 y Switch4. |
| Prueba PDU que ya traía el archivo (servidores → `172.16.0.14`) | El switch multicapa tiene `172.16.0.14` en el enlace IV. Coincide con el plan. |

Otras decisiones:

- **Enrutamiento:** se usaron rutas estáticas con **rutas flotantes** (distancia administrativa 10) para aprovechar los enlaces redundantes, igual que en el intento anterior. Se validó con `herramientas/simulate.py` que hay conectividad total en operación normal y con cualquier enlace o router de redundancia caído.
- **Nombres y contraseñas:** se mantuvieron los del intento anterior.
  - `enable secret CLASS`
  - Consola y VTY: `CISCO`
  - SSH: usuario `admin` / `CISCO`, dominio `casoestudio.local`
- **TI por DHCP:** se agregó al servidor DHCP un pool `TI` (`172.16.99.10`–`.59`, gateway `172.16.99.1`, DNS `10.10.10.4`).
- **Buenas prácticas:** se apagaron los puertos que no se usan, se activó `portfast` en los puertos de acceso y se dio una IP de administración a cada switch.

## 3. Tabla de direccionamiento

| Equipo (hostname) | Interfaz | IP | Máscara | Conecta con |
|---|---|---|---|---|
| Router0 (**RouterServidores**) | G0/0 | 10.10.10.1 | 255.255.255.248 | LAN Servidores (Switch0) |
| | G0/1 | 172.16.0.13 | 255.255.255.252 | Enlace IV → Multicapa |
| | G0/2 | 172.16.0.10 | 255.255.255.252 | Enlace III → Router2 |
| | G0/0/0 (fibra) | 172.16.0.17 | 255.255.255.252 | Enlace V → Router1 |
| Router1 (**RouterRedundancia2**) | G0/0 | 172.16.99.2 (VIP .1) | 255.255.255.0 | LAN TI – HSRP **activo** (200) |
| | G0/1 | 172.16.0.6 | 255.255.255.252 | Enlace II → Router2 |
| | G0/2 | 172.16.0.1 | 255.255.255.252 | Enlace I → Multicapa |
| | G0/0/0 (fibra) | 172.16.0.18 | 255.255.255.252 | Enlace V → Router0 |
| Router2 (**RouterRedundancia1**) | G0/0 | 172.16.99.3 (VIP .1) | 255.255.255.0 | LAN TI – HSRP standby (100) |
| | G0/1 | 172.16.0.5 | 255.255.255.252 | Enlace II → Router1 |
| | G0/2 | 172.16.0.9 | 255.255.255.252 | Enlace III → Router0 |
| Multilayer Switch0 (**SwitchMulticapaDistribucion**) | G0/1 (routed) | 172.16.0.14 | 255.255.255.252 | Enlace IV → Router0 |
| | G0/2 (routed) | 172.16.0.2 | 255.255.255.252 | Enlace I → Router1 |
| | VLAN 10 / 20 / 30 | 192.168.10.1 / 20.1 / 30.1 | 255.255.255.0 | Gateways de las VLAN (con `ip helper-address 10.10.10.3`) |
| Switch1 (**Clientes**) | VLAN 10 | 192.168.10.254 | 255.255.255.0 | Gestión (gw .1) |
| Switch2 (**Administrativo**) | VLAN 20 | 192.168.20.254 | 255.255.255.0 | Gestión (gw .1) |
| Switch3 (**Finanzas**) | VLAN 30 | 192.168.30.254 | 255.255.255.0 | Gestión (gw .1) |
| Switch0 (**Red-servidores**) | VLAN 1 | 10.10.10.2 | 255.255.255.248 | Gestión (gw 10.10.10.1) |
| Switch4 (**Red-TI**) | VLAN 1 | 172.16.99.254 | 255.255.255.0 | Gestión (gw 172.16.99.1) |
| DHCP / DNS / WEB | Fa0 | 10.10.10.3 / .4 / .5 | 255.255.255.248 | Sin cambios |
| PC0–PC11 | Fa0 | DHCP | — | VLAN 10/20/30: `.2–.65`; TI: `.10–.59` |

## 4. Capa 2: VLANs, troncales y EtherChannel

| Switch | Puertos de acceso | Troncales | Puertos apagados |
|---|---|---|---|
| Clientes (Switch1) | Fa0/1-10 → VLAN 10 | Po1 (Fa0/21-22, LACP) → Administrativo | Fa0/11-20, Fa0/23-24, G0/1-2 |
| Administrativo (Switch2) | Fa0/10-20 → VLAN 20 | Po1 (Fa0/21-22) → Clientes, Po2 (Fa0/1-2) → Finanzas, Fa0/24 → Multicapa | Fa0/3-9, Fa0/23, G0/1-2 |
| Finanzas (Switch3) | Fa0/10-20 → VLAN 30 | Po2 (Fa0/1-2, LACP) → Administrativo | Fa0/3-9, Fa0/21-24, G0/1-2 |
| Multicapa | — | Fa0/24 (dot1q) → Administrativo | Fa0/1-23 |
| Red-servidores (Switch0) | Fa0/1-10 (VLAN 1) | — (G0/1 → Router0) | Fa0/11-24, G0/2 |
| Red-TI (Switch4) | Fa0/1-10 (VLAN 1) | — (G0/1 → Router1, G0/2 → Router2) | Fa0/11-24 |

En todos los troncales se usa `switchport trunk allowed vlan 10,20,30`.

## 5. Enrutamiento estático

| Equipo | Destino | Ruta principal | Ruta flotante (AD 10) |
|---|---|---|---|
| RouterServidores | 192.168.10/20/30.0/24 | 172.16.0.14 (IV, Multicapa) | 172.16.0.18 (V, Router1) |
| | 172.16.99.0/24 | 172.16.0.18 (V, Router1) | 172.16.0.9 (III, Router2) |
| RouterRedundancia2 | 192.168.10/20/30.0/24 | 172.16.0.2 (I, Multicapa) | 172.16.0.17 (V, Router0) |
| | 10.10.10.0/29 | 172.16.0.17 (V, Router0) | 172.16.0.5 (II, Router2) |
| RouterRedundancia1 | 10.10.10.0/29 y 192.168.x.0/24 | 172.16.0.10 (III, Router0) | 172.16.0.6 (II, Router1) |
| Multicapa | 10.10.10.0/29 | 172.16.0.13 (IV, Router0) | 172.16.0.1 (I, Router1) |
| | 172.16.99.0/24 | 172.16.0.1 (I, Router1) | 172.16.0.13 (IV, Router0) |

Resultado de `python3 herramientas/simulate.py`: hay conectividad entre las 5 LAN en operación normal, con Router1 apagado (HSRP pasa a Router2), con Router2 apagado y con cada enlace I–V caído.

## 6. Cómo usarlo

### Opción A: abrir el `.pkt` resuelto (Packet Tracer 8.2.2 o superior)
1. Abre `Caso_de_Estudio-Fundamentos_V2_RESUELTO.pkt` y espera de 30 a 60 s, o usa *Fast Forward Time* varias veces, para que converjan STP, EtherChannel y HSRP.
2. En cada PC entra a *Desktop → IP Configuration* y selecciona **DHCP**, o ejecuta `ipconfig /renew` en el *Command Prompt*.
3. Para SSH, genera las llaves RSA en cada router y switch, porque no se guardan dentro de la configuración:
   ```
   enable
   configure terminal
   crypto key generate rsa general-keys modulus 1024
   ip ssh version 2
   end
   write memory
   ```
4. Revisa con `show running-config` que cada equipo tenga su hostname. Si alguno abre sin configuración, pégale su script de `configuraciones/`.

> El `.pkt` se generó editando el XML interno del archivo y no se pudo abrir en Packet Tracer durante su preparación. Si da cualquier problema, usa la opción B, que produce exactamente la misma configuración.

### Opción B: pegar los scripts en el archivo original
Pega el script de cada equipo en su pestaña **CLI**, en este orden:
1. Switch1
2. Switch2
3. Switch3
4. Multilayer Switch0
5. Switch0
6. Switch4
7. Router0
8. Router1
9. Router2

Después, en el servidor **DHCP** (*Services → DHCP*) agrega el pool `TI`:
- Default Gateway: `172.16.99.1`
- DNS: `10.10.10.4`
- Start IP: `172.16.99.10`
- Máscara: `255.255.255.0`
- Max users: `50`

Por último, pon las PCs en DHCP.

> Si un router pregunta *“initial configuration dialog? [yes/no]”*, responde `no`. Si `crypto key generate rsa general-keys modulus 1024` no se acepta, usa `crypto key generate rsa` y escribe `1024` cuando lo pida.

## 7. Verificación

| Comando (equipo) | Resultado esperado |
|---|---|
| `show etherchannel summary` (Clientes / Administrativo / Finanzas) | Po1 y Po2 en estado `(SU)` con los puertos `(P)` |
| `show interfaces trunk` (Administrativo, Multicapa) | Po1, Po2 y Fa0/24 en trunking con VLAN 10,20,30 |
| `show vlan brief` | VLAN 10 Clientes, 20 Administrativo, 30 Finanzas con sus puertos |
| `show ip interface brief` (routers, Multicapa) | Todas las interfaces usadas `up/up` |
| `show standby brief` (Router1 / Router2) | Router1 `Active` con prioridad 200, Router2 `Standby` con prioridad 100, VIP `172.16.99.1` |
| `show ip route static` | Rutas `S` principales. Las flotantes aparecen solo si cae el enlace principal |
| `ipconfig` (PC) | IP dentro del pool correspondiente, gateway `.1`, DNS `10.10.10.4` |
| `ping 10.10.10.5` / navegador `www.web.com` (cualquier PC) | Responde / carga la página |
| Apagar Router1 y hacer `ping` continuo desde una PC de TI | Router2 pasa a `Active` y vuelve la conectividad |

En el panel de simulación del archivo resuelto (*Scenario 0*) quedaron 8 pruebas PDU: las 3 originales (servidores → `172.16.0.14`) y 5 nuevas (PC3 → WEB, PC6 → DNS, PC9 → DHCP, PC0 → WEB, PC4 → VIP HSRP). Haz clic en cada una después de que las PCs obtengan IP por DHCP.
