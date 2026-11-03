"""Genera scripts CLI, running-configs estilo PT y el .pkt resuelto.

python3 ptcodec.py decode original.pkt original.xml
python3 build.py original.xml salida/
python3 simulate.py
"""
import copy
import os
import re
import sys

from lxml import etree

import ptcodec
from model import (DEVICES, DOMAIN, ENABLE_SECRET, ENABLE_SECRET_HASH, LINE_PASSWORD,
                   LINE_PASSWORD_T7, SSH_PASS, SSH_USER, USER_SECRET_HASH, VLANS, TI_POOL,
                   PCS_DHCP, expand, short)


# ------------------------------------------------------------------ CLI script
def range_cli(specs):
    parts = []
    for s in specs:
        head, _, last = s.rpartition('/')
        if '-' in last:
            a, b = last.split('-')
            parts.append(f'{head}/{a} - {b}')
        else:
            parts.append(s)
    return ', '.join(parts)


def cli_script(d):
    o = []
    sec = iter(range(1, 10))
    title = f"{d['xml']}  ->  hostname {d['hostname']}"
    o += ['!' + '=' * 70, f'! {title}', '!' + '=' * 70,
          'enable', 'configure terminal',
          f'!--- {next(sec)}. Configuracion basica y seguridad',
          f"hostname {d['hostname']}",
          'no ip domain-lookup',
          f'ip domain-name {DOMAIN}',
          f'enable secret {ENABLE_SECRET}',
          'service password-encryption',
          f"banner motd #{d['banner']}#",
          f'username {SSH_USER} secret {SSH_PASS}',
          'line console 0', f' password {LINE_PASSWORD}', ' login', ' exit',
          'line vty 0 15', f' password {LINE_PASSWORD}', ' login local', ' transport input ssh', ' exit',
          'crypto key generate rsa general-keys modulus 1024',
          'ip ssh version 2']
    if d.get('vlans'):
        o.append(f'!--- {next(sec)}. VLANs')
        for vid, name in d['vlans']:
            o += [f'vlan {vid}', f' name {name}', ' exit']
    o.append(f'!--- {next(sec)}. Interfaces')
    if d['kind'] == 'mls':
        o.append('ip routing')
    for specs, cmds in d['blocks']:
        multi = len(specs) > 1 or '-' in specs[0].rpartition('/')[2]
        o.append(('interface range ' if multi else 'interface ') + range_cli(specs))
        o += [' ' + c for c in cmds] + [' exit']
    for num, cmds in d.get('portchannels', []):
        o.append(f'interface port-channel {num}')
        o += [' ' + c for c in cmds] + [' exit']
    for vid, ipaddr, mask, extra in d.get('svis', []):
        o += [f'interface vlan {vid}', f' ip address {ipaddr} {mask}'] + [' ' + c for c in extra] + [' no shutdown', ' exit']
    if d.get('gateway'):
        o.append(f"ip default-gateway {d['gateway']}")
    if d.get('routes'):
        o.append(f'!--- {next(sec)}. Enrutamiento estatico (principal + flotante AD 10)')
        for net, mask, nh, ad in d['routes']:
            o.append(f'ip route {net} {mask} {nh}' + (f' {ad}' if ad else ''))
    if d['kind'] == 'router':
        o += ['!--- El registro estaba en 0x2142 (ignora la NVRAM al reiniciar). Se restablece:',
              'config-register 0x2102']
    o += ['end', 'write memory', '']
    return '\n'.join(o)


# ------------------------------------------------------------------ show-run
ORDER = ['description', 'no switchport', 'switchport trunk encapsulation', 'switchport access vlan',
         'switchport trunk allowed vlan', 'switchport mode', 'channel-group', 'no ip address', 'ip address',
         'ip helper-address', '__defaults__', 'standby version', 'standby 1 ip', 'standby 1 priority',
         'standby 1 preempt', 'shutdown', 'spanning-tree portfast']


def _rank(cmd):
    for i, p in enumerate(ORDER):
        if cmd.startswith(p):
            return i
    return len(ORDER)


def parse_run(lines):
    head, ifaces, tail = [], [], []
    i = 0
    while i < len(lines) and not lines[i].startswith('interface '):
        head.append(lines[i]); i += 1
    while i < len(lines) and lines[i].startswith('interface '):
        name = lines[i].split(' ', 1)[1]
        sub = []
        i += 1
        while i < len(lines) and lines[i].startswith(' '):
            sub.append(lines[i].strip()); i += 1
        while i < len(lines) and lines[i] == '!':
            i += 1
        ifaces.append([name, sub])
    tail = lines[i:]
    return head, ifaces, tail


def iface_cmds(d):
    per = {}
    for specs, cmds in d['blocks']:
        for s in specs:
            for n in expand(s):
                per.setdefault(n, []).extend(cmds)
    return per


