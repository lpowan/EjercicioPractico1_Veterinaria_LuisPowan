"""Cisco Packet Tracer (7.x/8.x) .pkt/.pka codec: Twofish-EAX + obfuscation + qCompress.

Usage:
  python3 -I ptcodec.py decode in.pkt out.xml
  python3 -I ptcodec.py encode in.xml out.pkt
"""
import sys
import zlib
import struct

# ---------------------------------------------------------------- Twofish
Q0T = [[8, 1, 7, 13, 6, 15, 3, 2, 0, 11, 5, 9, 14, 12, 10, 4],
       [14, 12, 11, 8, 1, 2, 3, 5, 15, 4, 10, 6, 7, 0, 9, 13],
       [11, 10, 5, 14, 6, 13, 9, 0, 12, 8, 15, 3, 2, 4, 7, 1],
       [13, 7, 15, 4, 1, 2, 6, 14, 9, 11, 3, 0, 8, 5, 12, 10]]
Q1T = [[2, 8, 11, 13, 15, 7, 6, 14, 3, 1, 9, 4, 0, 10, 12, 5],
       [1, 14, 2, 11, 4, 12, 3, 7, 6, 13, 10, 5, 15, 9, 0, 8],
       [4, 12, 7, 5, 1, 6, 9, 10, 0, 14, 13, 8, 2, 11, 3, 15],
       [11, 9, 5, 1, 12, 3, 13, 14, 6, 4, 7, 15, 2, 0, 8, 10]]


def _ror4(x, n):
    return ((x >> n) | (x << (4 - n))) & 0xF


def _qperm(t, x):
    a0, b0 = x >> 4, x & 15
    a1 = a0 ^ b0
    b1 = a0 ^ _ror4(b0, 1) ^ ((8 * a0) & 15)
    a2, b2 = t[0][a1], t[1][b1]
    a3 = a2 ^ b2
    b3 = a2 ^ _ror4(b2, 1) ^ ((8 * a2) & 15)
    a4, b4 = t[2][a3], t[3][b3]
    return (b4 << 4) | a4


Q0 = [_qperm(Q0T, x) for x in range(256)]
Q1 = [_qperm(Q1T, x) for x in range(256)]


def _gfmul(a, b, poly):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a <<= 1
        if a & 0x100:
            a ^= poly
        b >>= 1
    return r


MDS = [[0x01, 0xEF, 0x5B, 0x5B],
       [0x5B, 0xEF, 0xEF, 0x01],
       [0xEF, 0x5B, 0x01, 0xEF],
       [0xEF, 0x01, 0xEF, 0x5B]]
RS = [[0x01, 0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E],
      [0xA4, 0x56, 0x82, 0xF3, 0x1E, 0xC6, 0x68, 0xE5],
      [0x02, 0xA1, 0xFC, 0xC1, 0x47, 0xAE, 0x3D, 0x19],
      [0xA4, 0x55, 0x87, 0x5A, 0x58, 0xDB, 0x9E, 0x03]]
M32 = 0xFFFFFFFF


def _rol(x, n):
    return ((x << n) | (x >> (32 - n))) & M32


def _ror(x, n):
    return ((x >> n) | (x << (32 - n))) & M32


def _bytes_of(w):
    return [(w >> (8 * i)) & 0xFF for i in range(4)]


def _mds_col(j, y):
    """Contribution of input byte y in position j to the MDS output word."""
    out = 0
    for i in range(4):
        out |= _gfmul(MDS[i][j], y, 0x169) << (8 * i)
    return out


