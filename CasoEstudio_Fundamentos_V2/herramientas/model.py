"""Modelo de la solucion del Caso de Estudio - Fundamentos V2.

Una sola fuente de verdad para: scripts CLI, running-config inyectado en el .pkt,
tabla de direccionamiento y simulacion de rutas.
"""

DOMAIN = 'casoestudio.local'
ENABLE_SECRET = 'CLASS'
LINE_PASSWORD = 'CISCO'
SSH_USER = 'admin'
SSH_PASS = 'CISCO'
# Hashes/encodings tal como los guarda Packet Tracer (verificados con openssl / type 7)
ENABLE_SECRET_HASH = '$1$mERr$uhQEnb7HESVa4rbFgUgpe0'   # md5crypt("CLASS")
USER_SECRET_HASH = '$1$mERr$NJdjwh5wX8Ia/X8aC4RIu.'     # md5crypt("CISCO")
LINE_PASSWORD_T7 = '0802657D2A36'                       # type 7 de "CISCO"

DHCP_SERVER = '10.10.10.3'
VLANS = [(10, 'Clientes'), (20, 'Administrativo'), (30, 'Finanzas')]
TRUNK_VLANS = '10,20,30'

M30 = '255.255.255.252'
M24 = '255.255.255.0'
M29 = '255.255.255.248'

