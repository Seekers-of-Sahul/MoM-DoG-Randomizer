"""English text fixes from the proofreading Sheet (data/text_fixes.json).

Every file keeps its size: the rewritten text is shorter, and the rest is filled with 0x1A (the files'
own end-of-text byte) after the last entry. Sheet text is plain ASCII with \\n line breaks; the game
files hold full-width Shift-JIS.
"""
import json, os, re
from .mes import FW

DATA = os.path.join(os.path.dirname(__file__), 'data', 'text_fixes.json')


def load():
    return json.load(open(DATA, encoding='utf-8'))


def fw(s):
    out = []
    for ch in s:
        if '0' <= ch <= '9' or 'A' <= ch <= 'Z' or 'a' <= ch <= 'z': out.append(chr(ord(ch) + 0xfee0))
        elif ch in FW: out.append(FW[ch])
        elif ch.isascii(): raise ValueError('no full-width form for %r in %r' % (ch, s))
        else: out.append(ch)                       # already full-width (▲ etc.)
    return ''.join(out)


def wrap(text, width=36):
    """Re-flow a paragraph whose lines are too long (greedy, at spaces)."""
    if max(len(l) for l in text.split('\n')) <= width: return text
    words, lines, cur = text.replace('\n', ' ').split(' '), [], ''
    for w in words:
        if cur and len(cur) + 1 + len(w) > width: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w) if cur else w
    lines.append(cur)
    return '\n'.join(lines)


def _fit(new, raw):
    nb = new.replace('\uff0d', 'ー').encode('cp932')      # old text too: the font has no － glyph
    if len(nb) > len(raw): return nb                 # grew: core.generate moves the file (Disc.place_bind)
    return nb + b'\x1a' * (len(raw) - len(nb))


def entries(raw, fixes, names=None, pad=None, block=None):
    """ITEM.TXT / MAHOU.TXT / UNTIKU.TBL: ☆№NNN【Name】 then body lines, then blank lines.
    fixes: {'NNN': sheet text}; names: {'NNN': new name}; pad: pad body lines to this width (UNTIKU: 36);
    block: every entry is this many lines after its header, blank lines included (ITEM/MAHOU: 4), else the
    body keeps the blank lines that followed the old one."""
    t = raw.decode('cp932').rstrip('\x1a')
    lines = t.split('\r\n')
    out, i, done = [], 0, set()
    hdr = re.compile(r'^☆№(\d+)【([^】]*)】(.*)$')
    while i < len(lines):
        m = hdr.match(lines[i])
        if not m: out.append(lines[i]); i += 1; continue
        no = m.group(1)
        name = m.group(2)
        if names and no in names:
            name = fw(names[no]); done.add('n' + no)
        out.append('☆№%s【%s】%s' % (no, name, m.group(3)))
        i += 1
        j = i
        while j < len(lines) and lines[j].strip('　') and not hdr.match(lines[j]): j += 1
        if no in fixes:
            body = [fw(l) for l in wrap(fixes[no]).split('\n')]
            if pad: body = [l + '　' * max(0, pad - len(l)) for l in body]
            if block:          # fixed-height entry: replace the blank lines after the body too
                k = j
                while k < len(lines) and not lines[k].strip('　') and not hdr.match(lines[k]): k += 1
                last = k == len(lines)
                assert len(body) < block and (k - i == block or last), (no, len(body), k - i)
                body += [''] * (block - len(body))
                if not last: j = k
            out += body; done.add(no)
        else:
            out += lines[i:j]
        i = j
    missing = [k for k in fixes if k not in done] + [k for k in (names or {}) if 'n' + k not in done]
    assert not missing, missing
    return _fit('\r\n'.join(out) + '\x1a', raw)