def _h(x, L):
    k = len(L)
    y = _bytes_of(x)
    Lb = [_bytes_of(w) for w in L]
    if k == 4:
        y = [Q1[y[0]] ^ Lb[3][0], Q0[y[1]] ^ Lb[3][1], Q0[y[2]] ^ Lb[3][2], Q1[y[3]] ^ Lb[3][3]]
    if k >= 3:
        y = [Q1[y[0]] ^ Lb[2][0], Q1[y[1]] ^ Lb[2][1], Q0[y[2]] ^ Lb[2][2], Q0[y[3]] ^ Lb[2][3]]
    y = [Q1[Q0[Q0[y[0]] ^ Lb[1][0]] ^ Lb[0][0]],
         Q0[Q0[Q1[y[1]] ^ Lb[1][1]] ^ Lb[0][1]],
         Q1[Q1[Q0[y[2]] ^ Lb[1][2]] ^ Lb[0][2]],
         Q0[Q1[Q1[y[3]] ^ Lb[1][3]] ^ Lb[0][3]]]
    return _mds_col(0, y[0]) ^ _mds_col(1, y[1]) ^ _mds_col(2, y[2]) ^ _mds_col(3, y[3])


class Twofish:
    def __init__(self, key):
        assert len(key) in (16, 24, 32)
        k = len(key) // 8
        m = [struct.unpack('<I', key[4 * i:4 * i + 4])[0] for i in range(2 * k)]
        me, mo = m[0::2], m[1::2]
        s = []
        for i in range(k):
            chunk = key[8 * i:8 * i + 8]
            sb = [0, 0, 0, 0]
            for r in range(4):
                v = 0
                for c in range(8):
                    v ^= _gfmul(RS[r][c], chunk[c], 0x14D)
                sb[r] = v
            s.append(sb[0] | (sb[1] << 8) | (sb[2] << 16) | (sb[3] << 24))
        s = s[::-1]
        rho = 0x01010101
        K = []
        for i in range(20):
            a = _h((2 * i * rho) & M32, me)
            b = _rol(_h(((2 * i + 1) * rho) & M32, mo), 8)
            K.append((a + b) & M32)
            K.append(_rol((a + 2 * b) & M32, 9))
        self.K = K
        # Precompute key-dependent S-box tables for g().
        sb = [_bytes_of(w) for w in s]
        tabs = [[0] * 256 for _ in range(4)]
        for x in range(256):
            y = [x, x, x, x]
            if k == 4:
                y = [Q1[y[0]] ^ sb[3][0], Q0[y[1]] ^ sb[3][1], Q0[y[2]] ^ sb[3][2], Q1[y[3]] ^ sb[3][3]]
            if k >= 3:
                y = [Q1[y[0]] ^ sb[2][0], Q1[y[1]] ^ sb[2][1], Q0[y[2]] ^ sb[2][2], Q0[y[3]] ^ sb[2][3]]
            y = [Q1[Q0[Q0[y[0]] ^ sb[1][0]] ^ sb[0][0]],
                 Q0[Q0[Q1[y[1]] ^ sb[1][1]] ^ sb[0][1]],
                 Q1[Q1[Q0[y[2]] ^ sb[1][2]] ^ sb[0][2]],
                 Q0[Q1[Q1[y[3]] ^ sb[1][3]] ^ sb[0][3]]]
            for j in range(4):
                tabs[j][x] = _mds_col(j, y[j])
        self.T = tabs

    def _g(self, x):
        T = self.T
        return T[0][x & 0xFF] ^ T[1][(x >> 8) & 0xFF] ^ T[2][(x >> 16) & 0xFF] ^ T[3][x >> 24]

    def encrypt_block(self, blk):
        K = self.K
        r0, r1, r2, r3 = struct.unpack('<4I', blk)
        r0 ^= K[0]; r1 ^= K[1]; r2 ^= K[2]; r3 ^= K[3]
        g = self._g
        for rnd in range(16):
            t0 = g(r0)
            t1 = g(_rol(r1, 8))
            f0 = (t0 + t1 + K[2 * rnd + 8]) & M32
            f1 = (t0 + 2 * t1 + K[2 * rnd + 9]) & M32
            n2 = _ror(r2 ^ f0, 1)
            n3 = _rol(r3, 1) ^ f1
            r0, r1, r2, r3 = n2, n3, r0, r1
        return struct.pack('<4I', r2 ^ K[4], r3 ^ K[5], r0 ^ K[6], r1 ^ K[7])


