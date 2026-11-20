"""Read the game's files from a disc image, apply patches + randomization, write them back."""
from . import patches
from .disc import Disc, VERSION_FILES

TEXT_FILES = ['MAHOU.TXT', 'TUTORI.TXT', 'UNTIKU.TBL', 'ITEM.TXT']

def generate(disc_bytes, opts=None, seed=None, log=None):
    """Returns (patched image bytes, Disc, spoiler dict)."""
    from . import rando
    d = Disc(disc_bytes)
    files = VERSION_FILES[d.version]
    exe = d.read_file(files['exes'][0])
    for other in files['exes'][1:]:
        assert d.read_file(other) == exe, other + ' differs from the main executable'
    monst = d.read_bind('MONST.TBL')
    text = {n: d.read_bind(n) for n in TEXT_FILES + [{'PAL': 'URESET.MES', 'US': 'RESET.MES'}[d.version]]}
    opts, spoiler = rando.resolve(d.version, exe, monst, opts or {}, seed)
    new_exe, new_monst, new_text = patches.build(d.version, exe, monst, text, opts, face_in=d.read_bind('FACE.B8'))
    for f in files['exes']:
        d.write_file(f, new_exe)
    d.write_bind('MONST.TBL', new_monst)
    grown = {}
    for n, b in new_text.items():
        if len(b) == d.bind[n][1]: d.write_bind(n, b)
        else: grown[n] = b
    if opts.get('fast_load'):
        # The LOADING image (shown before every stage, save screen, title) sits at the very end of BIND.DAT,
        # a long seek away from the map files; MT.B16 (same size, never loaded) sits at the start, near them.
        d.swap_bind('SAVEW.B16', 'MT.B16')
    for n, b in grown.items():      # after the swap: place_bind may use MT.B16's space
        d.place_bind(n, b)
    if opts.get('text_fixes'):
        # story scripts: every TEXT run can change length (nothing in a .MES holds an offset)
        from . import mes, textfix
        TX = textfix.load()
        for us_name, runs in TX['story'].items():
            name = us_name if d.version == 'US' else 'U' + us_name
            b = d.read_bind(name)
            sp = mes.spans(b)
            new = {s: t.replace('\uff0d', 'ー') for s, _, t in sp if '\uff0d' in t}   # no － glyph
            new.update({sp[int(k)][0]: mes.to_fullwidth(v) for k, v in runs.items()})
            d.place_bind(name, mes.rebuild(b, new))
    return bytes(d.data), d, spoiler
