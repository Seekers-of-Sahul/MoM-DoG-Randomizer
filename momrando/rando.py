"""Seeded randomization. Turns user options + seed into concrete patch options and a spoiler log."""
import random, re, struct
from .patches import TABLES, BASE

WATER = {'ｱｻｾ', 'ｶﾜ', 'ｼﾝｶｲ'}
AIR = {'ﾃｲｸｳ', 'ｿﾗ'}

def monsters(monst):
    """id -> dict(name, lv, align, cls) from MONST.TBL. cls: ground / air / water."""
    out = {}
    for line in monst.decode('cp932').split('\r\n'):
        f = line.split(',')
        if len(f) > 5 and f[0].isdigit() and f[1].startswith('"'):
            ty = f[4].strip()
            out[int(f[0])] = dict(name=f[1].strip('" '), lv=int(f[2]), align=f[3],
                                  cls='water' if ty in WATER else 'air' if ty in AIR else 'ground')
    return out

def stage_lists(version, exe, n_stages=29):
    """Vanilla player (+17) and enemy (+33) summon lists per stage: [(id, lv)] without empties."""
    st = TABLES[version]['ST']; off = lambda a: a - BASE + 0x800
    out = {}
    for s in range(n_stages):
        r = exe[off(st + 72 * s):off(st + 72 * s) + 72]
        lst = lambda o: [(r[o + 2 * i], r[o + 2 * i + 1]) for i in range(8) if r[o + 2 * i] != 255]
        out[s] = dict(player=lst(17), enemy=lst(33))
    return out

def shuffle_summons(rng, mons, lists):
    pool = sorted({m for L in lists.values() for side in L.values() for m, _ in side})
    new, spoil = {}, {}
    for s, L in lists.items():
        if not L['player']: continue
        chosen = []
        for mid, lv in L['player']:
            base = mons[mid]['lv']; cls = mons[mid]['cls']
            cand = []
            for win in (2, 4, 7, 12, 99):
                cand = [m for m in pool if mons[m]['cls'] == cls and abs(mons[m]['lv'] - base) <= win
                        and m not in [c for c, _ in chosen]]
                if cand: break
            pick = rng.choice(cand)
            newlv = max(1, min(99, mons[pick]['lv'] + max(0, lv - base)))
            chosen.append((pick, newlv))
        new[s] = chosen
        spoil['stage %02d' % s] = ['%s lv%d' % (mons[m]['name'], v) for m, v in chosen]
    return new, spoil

# Story battle order by stage counter F (extras F=30/32/34 play stages 26/27/28; 23-25 are the final choice).
STORY_F = list(range(0, 10)) + [30] + list(range(10, 14)) + [32] + list(range(14, 17)) + [34] + list(range(17, 23))
def battle_of(F): return {30: 26, 32: 27, 34: 28}.get(F, F)