# ---------------------------------------------------------------- EAX
def _xor(a, b):
    return bytes(x ^ y for x, y in zip(a, b))


def _dbl(b):
    n = int.from_bytes(b, 'big') << 1
    if n >> 128:
        n = (n ^ 0x87) & ((1 << 128) - 1)
    return n.to_bytes(16, 'big')


def _cmac(c, msg):
    L = c.encrypt_block(bytes(16))
    k1 = _dbl(L)
    k2 = _dbl(k1)
    if msg and len(msg) % 16 == 0:
        blocks = [msg[i:i + 16] for i in range(0, len(msg), 16)]
        blocks[-1] = _xor(blocks[-1], k1)
    else:
        blocks = [msg[i:i + 16] for i in range(0, len(msg) - len(msg) % 16, 16)]
        last = msg[len(msg) - len(msg) % 16:] + b'\x80'
        last = last + bytes(16 - len(last))
        blocks.append(_xor(last, k2))
    x = bytes(16)
    for b in blocks:
        x = c.encrypt_block(_xor(x, b))
    return x


def _omac(c, t, msg):
    return _cmac(c, bytes(15) + bytes([t]) + msg)


def _ctr(c, iv, data):
    ctr = int.from_bytes(iv, 'big')
    out = bytearray()
    for i in range(0, len(data), 16):
        ks = c.encrypt_block(ctr.to_bytes(16, 'big'))
        chunk = data[i:i + 16]
        out += _xor(chunk, ks[:len(chunk)])
        ctr = (ctr + 1) & ((1 << 128) - 1)
    return bytes(out)


def eax_decrypt(key, nonce, data, header=b''):
    c = Twofish(key)
    ct, tag = data[:-16], data[-16:]
    n = _omac(c, 0, nonce)
    h = _omac(c, 1, header)
    cm = _omac(c, 2, ct)
    exp = _xor(_xor(n, h), cm)
    if exp != tag:
        raise ValueError('EAX tag mismatch')
    return _ctr(c, n, ct)


def eax_encrypt(key, nonce, pt, header=b''):
    c = Twofish(key)
    n = _omac(c, 0, nonce)
    h = _omac(c, 1, header)
    ct = _ctr(c, n, pt)
    cm = _omac(c, 2, ct)
    return ct + _xor(_xor(n, h), cm)


# ---------------------------------------------------------------- PT format
KEY = bytes([137] * 16)
IV = bytes([16] * 16)


def decode(raw):
    L = len(raw)
    stage1 = bytes((raw[L - 1 - i] ^ ((L - i * L) & 0xFF)) for i in range(L))
    dec = eax_decrypt(KEY, IV, stage1)
    n = len(dec)
    stage3 = bytes((dec[i] ^ ((n - i) & 0xFF)) for i in range(n))
    size = struct.unpack('>I', stage3[:4])[0]
    xml = zlib.decompress(stage3[4:])
    assert len(xml) == size, (len(xml), size)
    return xml


def encode(xml):
    comp = struct.pack('>I', len(xml)) + zlib.compress(xml, 9)
    n = len(comp)
    stage3 = bytes((comp[i] ^ ((n - i) & 0xFF)) for i in range(n))
    enc = eax_encrypt(KEY, IV, stage3)
    L = len(enc)
    out = bytearray(L)
    for i in range(L):
        out[L - 1 - i] = enc[i] ^ ((L - i * L) & 0xFF)
    return bytes(out)


def _selftest():
    c = Twofish(bytes(16))
    assert c.encrypt_block(bytes(16)).hex().upper() == '9F589F5CF6122C32B6BFEC2F2AE8C35A'


if __name__ == '__main__':
    _selftest()
    mode, src, dst = sys.argv[1:4]
    data = open(src, 'rb').read()
    out = decode(data) if mode == 'decode' else encode(data)
    open(dst, 'wb').write(out)
    print(mode, 'ok', len(data), '->', len(out))