def tutorial(raw, fixes, pal=False):
    """TUTORI.TXT: entry header '06Ｇ', then pages of 4 lines (text + blank lines), up to a '--' line.
    Sheet text separates pages with one blank line."""
    if pal:      # PAL menu button is CALL (patches step 15 changes the old text the same way)
        fixes = {k: re.sub(r'\bPLACE\b', 'CALL', v) for k, v in fixes.items()}
    t = raw.decode('cp932').rstrip('\x1a')
    lines = t.split('\r\n')
    out, i, done = [], 0, set()
    while i < len(lines):
        m = re.match(r'^(\d\d)([Ａ-Ｚａ-ｚ])$', lines[i])
        if not m: out.append(lines[i]); i += 1; continue
        key = m.group(1) + chr(ord(m.group(2)) - 0xfee0)
        out.append(lines[i]); i += 1
        j = i
        while j < len(lines) and not lines[j].startswith('-'): j += 1
        if key in fixes:
            for page in fixes[key].split('\n\n'):
                pl = [fw(l) for l in page.split('\n')]
                assert len(pl) <= 4, (key, page)
                out += pl + [''] * (4 - len(pl))
            done.add(key)
        else:
            out += lines[i:j]
        i = j
    assert done == set(fixes), set(fixes) - done
    txt = '\r\n'.join(out) + '\x1a'
    if pal:      # PAL: the guide is DEFENDER in the old text; the fixes (and the rest of the game) say RAPHAEL
        txt = txt.replace(fw('DEFENDER'), fw('RAPHAEL'))
    return _fit(txt, raw)


def exe_names(exe, pairs):
    """Full-width names in the executable (fixed slots: name, U+3000 padding, then 00 00).
    pairs: [(old, new)]. Each old name must be found once as a whole slot."""
    exe = bytearray(exe)
    for old, new in pairs:
        o = fw(old).encode('cp932')
        hits = [m.start() for m in re.finditer(re.escape(o) + rb'(?:\x81\x40)*\x00\x00', bytes(exe))
                if exe[m.start() - 1] == 0 or exe[m.start() - 2:m.start()] == b'\x00\x00']
        assert len(hits) == 1, (old, hits)
        h = hits[0]
        end = exe.index(b'\x00\x00', h)
        while (end - h) % 2: end = exe.index(b'\x00\x00', end + 1)
        slot = end - h
        n = fw(new).encode('cp932')
        assert len(n) <= slot, (new, len(n), slot)
        exe[h:end] = n + '　'.encode('cp932') * ((slot - len(n)) // 2)
    return bytes(exe)


def monst_names(monst, names):
    """MONST.TBL: NNN,"name padded to 16",... ('_' is not used for spaces here)."""
    lines = monst.split(b'\r\n'); done = set()
    for i, ln in enumerate(lines):
        s = ln.decode('cp932')
        m = re.match(r'^(\d{3}),"(.{16})"', s)
        if m and m.group(1) in names:
            new = names[m.group(1)].replace(' ', '_'); assert len(new) <= 16, new
            s = s[:m.start(2)] + new.ljust(16) + s[m.end(2):]
            nb = s.encode('cp932'); assert len(nb) == len(ln)
            lines[i] = nb; done.add(m.group(1))
    assert done == set(names), set(names) - done
    return b'\r\n'.join(lines)


def exe_ascii_names(exe, pairs):
    """ASCII copies of names in the executable ('_' for spaces, space-padded slots ending in NULs; item
    names have a 16- and a 13-character table). Renames every whole-slot copy; returns (exe, count)."""
    exe = bytearray(exe); n = 0
    for old, new in pairs:
        o, w = old.replace(' ', '_').encode(), new.replace(' ', '_').encode()
        for m in list(re.finditer(rb'(?<=\x00)' + re.escape(o) + rb'( *)\x00', bytes(exe))):
            slot = len(o) + len(m.group(1))
            assert len(w) <= slot, (new, slot)
            exe[m.start():m.start() + slot] = w.ljust(slot); n += 1
    return bytes(exe), n