def draft_plan(rng, mons, lists, size=6, step=3, start=None, start_n=3):
    """Draft rows per stage counter F (drafted after winning battle F), levels, roster limits, start monsters."""
    pool = sorted({m for L in lists.values() for side in L.values() for m, _ in side})
    def level_of(stage):
        lv = sorted(v for _, v in lists[stage]['player']) or [1]
        return lv[len(lv) // 2]
    def pick(n, target, land_only=False):
        for win in (6, 10, 15, 99):
            cand = [m for m in pool if target - win <= mons[m]['lv'] <= target
                    and not (land_only and mons[m]['cls'] == 'water')]
            if len(cand) >= n: break
        return rng.sample(cand, min(n, len(cand)))
    rows, levels, limits, spoil = {}, {}, {}, {}
    order = STORY_F + [23]
    for p, F in enumerate(STORY_F):
        nxt = battle_of(order[p + 1])
        target = level_of(nxt)
        rows[F] = pick(size, target)
        levels[F] = target
        limits[F] = step * (p + 2)
        spoil['after stage %d' % battle_of(F)] = dict(
            keep=min(29, limits[F]), level=target, offered=[mons[m]['name'] for m in rows[F]])
    l0 = level_of(0)
    if start:
        byname = {v['name'].lower(): k for k, v in mons.items()}
        st = [byname[x.strip().lower()] for x in start]
    else:
        st = pick(start_n, l0, land_only=True)      # stage 0 is a land map
    spoil['start'] = dict(level=l0, monsters=[mons[m]['name'] for m in st])
    return dict(rows=rows, levels=levels, limits=limits, start=st, start_level=l0), spoil

# Names the patch fixes (patches.py MONST edits) - used so the spoiler log matches the game
NAME_FIXES = {39: 'Imp', 119: 'Siren', 121: 'Peryton'}

# Base levels the rebalance changes in MONST.TBL (patches.py step 6): the Goblin line evolves Goblin 1 > Orc 8 > Overlord 25.
MOD_LEVELS = {128: 8, 129: 25}

HUB_IDS = [b for b in range(0, 29) if not 23 <= b <= 25]       # 0 tutorial, 1-22 story, 26-28 extras

def hub_plan(rng, mode, skip_tutorial):
    """'progressive': story order (extras after 9/13/16), 2 open, every first clear opens the next one.
    'open': everything unlocked. 'shuffled': random order loosely following the story; 2 open at the start,
    clearing the i-th stage of the order opens the (i+2)-th, stage 22 (-> ending) last. The tutorial is part of
    the order only when it is skipped at the start (otherwise it has been played already)."""
    story = [0] if skip_tutorial else []
    for b in range(1, 23):
        story.append(b)
        if b in (9, 13, 16): story.append({9: 26, 13: 27, 16: 28}[b])       # extras where the story puts them
    if mode == 'progressive':
        return dict(start=(1 << story[0]) | (1 << story[1]), unlocks={}, progressive=story[2:],
                    skip_tutorial=skip_tutorial), \
            {'mode': 'progressive', 'skip tutorial': skip_tutorial, 'order': story}
    if mode == 'open':
        return dict(start=sum(1 << b for b in HUB_IDS), unlocks={}, skip_tutorial=skip_tutorial), \
            {'mode': 'open', 'skip tutorial': skip_tutorial}
    # loosely follows the story so early stages stay early: sort by story position + random 0..8
    pos = {26: 9.5, 27: 13.5, 28: 16.5}
    pool = [b for b in HUB_IDS if b != 22 and (b or skip_tutorial)]
    order = sorted(pool, key=lambda b: pos.get(b, b) + rng.uniform(0, 8))
    order.append(22)
    unlocks = {order[i]: 1 << order[i + 2] for i in range(len(order) - 2)}
    return dict(start=(1 << order[0]) | (1 << order[1]), unlocks=unlocks, skip_tutorial=skip_tutorial), \
        {'mode': 'shuffled', 'skip tutorial': skip_tutorial, 'start': order[:2],
         'clear -> unlocks': {str(a): order[i + 2] for i, a in enumerate(order[:-2])}}

def resolve(version, exe, monst, user_opts, seed):
    """user_opts: summons ('vanilla'|'mod'|'shuffle'), combat_exp, commander_buffs, hardcore, lock_difficulty."""
    opts = dict(user_opts)
    spoiler = {'seed': seed, 'version': version}
    rng = random.Random('momrando:%s' % seed)
    mons = monsters(monst)
    for mid, lv in MOD_LEVELS.items(): mons[mid]['lv'] = lv
    for mid, nm in NAME_FIXES.items(): mons[mid]['name'] = nm
    if opts.get('text_fixes'):
        from . import textfix
        for mid, nm in textfix.load()['monsters'].items(): mons[int(mid)]['name'] = nm
    summons = opts.pop('summons', 'vanilla')
    hub = opts.pop('hub', None)
    if hub:
        opts['hub'], spoiler['hub'] = hub_plan(rng, hub['mode'], hub.get('skip_tutorial', False))
    draft = opts.pop('draft', None)
    if draft:
        lists = stage_lists(version, exe)
        opts['draft'], spoiler['draft'] = draft_plan(rng, mons, lists, draft.get('size', 6), draft.get('step', 3),
                                                     draft.get('start'))
        opts['summon_lists'] = {s: [] for s in lists}           # summoning disabled
        summons = None
    if summons is None:
        pass
    elif summons == 'shuffle':
        opts['summon_lists'], spoiler['summon lists'] = shuffle_summons(rng, mons, stage_lists(version, exe))
    else:
        opts['summon_lists'] = summons
    return opts, spoiler
