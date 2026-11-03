"""Modelo de la solucion del Caso de Estudio - Fundamentos V2 (segun el enunciado .docx).

Una sola fuente de verdad para: scripts CLI, running-config inyectado en el .pkt,
tablas de la documentacion y simulacion de rutas.

Direccionamiento del enunciado:
  VLAN 10/20/30 -> 192.168.10/20/30.0/24
  Red Servidores -> 10.10.1.0/29
  Intranet       -> 172.16.0.0 (subredes /30 para los enlaces I-V)
  HSRP           -> 192.168.1.0/29 (LAN de Router1/Router2 con Switch4 y PC0-PC2)
"""

ENABLE_SECRET = 'CLASS'
LINE_PASSWORD = 'CISCO'
# Hash/encoding tal como los guarda Packet Tracer (verificados con openssl / type 7)
ENABLE_SECRET_HASH = '$1$mERr$uhQEnb7HESVa4rbFgUgpe0'   # md5crypt("CLASS")
LINE_PASSWORD_T7 = '0802657D2A36'                       # type 7 de "CISCO"

DHCP_SERVER = '10.10.1.3'
DNS_SERVER = '10.10.1.4'
WEB_SERVER = '10.10.1.5'
VLANS = [(10, 'Clientes'), (20, 'Administrativo'), (30, 'Finanzas')]
TRUNK_VLANS = '10,20,30'

M30 = '255.255.255.252'
M24 = '255.255.255.0'
M29 = '255.255.255.248'

SRV = ('10.10.1.0', M29)
HSRP_NET = ('192.168.1.0', M29)
HSRP_VIP = '192.168.1.1'
LANS_VLAN = [('192.168.10.0', M24), ('192.168.20.0', M24), ('192.168.30.0', M24)]


def _routes(dests, nh, ad=None):
    return [(n, m, nh, ad) for n, m in dests]


# Enlaces de la intranet 172.16.0.0 /30, en el orden de las etiquetas I-V del diagrama
INTRANET = [
    ('I', '172.16.0.0', ('Router 1', 'Gig0/2', '172.16.0.1'), ('Multicapa', 'Gig0/2', '172.16.0.2')),
    ('II', '172.16.0.4', ('Router 2', 'Gig0/1', '172.16.0.5'), ('Router 1', 'Gig0/1', '172.16.0.6')),
    ('III', '172.16.0.8', ('Router 2', 'Gig0/2', '172.16.0.9'), ('Router 0', 'Gig0/2', '172.16.0.10')),
    ('IV', '172.16.0.12', ('Router 0', 'Gig0/1', '172.16.0.13'), ('Multicapa', 'Gig0/1', '172.16.0.14')),
    ('V', '172.16.0.16', ('Router 0', 'Gig0/0/0', '172.16.0.17'), ('Router 1', 'Gig0/0/0', '172.16.0.18')),
]

