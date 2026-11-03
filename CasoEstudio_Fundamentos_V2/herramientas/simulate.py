"""Simulacion de enrutamiento estatico (rutas + flotantes + HSRP) con escenarios de falla."""
import ipaddress as ip
import itertools
from model import DEVICES

L3 = {d['xml']: d for d in DEVICES if d['kind'] in ('router', 'mls')}

# Interfaces L3 por dispositivo: (iface, ip, net)
def l3_ifaces(d):
    out = []
    for ifs, cmds in d['blocks']:
        for c in cmds:
            if c.startswith('ip address'):
                _, _, a, m = c.split()
                out.append((ifs[0], a, ip.ip_network(f'{a}/{m}', strict=False)))
    for vid, a, m, _ in d.get('svis', []):
        out.append((f'Vlan{vid}', a, ip.ip_network(f'{a}/{m}', strict=False)))
    return out

IFACES = {n: l3_ifaces(d) for n, d in L3.items()}
LINKS = {  # nombre enlace -> extremos (dispositivo, interfaz)
    'I': [('Router1', 'GigabitEthernet0/2'), ('Multilayer Switch0', 'GigabitEthernet0/2')],
    'II': [('Router2', 'GigabitEthernet0/1'), ('Router1', 'GigabitEthernet0/1')],
    'III': [('Router2', 'GigabitEthernet0/2'), ('Router0', 'GigabitEthernet0/2')],
    'IV': [('Router0', 'GigabitEthernet0/1'), ('Multilayer Switch0', 'GigabitEthernet0/1')],
    'V': [('Router0', 'GigabitEthernet0/0/0'), ('Router1', 'GigabitEthernet0/0/0')],
}
LANS = {
    'Servidores': ('10.10.1.5', ['Router0']),
    'TI': ('192.168.1.4', ['Router1', 'Router2']),
    'VLAN10': ('192.168.10.2', ['Multilayer Switch0']),
    'VLAN20': ('192.168.20.2', ['Multilayer Switch0']),
    'VLAN30': ('192.168.30.2', ['Multilayer Switch0']),
}

# Comprobar que cada enlace usa la misma subred en ambos extremos
for name, ends in LINKS.items():
    nets = {next(n for i, a, n in IFACES[d] if i == f) for d, f in ends}
    assert len(nets) == 1, (name, nets)


def run(down_devs=(), down_links=()):
    down_if = set()
    for l in down_links:
        down_if |= set(LINKS[l])
    for l, ends in LINKS.items():
        if any(d in down_devs for d, _ in ends):
            down_if |= set(ends)
    up = {n for n in L3 if n not in down_devs}

    def conn(dev):
        return [(i, a, n) for i, a, n in IFACES[dev] if (dev, i) not in down_if]

    def owner(addr):
        for dev in up:
            for i, a, n in conn(dev):
                if a == addr:
                    return dev
        return None

    def fwd(dev, dst):
        dst = ip.ip_address(dst)
        path = [dev]
        for _ in range(10):
            if any(dst in n for _, _, n in conn(dev)):
                return path
            cands = []
            for net, mask, nh, ad in L3[dev].get('routes', []):
                pfx = ip.ip_network(f'{net}/{mask}')
                if dst in pfx and any(ip.ip_address(nh) in n for _, _, n in conn(dev)):
                    cands.append((-pfx.prefixlen, ad or 1, nh))
            if not cands:
                return path + ['SIN RUTA']
            nh = sorted(cands)[0][2]
            nxt = owner(nh)
            if nxt is None:
                return path + [f'next-hop {nh} caido']
            dev = nxt
            path.append(dev)
        return path + ['BUCLE']

    def gateway(lan):
        gws = [g for g in LANS[lan][1] if g in up]
        if lan == 'TI':  # HSRP: activo = prioridad mas alta (Router1=200) si esta arriba
            gws = [g for g in gws if ('Router1' if g == 'Router1' else 'Router2', 'GigabitEthernet0/0') not in down_if]
            return gws[0] if gws else None
        return gws[0] if gws else None

    ok = True
    for a, b in itertools.permutations(LANS, 2):
        gw = gateway(a)
        if gw is None or gateway(b) is None:
            continue
        p = fwd(gw, LANS[b][0])
        good = p[-1] in L3 and any(ip.ip_address(LANS[b][0]) in n for _, _, n in conn(p[-1]))
        ok &= good
        if not good:
            print(f'   FALLA {a} -> {b}: {p}')
    return ok


SCENARIOS = [
    ('Normal', (), ()),
    ('Router1 (HSRP activo) apagado', ('Router1',), ()),
    ('Router2 apagado', ('Router2',), ()),
    ('Enlace I caido', (), ('I',)),
    ('Enlace II caido', (), ('II',)),
    ('Enlace III caido', (), ('III',)),
    ('Enlace IV caido', (), ('IV',)),
    ('Enlace V caido', (), ('V',)),
]
if __name__ == '__main__':
    allok = True
    for name, dd, dl in SCENARIOS:
        r = run(dd, dl)
        allok &= r
        print(f"{'OK   ' if r else 'FALLA'} {name}")
    print('TODO OK' if allok else 'HAY FALLAS')
