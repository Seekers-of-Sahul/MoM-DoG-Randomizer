"""Story script (.MES) text re-encoder.

Format (interpreter 0x80018238): u16 header = code start; bytes 2..header = dictionary of SJIS characters
(2 bytes each, up to 128). Code is structured (blocks are 01 ... 00, skipped by scanning), so nothing in
the file holds an offset: a TEXT run can change length freely. A TEXT run is a sequence of characters,
each either one byte 0x80+i (dictionary entry i) or two bytes (SJIS lead - 0x20, trail) with the lead in
0x81..0x9f. '％' is a line break; every line of a page ends with one.
"""
import re
from collections import Counter

# '-': the font has no glyph for －; ー (long vowel mark) draws a mid-height dash
FW = {' ': '　', "'": '’', '"': '”', '.': '．', ',': '，', '-': 'ー', '!': '！', '?': '？', ':': '：',
      ';': '；', '(': '（', ')': '）', '/': '／', '&': '＆', '+': '＋', '=': '＝', '%': '％', '*': '＊',
      '#': '＃', '<': '＜', '>': '＞', '[': '［', ']': '］', '~': '～', '…': '．．．', '’': '’', '‘': '’',
      '“': '”', '”': '”', '—': 'ー', '–': 'ー'}


def to_fullwidth(s):
    """Sheet text (ASCII, \\n line breaks) -> game text (full-width, ％ after every line)."""
    out = []
    for ch in s:
        if ch == '\n': out.append('％')
        elif '0' <= ch <= '9' or 'A' <= ch <= 'Z' or 'a' <= ch <= 'z': out.append(chr(ord(ch) + 0xfee0))
        elif ch in FW: out.append(FW[ch])
        else: raise ValueError('no full-width form for %r in %r' % (ch, s))
    return ''.join(out) + '％'


def spans(data):
    """[(start, end, text)] of every TEXT run, found by walking the script like the interpreter."""
    from . import mesdec
    found = []

    class D(mesdec.Dec):
        def text(self):
            s = self.p; t = super().text(); found.append((s, self.p, t)); return t
    d = D(data)
    while d.p < len(data): d.block(0)
    assert not [l for l in d.out if '??' in l or '?e' in l or '?c' in l]
    return found


def rebuild(data, new_texts):
    """new_texts: {span start offset: unicode text (full-width, with ％)}. Returns the new file bytes."""
    sp = spans(data)
    starts = {s for s, _, _ in sp}
    assert set(new_texts) <= starts, sorted(set(new_texts) - starts)
    texts = [(s, e, new_texts.get(s, t)) for s, e, t in sp]
    for _, _, t in texts:
        for ch in t:
            b = ch.encode('cp932')
            assert len(b) == 2, (ch, t)
    freq = Counter(ch for _, _, t in texts for ch in t)
    # dictionary: the 128 most used characters (one byte each instead of two); kanji outside 0x81-0x9f
    # leads can only be written through the dictionary, so they always get a slot
    must = [c for c in freq if not 0x81 <= c.encode('cp932')[0] <= 0x9f]
    rest = [c for c, n in freq.most_common() if c not in must and n > 2]   # a slot costs 2 bytes
    dic = (must + rest)[:128]
    assert len(must) <= 128, len(must)
    idx = {c: i for i, c in enumerate(dic)}
    hdr = 2 + 2 * len(dic)
    old_hdr = data[0] | data[1] << 8
    out = bytearray(hdr.to_bytes(2, 'little') + b''.join(c.encode('cp932') for c in dic))
    p = old_hdr
    for s, e, t in texts:
        out += data[p:s]
        for ch in t:
            if ch in idx: out.append(0x80 + idx[ch])
            else:
                b = ch.encode('cp932'); out += bytes([b[0] - 0x20, b[1]])
        p = e
    out += data[p:]
    # check: same structure, same texts
    chk = spans(bytes(out))
    assert [t for _, _, t in chk] == [t for _, _, t in texts]
    return bytes(out)


def sheet_offset(id_):
    """Sheet ID column ('023ae' or "'02417") -> span start."""
    return int(id_.lstrip("'"), 16)