# --------------------------------------------------------------------------
# Cada dispositivo: lista de bloques (interfaces, comandos) en orden de CLI.
# 'X0/a-b' expande a un rango de interfaces.
# Las descripciones solo se configuran en el switch multicapa (segun indicacion).
# --------------------------------------------------------------------------
DEVICES = [
    dict(
        xml='Router0', label='Router 0', kind='router',
        banner='Estas conectandote al Router de la red de servidores',
        blocks=[
            (['GigabitEthernet0/0'], [f'ip address 10.10.1.1 {M29}', 'no shutdown']),
            (['GigabitEthernet0/1'], [f'ip address 172.16.0.13 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], [f'ip address 172.16.0.10 {M30}', 'no shutdown']),
            (['GigabitEthernet0/0/0'], [f'ip address 172.16.0.17 {M30}', 'no shutdown']),
        ],
        routes=_routes(LANS_VLAN, '172.16.0.14') + _routes([HSRP_NET], '172.16.0.18')
        + _routes(LANS_VLAN, '172.16.0.18', 10) + _routes([HSRP_NET], '172.16.0.9', 10),
    ),
    dict(
        xml='Router1', label='Router 1', kind='router',
        banner='Estas conectandote al Router de redundancia 2',
        blocks=[
            (['GigabitEthernet0/0'], [f'ip address 192.168.1.2 {M29}',
                                      'standby version 2', f'standby 1 ip {HSRP_VIP}',
                                      'standby 1 priority 200', 'standby 1 preempt', 'no shutdown']),
            (['GigabitEthernet0/1'], [f'ip address 172.16.0.6 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], [f'ip address 172.16.0.1 {M30}', 'no shutdown']),
            (['GigabitEthernet0/0/0'], [f'ip address 172.16.0.18 {M30}', 'no shutdown']),
        ],
        routes=_routes(LANS_VLAN, '172.16.0.2') + _routes([SRV], '172.16.0.17')
        + _routes(LANS_VLAN, '172.16.0.17', 10) + _routes([SRV], '172.16.0.5', 10),
    ),
    dict(
        xml='Router2', label='Router 2', kind='router',
        banner='Estas conectandote al Router de redundancia 1',
        blocks=[
            (['GigabitEthernet0/0'], [f'ip address 192.168.1.3 {M29}',
                                      'standby version 2', f'standby 1 ip {HSRP_VIP}',
                                      'standby 1 priority 100', 'standby 1 preempt', 'no shutdown']),
            (['GigabitEthernet0/1'], [f'ip address 172.16.0.5 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], [f'ip address 172.16.0.9 {M30}', 'no shutdown']),
        ],
        routes=_routes([SRV] + LANS_VLAN, '172.16.0.10') + _routes([SRV] + LANS_VLAN, '172.16.0.6', 10),
    ),
    dict(
        xml='Multilayer Switch0', label='Multicapa', kind='mls',
        banner='Estas conectandote al Switch multicapa de distribucion',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/24'], ['description Troncal 802.1Q hacia switch Administrativo (VLAN 10,20,30)',
                                    'switchport trunk encapsulation dot1q', 'switchport mode trunk',
                                    f'switchport trunk allowed vlan {TRUNK_VLANS}', 'no shutdown']),
            (['GigabitEthernet0/1'], ['description Enlace IV capa 3 hacia RouterServidores (Router0 Gig0/1)',
                                      'no switchport', f'ip address 172.16.0.14 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], ['description Enlace I capa 3 hacia RouterRedundancia2 (Router1 Gig0/2)',
                                      'no switchport', f'ip address 172.16.0.2 {M30}', 'no shutdown']),
        ],
        svis=[
            (10, '192.168.10.1', M24, ['description Gateway VLAN 10 Clientes + relay DHCP',
                                       f'ip helper-address {DHCP_SERVER}']),
            (20, '192.168.20.1', M24, ['description Gateway VLAN 20 Administrativo + relay DHCP',
                                       f'ip helper-address {DHCP_SERVER}']),
            (30, '192.168.30.1', M24, ['description Gateway VLAN 30 Finanzas + relay DHCP',
                                       f'ip helper-address {DHCP_SERVER}']),
        ],
        routes=_routes([SRV], '172.16.0.13') + _routes([HSRP_NET], '172.16.0.1')
        + _routes([SRV], '172.16.0.1', 10) + _routes([HSRP_NET], '172.16.0.13', 10),
    ),
    dict(
        xml='Switch1', label='Switch 1', kind='l2',
        banner='Estas conectandote al Switch de Clientes',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/1-10'], ['switchport mode access', 'switchport access vlan 10',
                                      'spanning-tree portfast', 'no shutdown']),
            (['FastEthernet0/21-22'], ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                       'channel-group 1 mode active', 'no shutdown']),
        ],
        portchannels=[(1, ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}'])],
    ),
    dict(
        xml='Switch2', label='Switch 2', kind='l2',
        banner='Estas conectandote al Switch de administracion',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/10-20'], ['switchport mode access', 'switchport access vlan 20',
                                       'spanning-tree portfast', 'no shutdown']),
            (['FastEthernet0/21-22'], ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                       'channel-group 1 mode active', 'no shutdown']),
            (['FastEthernet0/1-2'], ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                     'channel-group 2 mode active', 'no shutdown']),
            (['FastEthernet0/24'], ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                    'no shutdown']),
        ],
        portchannels=[(1, ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}']),
                      (2, ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}'])],
    ),
    dict(
        xml='Switch3', label='Switch 3', kind='l2',
        banner='Estas conectandote al Switch de Finanzas',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/10-20'], ['switchport mode access', 'switchport access vlan 30',
                                       'spanning-tree portfast', 'no shutdown']),
            (['FastEthernet0/1-2'], ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                     'channel-group 2 mode active', 'no shutdown']),
        ],
        portchannels=[(2, ['switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}'])],
    ),
    dict(
        xml='Switch0', label='Switch 0', kind='l2',
        banner='Estas conectandote al Switch de la red de servidores',
        blocks=[
            (['FastEthernet0/1-10'], ['switchport mode access', 'spanning-tree portfast', 'no shutdown']),
        ],
    ),
    dict(
        xml='Switch4', label='Switch 4', kind='l2',
        banner='Estas conectandote al Switch de la red de TI',
        blocks=[
            (['FastEthernet0/1-10'], ['switchport mode access', 'spanning-tree portfast', 'no shutdown']),
        ],
    ),
]

# Servidores (IP estatica) y PCs
SERVERS = [('DHCP', DHCP_SERVER), ('DNS', DNS_SERVER), ('WEB', WEB_SERVER)]
SERVER_GW = '10.10.1.1'
DNS_RECORDS = {'www.web.com': WEB_SERVER, 'www.micorreo.com': '10.10.1.6'}
PCS_DHCP = ['PC%d' % i for i in range(3, 12)]                     # VLAN 10/20/30 -> DHCP
PCS_STATIC = [('PC0', '192.168.1.4'), ('PC1', '192.168.1.5'), ('PC2', '192.168.1.6')]  # red HSRP/TI


def expand(spec):
    """'FastEthernet0/1-10' -> ['FastEthernet0/1', ..., 'FastEthernet0/10']"""
    head, _, last = spec.rpartition('/')
    if '-' in last:
        a, b = last.split('-')
        return [f'{head}/{i}' for i in range(int(a), int(b) + 1)]
    return [spec]
