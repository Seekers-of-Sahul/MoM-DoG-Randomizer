"""PlayStation Track 1 image access (MODE2/2352): ISO 9660 lookup, BIND archive, sector-correct writes."""
import struct, hashlib

# ---------- EDC / ECC (Mode 2 Form 1) ----------
_EDC = []
for i in range(256):
    e = i
    for _ in range(8): e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
    _EDC.append(e)
_F, _B = [0] * 256, [0] * 256
for i in range(256):
    j = ((i << 1) ^ (0x11D if i & 0x80 else 0)) & 0xff
    _F[i] = j; _B[i ^ j] = i

def _edc(buf):
    e = 0
    for x in buf: e = (e >> 8) ^ _EDC[(e ^ x) & 0xff]
    return e

def _ecc_block(src, majc, minc, majm, mininc):
    size = majc * minc
    out = bytearray(majc * 2)
    for major in range(majc):
        idx = (major >> 1) * majm + (major & 1)
        a = b = 0
        for _ in range(minc):
            t = src[idx]; idx += mininc
            if idx >= size: idx -= size
            a ^= t; b ^= t; a = _F[a]
        a = _B[_F[a] ^ b]
        out[major] = a; out[major + majc] = a ^ b
    return out

def fix_sector(s):
    s = bytearray(s)
    assert s[0x12] & 0x20 == 0, 'form 2 sector'
    struct.pack_into('<I', s, 0x818, _edc(s[0x10:0x818]))
    hdr = bytes(s[0xC:0x10]); s[0xC:0x10] = b'\0\0\0\0'
    s[0x81C:0x8C8] = _ecc_block(s[0xC:0x81C], 86, 24, 2, 86)
    s[0x8C8:0x930] = _ecc_block(s[0xC:0x8C8], 52, 43, 86, 88)
    s[0xC:0x10] = hdr
    return bytes(s)

# Known clean Track 1 dumps (Redump-style bin/cue)
KNOWN = {
    '9e453ec3d3c20302e271eca5f272bcb7': 'US',
    '6fa52600f97e551313acceb96ce27d99': 'PAL',
}
VERSION_FILES = {
    'US': dict(exes=['SLUS_005.95', 'AI5.EXE']),
    'PAL': dict(exes=['ASC_USA.EXE', 'AI5_USA.EXE']),
}