def running_config(d, base):
    head, ifaces, tail = parse_run(base)
    # ---- head
    nh = []
    for l in head:
        if l == 'no service password-encryption':
            l = 'service password-encryption'
        if l.startswith('hostname '):
            nh += [f"hostname {d['hostname']}", '!', f'enable secret 5 {ENABLE_SECRET_HASH}', '!',
                   f'username {SSH_USER} secret 5 {USER_SECRET_HASH}', '!',
                   'no ip domain-lookup', f'ip domain-name {DOMAIN}']
            continue
        nh.append(l)
    # ---- interfaces
    per = iface_cmds(d)
    out_if = []
    for num, cmds in d.get('portchannels', []):
        out_if.append([f'Port-channel{num}', sorted(cmds, key=_rank)])
    for name, sub in ifaces:
        cmds = [c for c in per.get(name, []) if c != 'no shutdown']
        defaults = [s for s in sub if s in ('duplex auto', 'speed auto')]
        rest = [s for s in sub if s not in ('duplex auto', 'speed auto')]
        if any(c.startswith('ip address') for c in cmds):
            rest = [s for s in rest if s not in ('no ip address', 'shutdown')]
        if name in per and 'shutdown' not in cmds:
            rest = [s for s in rest if s != 'shutdown']
        allc = rest + cmds
        allc = sorted(set(allc), key=lambda c: (_rank(c), allc.index(c)))
        k = _rank('__defaults__')
        allc = [c for c in allc if _rank(c) < k] + defaults + [c for c in allc if _rank(c) >= k]
        if name == 'Vlan1':
            svi = [s for s in d.get('svis', []) if s[0] == 1]
            if svi:
                _, a, m, extra = svi[0]
                allc = [f'ip address {a} {m}'] + extra
        out_if.append([name, allc])
    for vid, a, m, extra in d.get('svis', []):
        if vid != 1:
            out_if.append([f'Vlan{vid}', [f'ip address {a} {m}'] + extra])
    body = []
    for name, sub in out_if:
        body.append(f'interface {name}')
        body += [' ' + s for s in sub]
        body.append('!')
    # ---- tail
    nt = []
    has_aux = any(l == 'line aux 0' for l in tail)
    i = 0
    while i < len(tail):
        l = tail[i]
        if l == 'ip classless' and d.get('routes'):
            nt.append(l)
            for net, mask, nhop, ad in d['routes']:
                nt.append(f'ip route {net} {mask} {nhop}' + (f' {ad}' if ad else ''))
            i += 1
            continue
        if l.startswith('line con 0'):
            if d.get('gateway'):
                nt += [f"ip default-gateway {d['gateway']}", '!']
            nt += ['ip ssh version 2', '!', f"banner motd '{d['banner']}'", '!', '!']
            nt += ['line con 0', f' password 7 {LINE_PASSWORD_T7}', ' login', '!']
            if has_aux:
                nt += ['line aux 0', '!']
            for r in ('0 4', '5 15'):
                nt += [f'line vty {r}', f' password 7 {LINE_PASSWORD_T7}', ' login local', ' transport input ssh']
            nt += ['!', '!', '!', 'end']
            break
        nt.append(l)
        i += 1
    return nh + body + nt


# ------------------------------------------------------------------ XML edits
def set_lines(engine, tag, lines):
    el = engine.find(tag)
    tail = el.tail
    for c in list(el):
        el.remove(c)
    el.text = '\n' + ' ' * 6
    for idx, l in enumerate(lines):
        le = etree.SubElement(el, 'LINE')
        le.text = l
        le.tail = '\n' + ' ' * (6 if idx < len(lines) - 1 else 5)
    el.tail = tail


def set_text(engine, path, value):
    el = engine.find(path)
    el.text = value


def port_names(d, engine):
    ports = list(engine.find('MODULE').iter('PORT'))
    if d['kind'] == 'router':
        names, copper = [], 0
        for p in ports:
            if p.findtext('TYPE') == 'eFiberGigabitEthernet':
                names.append('GigabitEthernet0/0/0')
            else:
                names.append(f'GigabitEthernet0/{copper}'); copper += 1
        return list(zip(names, ports))
    names = [f'FastEthernet0/{i}' for i in range(1, 25)] + ['GigabitEthernet0/1', 'GigabitEthernet0/2']
    assert len(ports) == 26, len(ports)
    return list(zip(names, ports))


def apply_ports(d, engine):
    per = iface_cmds(d)
    for name, p in port_names(d, engine):
        cmds = per.get(name, [])
        if 'shutdown' in cmds:
            p.find('POWER').text = 'false'
        elif cmds:
            p.find('POWER').text = 'true'
        for c in cmds:
            if c.startswith('ip address') and p.find('IP') is not None:
                _, _, a, m = c.split()
                p.find('IP').text = a
                p.find('SUBNET').text = m


