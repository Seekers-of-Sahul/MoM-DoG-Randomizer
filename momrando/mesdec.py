"""Decompiler for Master of Monsters (PS1) AI5-style .MES scripts.
Derived from the interpreter in ASC_*.EXE (0x80018238)."""
import sys

OPS = {0x20: '+', 0x21: '-', 0x22: '*', 0x23: '/', 0x24: '%', 0x25: '|', 0x26: '&',
       0x27: '==', 0x28: '!=', 0x29: '>', 0x2a: '<', 0x2b: '[w]', 0x2c: '[b]',
       0x2d: 'F@', 0x2e: 'F[]', 0x2f: 'rnd'}
SYS = {0: 'BATTLE'}


class Dec:
    def __init__(self, data):
        self.d = data
        self.hdr = data[0] | data[1] << 8
        self.p = self.hdr
        self.out = []
        self.blocks = []

    def b(self):
        v = self.d[self.p]; self.p += 1; return v

    def const(self):
        """index operand parser (0x8001a7f0)"""
        c = self.b()
        if 0x30 <= c < 0x40: return c - 0x30
        if c == 7: return self.b() >> 2
        if c == 8:
            b1, b2 = self.b(), self.b(); return (((b1 >> 2) << 8) + b2) >> 2
        if c == 9:
            b1, b2, b3 = self.b(), self.b(), self.b()
            a0 = (((b1 >> 2) << 8) + b2) >> 2
            return ((a0 >> 2) << 8) + ((b3 >> 2) + ((a0 & 3) << 6))
        return f'?c{c:02x}'

    def expr(self):
        st = []
        while True:
            c = self.d[self.p]
            if c == 3: self.p += 1; break
            if c in (0x30,) or 0x30 <= c < 0x40 or c in (7, 8, 9):
                st.append(str(self.const())); continue
            self.p += 1
            if 0x40 <= c < 0x5b: st.append(chr(c)); continue
            if c == 0x2d: st.append(f'F[{self.const()}]'); continue
            if c == 0x2f:
                st.append(f'rnd({self.const()})'); continue
            if c == 0x2e:
                a = st.pop() if st else '?'; st.append(f'F[{a}]'); continue
            if c in OPS:
                y = st.pop() if st else '?'; x = st.pop() if st else '?'
                if c == 0x2b: st.append(f'W({x})[{y}]')
                elif c == 0x2c: st.append(f'B({x})[{y}]')
                else: st.append(f'({x} {OPS[c]} {y})')
                continue
            st.append(f'?e{c:02x}')
        return st[-1] if st else '<empty>'

    def args(self):
        res = []
        while True:
            c = self.d[self.p]
            if c == 6:
                self.p += 1; s = self.p
                while self.d[self.p] != 6: self.p += 1
                res.append(repr(self.d[s:self.p].decode('latin1'))); self.p += 1
            elif c == 1:
                res.append('{block@%x}' % self.p); self.blocks.append(self.p); self.skipblock()
            elif (7 <= c <= 9) or (0x20 <= c < 0x5b):
                res.append(self.expr())
            else:
                break
            if self.d[self.p] == 2: self.p += 1
            else: break
            if len(res) >= 20: break
        return res

    def skipblock(self):
        while self.d[self.p] != 1: self.p += 1
        self.p += 1; depth = 1
        while depth:
            c = self.b()
            if c == 1: depth += 1
            elif c == 0: depth -= 1

    def emit(self, ind, s):
        self.out.append(f'{self.p_start:05x} ' + '  ' * ind + s)

    def text(self):
        s = []
        while self.p < len(self.d):
            c = self.d[self.p]
            if c >= 0x80:
                i = self.hdr and 2 + (c - 0x80) * 2
                s.append(self.d[i:i + 2].decode('cp932', 'replace')); self.p += 1
            elif 0x61 <= c < 0x80:
                s.append(bytes([c + 0x20, self.d[self.p + 1]]).decode('cp932', 'replace')); self.p += 2
            else: break
        return ''.join(s)

    def block(self, ind):
        # statements until 0 (end) ; returns at 0
        while self.p < len(self.d):
            self.p_start = self.p
            c = self.d[self.p]
            if c == 0: self.p += 1; return
            if c == 1: self.p += 1; continue
            if c == 2: self.p += 1; return
            if c >= 0x61:
                self.emit(ind, 'TEXT ' + self.text()); continue
            self.p += 1
            if c == 4:
                sub = self.b()
                if sub == 0x10:
                    cond = self.expr(); self.emit(ind, f'WHILE {cond}:'); self.sub_block(ind + 1)
                elif sub == 0x11: self.emit(ind, 'CONTINUE')
                elif sub == 0x12: self.emit(ind, 'BREAK')
                else:
                    self.blocks = []
                    a = self.args(); blks = self.blocks; self.emit(ind, f'CMD{sub:02x}(' + ', '.join(a) + ')')
                    save = self.p
                    for bp in blks:
                        self.p = bp; self.sub_block(ind + 1)
                    self.p = save
            elif c == 6:
                s = self.p
                while self.d[self.p] != 6: self.p += 1
                self.emit(ind, 'STR ' + repr(self.d[s:self.p])); self.p += 1
            elif c == 0x0a:
                i = self.const(); vals = [self.expr()]
                while self.d[self.p] == 2: self.p += 1; vals.append(self.expr())
                self.emit(ind, f'F[{i}..] = ' + ', '.join(vals))
            elif c == 0x0b:
                i = self.expr(); vals = [self.expr()]
                while self.d[self.p] == 2: self.p += 1; vals.append(self.expr())
                self.emit(ind, f'F[{i}..] = ' + ', '.join(vals))
            elif c == 0x0c:
                v = chr(self.b()); self.emit(ind, f'{v} = {self.expr()}')
            elif c == 0x0d:
                v = chr(self.b()); i = self.expr(); vals = [self.expr()]
                while self.d[self.p] == 2: self.p += 1; vals.append(self.expr())
                self.emit(ind, f'W({v})[{i}..] = ' + ', '.join(vals))
            elif c == 0x0e:
                v = chr(self.b()); i = self.expr(); vals = [self.expr()]
                while self.d[self.p] == 2: self.p += 1; vals.append(self.expr())
                self.emit(ind, f'B({v})[{i}..] = ' + ', '.join(vals))
            elif c == 0x0f:
                first = True
                while True:
                    cond = self.expr()
                    self.emit(ind, ('IF ' if first else 'ELIF ') + cond + ':')
                    self.sub_block(ind + 1); first = False
                    if self.d[self.p] == 2 and self.d[self.p + 1] == 0x0f:
                        self.p += 2; self.p_start = self.p; continue
                    if self.d[self.p] == 2:
                        self.p += 1; self.p_start = self.p
                        self.emit(ind, 'ELSE:'); self.sub_block(ind + 1)
                    break
            elif 0x10 <= c <= 0x19:
                self.blocks = []
                a = self.args(); blks = self.blocks
                name = {0x19: 'SYS', 0x12: 'DEFPROC', 0x13: 'CALLPROC'}.get(c, f'OP{c:02x}')
                self.emit(ind, f'{name}(' + ', '.join(a) + ')')
                save = self.p
                for bp in blks:
                    self.p = bp; self.sub_block(ind + 1)
                self.p = save
            else:
                self.emit(ind, f'?? {c:02x}')

    def sub_block(self, ind):
        while self.d[self.p] != 1: self.p += 1
        self.p += 1
        self.block(ind)


if __name__ == '__main__':
    data = open(sys.argv[1], 'rb').read()
    dd = Dec(data)
    try:
        while dd.p < len(data): dd.block(0)
    except IndexError:
        dd.out.append('<eof>')
    print('\n'.join(dd.out))