# --------------------------------------------------------------------------
# Cada dispositivo: lista de bloques (interfaces, comandos) en orden de CLI.
# Las interfaces se escriben como en IOS completo; 'X0/a-b' expande rango.
# --------------------------------------------------------------------------
DEVICES = [
    dict(
        xml='Router0', hostname='RouterServidores', kind='router',
        banner='Estas conectandote al Router de la red de servidores',
        blocks=[
            (['GigabitEthernet0/0'], ['description LAN Servidores 10.10.10.0/29',
                                      f'ip address 10.10.10.1 {M29}', 'no shutdown']),
            (['GigabitEthernet0/1'], ['description Enlace IV hacia SwitchMulticapaDistribucion',
                                      f'ip address 172.16.0.13 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], ['description Enlace III hacia RouterRedundancia1',
                                      f'ip address 172.16.0.10 {M30}', 'no shutdown']),
            (['GigabitEthernet0/0/0'], ['description Enlace V (fibra) hacia RouterRedundancia2',
                                        f'ip address 172.16.0.17 {M30}', 'no shutdown']),
        ],
        routes=[
            ('192.168.10.0', M24, '172.16.0.14', None),
            ('192.168.20.0', M24, '172.16.0.14', None),
            ('192.168.30.0', M24, '172.16.0.14', None),
            ('172.16.99.0', M24, '172.16.0.18', None),
            ('192.168.10.0', M24, '172.16.0.18', 10),
            ('192.168.20.0', M24, '172.16.0.18', 10),
            ('192.168.30.0', M24, '172.16.0.18', 10),
            ('172.16.99.0', M24, '172.16.0.9', 10),
        ],
    ),
    dict(
        xml='Router1', hostname='RouterRedundancia2', kind='router',
        banner='Estas conectandote al Router de redundancia 2',
        blocks=[
            (['GigabitEthernet0/0'], ['description LAN TI 172.16.99.0/24 - HSRP activo',
                                      f'ip address 172.16.99.2 {M24}',
                                      f'ip helper-address {DHCP_SERVER}',
                                      'standby version 2', 'standby 1 ip 172.16.99.1',
                                      'standby 1 priority 200', 'standby 1 preempt', 'no shutdown']),
            (['GigabitEthernet0/1'], ['description Enlace II hacia RouterRedundancia1',
                                      f'ip address 172.16.0.6 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], ['description Enlace I hacia SwitchMulticapaDistribucion',
                                      f'ip address 172.16.0.1 {M30}', 'no shutdown']),
            (['GigabitEthernet0/0/0'], ['description Enlace V (fibra) hacia RouterServidores',
                                        f'ip address 172.16.0.18 {M30}', 'no shutdown']),
        ],
        routes=[
            ('192.168.10.0', M24, '172.16.0.2', None),
            ('192.168.20.0', M24, '172.16.0.2', None),
            ('192.168.30.0', M24, '172.16.0.2', None),
            ('10.10.10.0', M29, '172.16.0.17', None),
            ('192.168.10.0', M24, '172.16.0.17', 10),
            ('192.168.20.0', M24, '172.16.0.17', 10),
            ('192.168.30.0', M24, '172.16.0.17', 10),
            ('10.10.10.0', M29, '172.16.0.5', 10),
        ],
    ),
    dict(
        xml='Router2', hostname='RouterRedundancia1', kind='router',
        banner='Estas conectandote al Router de redundancia 1',
        blocks=[
            (['GigabitEthernet0/0'], ['description LAN TI 172.16.99.0/24 - HSRP standby',
                                      f'ip address 172.16.99.3 {M24}',
                                      f'ip helper-address {DHCP_SERVER}',
                                      'standby version 2', 'standby 1 ip 172.16.99.1',
                                      'standby 1 priority 100', 'standby 1 preempt', 'no shutdown']),
            (['GigabitEthernet0/1'], ['description Enlace II hacia RouterRedundancia2',
                                      f'ip address 172.16.0.5 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], ['description Enlace III hacia RouterServidores',
                                      f'ip address 172.16.0.9 {M30}', 'no shutdown']),
        ],
        routes=[
            ('10.10.10.0', M29, '172.16.0.10', None),
            ('192.168.10.0', M24, '172.16.0.10', None),
            ('192.168.20.0', M24, '172.16.0.10', None),
            ('192.168.30.0', M24, '172.16.0.10', None),
            ('10.10.10.0', M29, '172.16.0.6', 10),
            ('192.168.10.0', M24, '172.16.0.6', 10),
            ('192.168.20.0', M24, '172.16.0.6', 10),
            ('192.168.30.0', M24, '172.16.0.6', 10),
        ],
    ),
    dict(
        xml='Multilayer Switch0', hostname='SwitchMulticapaDistribucion', kind='mls',
        banner='Estas conectandote al Switch multicapa de distribucion',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/24'], ['description Troncal hacia Administrativo',
                                    'switchport trunk encapsulation dot1q', 'switchport mode trunk',
                                    f'switchport trunk allowed vlan {TRUNK_VLANS}', 'no shutdown']),
            (['GigabitEthernet0/1'], ['description Enlace IV hacia RouterServidores', 'no switchport',
                                      f'ip address 172.16.0.14 {M30}', 'no shutdown']),
            (['GigabitEthernet0/2'], ['description Enlace I hacia RouterRedundancia2', 'no switchport',
                                      f'ip address 172.16.0.2 {M30}', 'no shutdown']),
            (['FastEthernet0/1-23'], ['shutdown']),
        ],
        svis=[
            (10, '192.168.10.1', M24, [f'ip helper-address {DHCP_SERVER}']),
            (20, '192.168.20.1', M24, [f'ip helper-address {DHCP_SERVER}']),
            (30, '192.168.30.1', M24, [f'ip helper-address {DHCP_SERVER}']),
        ],
        routes=[
            ('10.10.10.0', M29, '172.16.0.13', None),
            ('172.16.99.0', M24, '172.16.0.1', None),
            ('10.10.10.0', M29, '172.16.0.1', 10),
            ('172.16.99.0', M24, '172.16.0.13', 10),
        ],
    ),
    dict(
        xml='Switch1', hostname='Clientes', kind='l2',
        banner='Estas conectandote al Switch de Clientes',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/1-10'], ['description Puertos VLAN 10 Clientes', 'switchport mode access',
                                      'switchport access vlan 10', 'spanning-tree portfast', 'no shutdown']),
            (['FastEthernet0/21-22'], ['description EtherChannel Po1 hacia Administrativo',
                                       'switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                       'channel-group 1 mode active', 'no shutdown']),
            (['FastEthernet0/11-20', 'FastEthernet0/23-24', 'GigabitEthernet0/1-2'], ['shutdown']),
        ],
        portchannels=[(1, ['description EtherChannel LACP hacia Administrativo', 'switchport mode trunk',
                           f'switchport trunk allowed vlan {TRUNK_VLANS}'])],
        svis=[(10, '192.168.10.254', M24, [])],
        gateway='192.168.10.1',
    ),
    dict(
        xml='Switch2', hostname='Administrativo', kind='l2',
        banner='Estas conectandote al Switch de administracion',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/10-20'], ['description Puertos VLAN 20 Administrativo', 'switchport mode access',
                                       'switchport access vlan 20', 'spanning-tree portfast', 'no shutdown']),
            (['FastEthernet0/21-22'], ['description EtherChannel Po1 hacia Clientes',
                                       'switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                       'channel-group 1 mode active', 'no shutdown']),
            (['FastEthernet0/1-2'], ['description EtherChannel Po2 hacia Finanzas',
                                     'switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                     'channel-group 2 mode active', 'no shutdown']),
            (['FastEthernet0/24'], ['description Troncal hacia SwitchMulticapaDistribucion',
                                    'switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                    'no shutdown']),
            (['FastEthernet0/3-9', 'FastEthernet0/23', 'GigabitEthernet0/1-2'], ['shutdown']),
        ],
        portchannels=[(1, ['description EtherChannel LACP hacia Clientes', 'switchport mode trunk',
                           f'switchport trunk allowed vlan {TRUNK_VLANS}']),
                      (2, ['description EtherChannel LACP hacia Finanzas', 'switchport mode trunk',
                           f'switchport trunk allowed vlan {TRUNK_VLANS}'])],
        svis=[(20, '192.168.20.254', M24, [])],
        gateway='192.168.20.1',
    ),
    dict(
        xml='Switch3', hostname='Finanzas', kind='l2',
        banner='Estas conectandote al Switch de Finanzas',
        vlans=VLANS,
        blocks=[
            (['FastEthernet0/10-20'], ['description Puertos VLAN 30 Finanzas', 'switchport mode access',
                                       'switchport access vlan 30', 'spanning-tree portfast', 'no shutdown']),
            (['FastEthernet0/1-2'], ['description EtherChannel Po2 hacia Administrativo',
                                     'switchport mode trunk', f'switchport trunk allowed vlan {TRUNK_VLANS}',
                                     'channel-group 2 mode active', 'no shutdown']),
            (['FastEthernet0/3-9', 'FastEthernet0/21-24', 'GigabitEthernet0/1-2'], ['shutdown']),
        ],
        portchannels=[(2, ['description EtherChannel LACP hacia Administrativo', 'switchport mode trunk',
                           f'switchport trunk allowed vlan {TRUNK_VLANS}'])],
        svis=[(30, '192.168.30.254', M24, [])],
        gateway='192.168.30.1',
    ),
    dict(
        xml='Switch0', hostname='Red-servidores', kind='l2',
        banner='Estas conectandote al Switch de la red de servidores',
        blocks=[
            (['FastEthernet0/1-10'], ['description Puertos Red de Servidores', 'switchport mode access',
                                      'spanning-tree portfast', 'no shutdown']),
            (['GigabitEthernet0/1'], ['description Enlace hacia RouterServidores', 'no shutdown']),
            (['FastEthernet0/11-24', 'GigabitEthernet0/2'], ['shutdown']),
        ],
        svis=[(1, '10.10.10.2', M29, [])],
        gateway='10.10.10.1',
    ),
    dict(
        xml='Switch4', hostname='Red-TI', kind='l2',
        banner='Estas conectandote al Switch de la red de TI',
        blocks=[
            (['FastEthernet0/1-10'], ['description Puertos Red de TI', 'switchport mode access',
                                      'spanning-tree portfast', 'no shutdown']),
            (['GigabitEthernet0/1'], ['description Enlace hacia RouterRedundancia2', 'no shutdown']),
            (['GigabitEthernet0/2'], ['description Enlace hacia RouterRedundancia1', 'no shutdown']),
            (['FastEthernet0/11-24'], ['shutdown']),
        ],
        svis=[(1, '172.16.99.254', M24, [])],
        gateway='172.16.99.1',
    ),
]

# Pool DHCP nuevo para la red de TI (se agrega al servidor DHCP existente)
TI_POOL = dict(name='TI', network='172.16.99.0', mask=M24, gw='172.16.99.1',
               dns='10.10.10.4', start='172.16.99.10', max_users=50)

PCS_DHCP = ['PC%d' % i for i in range(12)]


def expand(spec):
    """'FastEthernet0/1-10' -> ['FastEthernet0/1', ..., 'FastEthernet0/10']"""
    head, _, last = spec.rpartition('/')
    if '-' in last:
        a, b = last.split('-')
        return [f'{head}/{i}' for i in range(int(a), int(b) + 1)]
    return [spec]


ABBR = {'FastEthernet': 'fa', 'GigabitEthernet': 'g'}


def short(spec):
    for k, v in ABBR.items():
        if spec.startswith(k):
            return v + spec[len(k):]
    return spec