def apply_vlans(d, engine):
    if not d.get('vlans'):
        return
    vl = engine.find('VLANS')
    existing = {int(v.get('number')): v for v in vl.findall('VLAN')}
    for vid, name in d['vlans']:
        if vid in existing:
            existing[vid].set('name', name)
        else:
            ref = existing[1]
            new = copy.deepcopy(ref)
            new.set('name', name); new.set('number', str(vid))
            # insertar en orden numerico
            after = max(n for n in existing if n < vid)
            existing[after].addnext(new)
            existing[vid] = new


def add_ti_pool(server_engine):
    pools = server_engine.find('DHCP_SERVERS/ASSOCIATED_PORTS/ASSOCIATED_PORT/DHCP_SERVER/POOLS')
    for p in pools.findall('POOL'):
        if p.findtext('NAME') == TI_POOL['name']:
            return
    tmpl = [p for p in pools.findall('POOL') if p.findtext('NAME') == 'VLAN 10'][0]
    new = copy.deepcopy(tmpl)
    new.find('NAME').text = TI_POOL['name']
    new.find('NETWORK').text = TI_POOL['network']
    new.find('MASK').text = TI_POOL['mask']
    new.find('DEFAULT_ROUTER').text = TI_POOL['gw']
    new.find('START_IP').text = TI_POOL['start']
    s = TI_POOL['start'].split('.')
    new.find('END_IP').text = '.'.join(s[:3] + [str(int(s[3]) + TI_POOL['max_users'] - 1)])
    new.find('DNS_SERVER').text = TI_POOL['dns']
    new.find('MAX_USERS').text = str(TI_POOL['max_users'])
    pools[-1].addnext(new)


PDU_TESTS = [  # (origen, destino, ip destino)
    ('PC3', 'WEB', '10.10.10.5'),
    ('PC6', 'DNS', '10.10.10.4'),
    ('PC9', 'DHCP', '10.10.10.3'),
    ('PC0', 'WEB', '10.10.10.5'),
    ('PC4', 'Router1', '172.16.99.1'),
]


def add_pdus(root, ids):
    sc = root.find('SCENARIOSET/SCENARIO')
    tmpl = sc.findall('PDU')[0]
    colors = [-16776961, -65536, -16744448, -8388480, -23296]
    for (src, dst, addr), col in zip(PDU_TESTS, colors):
        new = copy.deepcopy(tmpl)
        new.find('SOURCE').text = ids[src]
        new.find('DESTINATION').set('device', ids[dst])
        new.find('COLOR').text = str(col)
        new.find('PDU/DSTADDR').text = addr
        sc.findall('PDU')[-1].addnext(new)


def main(src_xml, outdir):
    os.makedirs(os.path.join(outdir, 'configuraciones'), exist_ok=True)
    tree = etree.parse(src_xml)
    root = tree.getroot()
    engines = {d.find('ENGINE').findtext('NAME'): d.find('ENGINE') for d in root.find('NETWORK/DEVICES').findall('DEVICE')}
    ids = {n: e.findtext('SAVE_REF_ID') for n, e in engines.items()}

    all_cli = []
    for idx, d in enumerate(DEVICES, 1):
        e = engines[d['xml']]
        base = [l.text or '' for l in e.find('RUNNINGCONFIG').findall('LINE')]
        run = running_config(d, base)
        set_lines(e, 'RUNNINGCONFIG', run)
        set_lines(e, 'STARTUPCONFIG', run)
        set_text(e, 'SYS_NAME', d['hostname'])
        if d['kind'] == 'router':
            set_text(e, 'CONFIG_REGISTER', '8450')        # 0x2102
            set_text(e, 'NEXT_CONFIG_REGISTER', '8450')
        apply_ports(d, e)
        apply_vlans(d, e)
        cli = cli_script(d)
        all_cli.append(cli)
        fn = f"{idx:02d}_{d['xml'].replace(' ', '')}_{d['hostname']}"
        open(os.path.join(outdir, 'configuraciones', fn + '.txt'), 'w').write(cli)
        os.makedirs(os.path.join(outdir, 'configuraciones', 'show-run'), exist_ok=True)
        open(os.path.join(outdir, 'configuraciones', 'show-run', fn + '.cfg'), 'w').write('\n'.join(run) + '\n')

    add_ti_pool(engines['DHCP'])
    for pc in PCS_DHCP:
        port = next(engines[pc].find('MODULE').iter('PORT'))
        port.find('PORT_DHCP_ENABLE').text = 'true'
    add_pdus(root, ids)

    xml_out = etree.tostring(root, encoding='utf-8')
    # Conservar la cabecera tal cual (el original no trae declaracion XML)
    open(os.path.join(outdir, 'resuelto.xml'), 'wb').write(xml_out)
    pkt = ptcodec.encode(xml_out)
    open(os.path.join(outdir, 'Caso_de_Estudio-Fundamentos_V2_RESUELTO.pkt'), 'wb').write(pkt)
    open(os.path.join(outdir, 'configuraciones', '00_TODOS_LOS_EQUIPOS.txt'), 'w').write('\n\n'.join(all_cli))
    print('ok', len(xml_out), len(pkt))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