class Disc:
    def __init__(self, data):
        self.data = bytearray(data)
        self.orig = bytes(data)
        self.md5 = hashlib.md5(self.orig).hexdigest()
        pvd = self.sector(16)
        assert pvd[1:6] == b'CD001', 'not an ISO 9660 MODE2/2352 track'
        self.root = self._rec(pvd[156:190])
        self.version = 'US' if self.find('SLUS_005.95') else 'PAL' if self.find('ASC_USA.EXE') else None
        assert self.version, 'not Master of Monsters: Disciples of Gaia (US SLUS-00595 or PAL SLES-00244)'
        self.known_dump = KNOWN.get(self.md5) == self.version
        self.bind_lba = self.find('MM/BIND.DAT')[0]
        lba, size = self.find('MM/BIND.TBL')
        tb = self.read(lba, 0, size)
        self.bind = {}
        for i in range(0, len(tb) - 18, 19):
            x = tb[i:i + 19]
            name = x[:8].decode('latin1').strip() + '.' + x[8:11].decode('latin1').strip()
            self.bind[name] = (int.from_bytes(x[11:15], 'big'), int.from_bytes(x[15:19], 'big'))

    def sector(self, lba):
        o = lba * 2352 + 24
        return bytes(self.data[o:o + 2048])

    @staticmethod
    def _rec(r):
        return dict(lba=struct.unpack_from('<I', r, 2)[0], size=struct.unpack_from('<I', r, 10)[0],
                    dir=bool(r[25] & 2), name=r[33:33 + r[32]].decode('latin1').split(';')[0])

    def _list(self, rec):
        out, n = [], (rec['size'] + 2047) // 2048
        for k in range(n):
            s = self.sector(rec['lba'] + k); p = 0
            while p < 2048 and s[p]:
                out.append(self._rec(s[p:p + s[p]])); p += s[p]
        return out

    def find(self, path):
        """'MM/BIND.DAT' -> (lba, size) or None."""
        rec = self.root
        for part in path.upper().split('/'):
            hit = [r for r in self._list(rec) if r['name'].upper() == part]
            if not hit: return None
            rec = hit[0]
        return rec['lba'], rec['size']

    def read(self, lba, offset, size):
        out = bytearray(); o = offset
        while len(out) < size:
            s = self.sector(lba + o // 2048); w = o % 2048
            take = min(2048 - w, size - len(out)); out += s[w:w + take]; o += take
        return bytes(out)

    def write(self, lba, offset, data):
        pos = 0
        while pos < len(data):
            o = offset + pos; sec = lba + o // 2048; w = o % 2048
            n = min(2048 - w, len(data) - pos)
            a = sec * 2352
            s = bytearray(self.data[a:a + 2352]); s[24 + w:24 + w + n] = data[pos:pos + n]
            self.data[a:a + 2352] = fix_sector(s)
            pos += n

    def read_file(self, path):
        lba, size = self.find(path); return self.read(lba, 0, size)

    def write_file(self, path, data):
        lba, size = self.find(path); assert len(data) == size, (path, len(data), size)
        self.write(lba, 0, data)

    def read_bind(self, name):
        o, size = self.bind[name]; return self.read(self.bind_lba, o, size)

    def write_bind(self, name, data):
        o, size = self.bind[name]; assert len(data) == size, (name, len(data), size)
        self.write(self.bind_lba, o, data)

    def swap_bind(self, a, b):
        """Swap where two same-size BIND.DAT files live (data and BIND.TBL offsets)."""
        (oa, sa), (ob, sb) = self.bind[a], self.bind[b]
        assert sa == sb, (a, b)
        da, db = self.read_bind(a), self.read_bind(b)
        self.write(self.bind_lba, oa, db); self.write(self.bind_lba, ob, da)
        lba, size = self.find('MM/BIND.TBL'); tbl = bytearray(self.read(lba, 0, size))
        for i in range(0, len(tbl) - 18, 19):
            n = tbl[i:i + 8].decode('latin1').strip() + '.' + tbl[i + 8:i + 11].decode('latin1').strip()
            if n == a: tbl[i + 11:i + 15] = ob.to_bytes(4, 'big')
            elif n == b: tbl[i + 11:i + 15] = oa.to_bytes(4, 'big')
        self.write(lba, 0, bytes(tbl))
        self.bind[a], self.bind[b] = (ob, sa), (oa, sb)

    def resize_bind(self, name, data):
        """Write a BIND.DAT file of a different size: it must fit before the next file (files start on
        sector boundaries, so there is slack up to the next 2048). Updates the size in BIND.TBL; the
        bytes up to the old end are zeroed."""
        o, size = self.bind[name]
        nxt = min([x for x, _ in self.bind.values() if x > o] + [o + ((size + 2047) & ~2047)])
        assert o + len(data) <= nxt, (name, len(data), nxt - o)
        self.write(self.bind_lba, o, data + bytes(max(0, size - len(data))))
        lba, tsize = self.find('MM/BIND.TBL'); tbl = bytearray(self.read(lba, 0, tsize))
        hits = 0
        for i in range(0, len(tbl) - 18, 19):
            n = tbl[i:i + 8].decode('latin1').strip() + '.' + tbl[i + 8:i + 11].decode('latin1').strip()
            if n == name: tbl[i + 15:i + 19] = len(data).to_bytes(4, 'big'); hits += 1
        assert hits == 1, (name, hits)
        self.write(lba, 0, bytes(tbl))
        self.bind[name] = (o, len(data))

    def _set_tbl(self, name, off, size):
        lba, tsize = self.find('MM/BIND.TBL'); tbl = bytearray(self.read(lba, 0, tsize)); hits = 0
        for i in range(0, len(tbl) - 18, 19):
            n = tbl[i:i + 8].decode('latin1').strip() + '.' + tbl[i + 8:i + 11].decode('latin1').strip()
            if n == name:
                tbl[i + 11:i + 15] = off.to_bytes(4, 'big'); tbl[i + 15:i + 19] = size.to_bytes(4, 'big'); hits += 1
        assert hits == 1, (name, hits)
        self.write(lba, 0, bytes(tbl)); self.bind[name] = (off, size)

    def place_bind(self, name, data, spare='MT.B16'):
        """Write a BIND.DAT file of any size. Same size: in place. Larger: into the space of a file the game
        never loads (MT.B16, 150 KB), BIND.TBL pointed there; the old copy stays unused."""
        o, size = self.bind[name]
        if len(data) == size: return self.write_bind(name, data)
        if len(data) < size: return self.resize_bind(name, data)
        so, ss = self.bind[spare]
        used = getattr(self, '_spare_used', 0)
        assert used + len(data) <= ss, ('spare full', name)
        self.write(self.bind_lba, so + used, data)
        self._set_tbl(name, so + used, len(data))
        self._spare_used = (used + len(data) + 3) & ~3


def make_ppf(orig, mod, desc):
    """PPF 3.0 patch (no undo data, no block check) turning orig into mod."""
    assert len(orig) == len(mod)
    h = b'PPF30' + b'\x02' + desc.encode('ascii', 'replace')[:50].ljust(50, b' ') + bytes([0, 0, 0, 0])
    recs = bytearray(); n = len(orig)
    # walk only changed sectors for speed
    for sec in range(n // 2352):
        a = sec * 2352
        if orig[a:a + 2352] == mod[a:a + 2352]: continue
        i = a
        while i < a + 2352:
            if orig[i] != mod[i]:
                j = i
                while j < a + 2352 and j - i < 255 and orig[j] != mod[j]: j += 1
                recs += struct.pack('<QB', i, j - i) + mod[i:j]; i = j
            else: i += 1
    return h + bytes(recs)

def apply_ppf(img, ppf):
    img = bytearray(img); assert ppf[:5] == b'PPF30'
    blockcheck, undo = ppf[57], ppf[58]
    p = 60 + (1024 if blockcheck else 0)
    while p < len(ppf):
        off, ln = struct.unpack_from('<QB', ppf, p); p += 9
        img[off:off + ln] = ppf[p:p + ln]; p += ln + (ln if undo else 0)
    return bytes(img)
