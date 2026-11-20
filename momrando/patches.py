"""All rebalance-mod patches, as a function of game version and options.
Ported from the hand-built mod (work/scripts/build_mod.py); same code, no file I/O."""
import struct, re

BASE = 0x80010000

PAL_V = dict(
    UREG='s7',
    RNG=0x8001b644, SEEDLO=-0x5388, LVUP=(0x8002c114, 0x80032a04, 0x80032ee8),
    T1=0x80016e80, T2=0x80016ef4, F1=0x80016f74, ST=0x8007c5cc,
    CEXP=0x8002b534, IDXA=0x6928, IDXB=-0x1140, MAGIC=0x8002af60,
    CAVE=0x80044540, CAVE_END=0x80044b40, ITEMLO=-0x3f80, INVLO=0x7d8, PARSE=0x800465e0,
    TPL_MOVE=0x5f9a, TPL_MP=0x5fb4, EQ_CHECK=0x80033664, EQ_H=0x80033674, EQ_CONT=0x800336f4,
    KILLB=0x8002bd80, KILLT=0x8002bd98, ANIM=0x80031b60, ANIM_T=0x800386cc,
    TOWER=0x80029f98, TOWER_MSG=0x80029ff0, MSGFN=0x8003ec18,
    SETSTATE=0x80038b14, ENDACT=0x80037334, HOOK_SITES=(0x8002b6c4, 0x8002bdd8, 0x8002c868),
    DIFF_LO=-0x3a60, DIFF_READS=((0x8002b024, 'v0'), (0x8002b058, 'v0'), (0x800599f4, 'v1')),
    SAVEFN=0x8003c45c, BATTLE_LO=-0x3a76, UNITMODE_LO=-0x3a72,
    CREATE=0x80045f24, FLAGS_LO=-0x1f18, DRAFT_SITE=0x800232c8, DRAFT_LO=-0x3a6a, START_SITE=0x80023034,
    LIMIT_SITE=0x8003793c, SUBREG='s1',
    MODE_LO=-0x3a6c, HUB_SYS19J=0x80023200, HUB_LOOP=0x80023348, SYSRET=0x80039964, HUB_LIST=0x8002416c,
    HUB_PREV=0x800241cc, HUB_END=0x80024310, HUB_LABEL=0x8005d5b0, HUB_CONF=0x80037654, HUB_CANC=0x80037668,
    CANC_CONT=0x80037670, CANC_IGN=0x8003934c, CAVE4=0x800630f4, CAVE4_END=0x80063478,
    HUB_LOADRES=0x80024760, SYS1_BODY=0x80022e30, HUB_HILITE=0x8005d658, SYS5_CMP=0x80022fa4, SYS5_END=0x80023090, RESET_MES='URESET.MES', CAVE5=0x80065f58, CAVE5_END=0x80066370, MBOX=0x800661a4,
    READER=0x8001b2a4, CDSYNC=0x8001b4bc, CDCTL=0x80066914, CDREAD=0x80069658, POS2INT=0x80066e78, INT2POS=0x80066d74,
    CAVE6=0x80064658, CAVE6_END=0x80064850, CAVE8=0x800787bc, CAVE8_END=0x80078970, MOVIEWAIT=(0x80021c3c, 0x80021c88), SAVEREAD=0x80020ae8,
    READALL=0x80040cd0, BOOTREAD=0x80022da8, CARDTEST=0x800207e4, CARDEXISTS=0x80020ccc, READSLOT=0x80020aa8,
    CAVE7=0x80064458, CAVE7_END=0x80064604, LOOPVSYNC=(0x800398c0, 0x8004a558, 0x8004b27c),
    BGM_COMBAT=0x8004b088, BGM_SELECT=0x8003b678, PLAYBGM=0x8001fe98)
US_V = dict(
    UREG='fp',
    RNG=0x8001b69c, SEEDLO=-0x5538, LVUP=(0x8002bd28, 0x800326c8, 0x80032bc0),
    T1=0x80016ef0, T2=0x80016f64, F1=0x80016fe4, ST=0x8007c41c,
    CEXP=0x8002b180, IDXA=0x6778, IDXB=-0x12f0, MAGIC=0x8002aba8,
    CAVE=0x80044388, CAVE_END=0x80044988, ITEMLO=-0x4130, INVLO=-0xd8, PARSE=0x80046428,
    TPL_MOVE=0x56ea, TPL_MP=0x5704, EQ_CHECK=0x80033324, EQ_H=0x80033334, EQ_CONT=0x80033398,
    KILLB=0x8002b99c, KILLT=0x8002b9b4, ANIM=0x80031864, ANIM_T=0x8003845c,
    TOWER=0x80029c30, TOWER_MSG=0x80029c80, MSGFN=0x8003ea60,
    SETSTATE=0x8003889c, ENDACT=0x800390f4, HOOK_SITES=(0x8002b310, 0x8002b9f4, 0x8002c498),
    DIFF_LO=-0x3c10, DIFF_READS=((0x8002ac6c, 'v0'), (0x8002aca0, 'v0'), (0x8005983c, 'v1')),
    SAVEFN=0x8003c2a4, BATTLE_LO=-0x3c26, UNITMODE_LO=-0x3c22,
    CREATE=0x80045d6c, FLAGS_LO=-0x20c8, DRAFT_SITE=0x80022f48, DRAFT_LO=-0x3c1a, START_SITE=0x80022cb4,
    LIMIT_SITE=0x80037670, SUBREG='s2',   # US keeps the SYS subcommand in s2 (PAL: s1)
    MODE_LO=-0x3c1c, HUB_SYS19J=0x80022e80, HUB_LOOP=0x80022fc8, SYSRET=0x800397a8, HUB_LIST=0x80023dec,
    HUB_PREV=0x80023e4c, HUB_END=0x80023f90, HUB_LABEL=0x8005d400, HUB_CONF=0x80037388, HUB_CANC=0x8003739c,
    CANC_CONT=0x800373a4, CANC_IGN=0x800390fc, CAVE4=0x80062f44, CAVE4_END=0x800632c8,
    HUB_LOADRES=0x800243e0, SYS1_BODY=0x80022ab0, HUB_HILITE=0x8005d4a8, SYS5_CMP=0x80022c24, SYS5_END=0x80022d10, RESET_MES='RESET.MES', CAVE5=0x80065da8, CAVE5_END=0x800661c0, MBOX=0x80065ff4,
    READER=0x8001b2fc, CDSYNC=0x8001b514, CDCTL=0x80066764, CDREAD=0x800694a8, POS2INT=0x80066cc8, INT2POS=0x80066bc4,
    CAVE6=0x800644a8, CAVE6_END=0x800646a0, CAVE8=0x8007860c, CAVE8_END=0x800787c0, MOVIEWAIT=(0x800218bc, 0x80021908), SAVEREAD=0x80020768,
    READALL=0x80040b18, BOOTREAD=0x80022a28, CARDTEST=0x80020464, CARDEXISTS=0x8002094c, READSLOT=0x80020728,
    CAVE7=0x800642a8, CAVE7_END=0x80064454, LOOPVSYNC=(0x80039700, 0x8004a3a0, 0x8004b0c4),
    BGM_COMBAT=0x8004aed0, BGM_SELECT=0x8003b4c0, PLAYBGM=0x8001fb18)

TABLES = {'PAL': PAL_V, 'US': US_V}

DEFAULTS = dict(
    summon_lists='vanilla',     # 'vanilla' | 'mod' (hand-picked early lists) | dict stage -> [(id, lv)]*8
    combat_exp=True,            # exp from dealing/taking damage + level-ups without a kill
    hardcore=False,             # refuse saving during battles
    lock_difficulty=None,       # None | 'normal' | 'hard'
    draft=None,                 # None | dict(rows={F: [ids<=6]}, levels={F: lv}, limits={F: n}, start=[ids], start_level)
    commander_buffs=True,       # buff the five non-Justice disciples
    hub=None,                   # None | dict(start=bitmask, unlocks={battle: bitmask}, progressive=[ids],
                                #              skip_tutorial=bool)
    fast_load=False,            # one disc request per file, load cache, quick card read at boot, LOADING image moved
    battle_music=True,          # False: one track per stage (no battle / phase music swaps: no music loads in battle)
    game_speed=None,            # None | 'fast' (~1.45x) | 'faster' (2x): game loops wait 1 vblank instead of 2 on some frames
    mailbox=False,
    text_fixes=False,           # proofread English (data/text_fixes.json): story, tutorial, items, spells,
                                # encyclopedia, monster and item names              # Archipelago mailbox (needs hub): client-delivered monsters between battles
)

def build(version, exe_in, monst_in, text_in, opts=None, face_in=None):
    """version 'PAL'/'US'; exe_in bytes; monst_in = MONST.TBL bytes; text_in = {name: bytes} for
    MAHOU.TXT, TUTORI.TXT, UNTIKU.TBL and the title script (URESET.MES / RESET.MES).
    Returns (exe, monst, {name: bytes}) - only the files that were changed."""
    o_ = dict(DEFAULTS); o_.update(opts or {}); opts = o_
    V = TABLES[version]; US = version == 'US'
    exe = bytearray(exe_in)
    text_out = {}
    def off(a): return a - BASE + 0x800
    def rd(a, n): return bytes(exe[off(a):off(a) + n])
    def wr(a, b): exe[off(a):off(a) + len(b)] = b
    def words(a, ws): wr(a, struct.pack('<%dI' % len(ws), *ws))
    def expect(a, hexstr):
        b = bytes.fromhex(hexstr.replace(' ', ''))
        assert rd(a, len(b)) == b, (hex(a), rd(a, len(b)).hex(), hexstr)

    # ---------- MIPS encoders ----------
    R = {'zero': 0, 'at': 1, 'v0': 2, 'v1': 3, 'a0': 4, 'a1': 5, 'a2': 6, 'a3': 7,
         's0': 16, 'ra': 31, 'fp': 30}
    def I(op, rs, rt, imm): return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xffff)
    def Rr(rs, rt, rd_, sh, fn): return (R[rs] << 21) | (R[rt] << 16) | (R[rd_] << 11) | (sh << 6) | fn
    lui = lambda rt, imm: I(0x0f, 'zero', rt, imm)
    ori = lambda rt, rs, imm: I(0x0d, rs, rt, imm)
    addiu = lambda rt, rs, imm: I(0x09, rs, rt, imm)
    sltiu = lambda rt, rs, imm: I(0x0b, rs, rt, imm)
    lw = lambda rt, o, rs: I(0x23, rs, rt, o)
    sw = lambda rt, o, rs: I(0x2b, rs, rt, o)
    lbu = lambda rt, o, rs: I(0x24, rs, rt, o)
    sb = lambda rt, o, rs: I(0x28, rs, rt, o)
    multu = lambda rs, rt: Rr(rs, rt, 'zero', 0, 0x19)
    mflo = lambda rd_: Rr('zero', 'zero', rd_, 0, 0x12)
    addu = lambda rd_, rs, rt: Rr(rs, rt, rd_, 0, 0x21)
    srl = lambda rd_, rt, sh: Rr('zero', rt, rd_, sh, 0x02)
    jr = lambda rs: Rr(rs, 'zero', 'zero', 0, 0x08)
    jal = lambda t: (3 << 26) | ((t >> 2) & 0x3ffffff)
    NOP = 0

    # ---------- 1. RNG fix ----------
    # Original returned a counter (+1 per call). New: proper LCG on the seed the
    # game already kept (initial value 123456), returning bits 16-31 (0..65535).
    # Every caller takes its own modulo.
    assert rd(V['RNG'], 8) == struct.pack('<2I', lui('a1', 0x8008), lw('v0', V['SEEDLO'], 'a1'))
    # v4: non-deterministic. Mix in root counter 1 (hblank counter at 0x1F801110,
    # always running: the game's VSync relies on it), so results depend on the
    # moment the player acts. seed = (seed + hblanks) * 0xE65D; return seed >> 16.
    # Must not touch a0 (the v3 magic code keeps a value in a0 across calls).
    words(V['RNG'], [
        lui('a1', 0x8008),
        lw('v0', V['SEEDLO'], 'a1'),
        lui('at', 0x1f80),
        I(0x25, 'at', 'at', 0x1110),     # lhu at, 0x1110(at)
        ori('v1', 'zero', 0xe65d),
        addu('v0', 'v0', 'at'),
        multu('v0', 'v1'),
        mflo('v0'),
        sw('v0', V['SEEDLO'], 'a1'),
        jr('ra'),
        srl('v0', 'v0', 16),
    ])

    # ---------- 2. Level cap at 99 (three level-up sites) ----------
    # Original: lbu v0,15(s0); nop; addiu v0,v0,1; sb v0,15(s0); jal rng; sb zero,2c(s0)
    for a in V['LVUP']:
        orig = [lbu('v0', 0x15, 's0'), NOP, addiu('v0', 'v0', 1), sb('v0', 0x15, 's0'),
                jal(V['RNG']), sb('zero', 0x2c, 's0')]
        assert rd(a, 24) == struct.pack('<6I', *orig), hex(a)
        words(a, [
            lbu('v0', 0x15, 's0'),
            sb('zero', 0x2c, 's0'),      # clear exp (moved up; fills load delay)
            sltiu('at', 'v0', 99),       # at = level < 99
            addu('v0', 'v0', 'at'),      # level += at  (never passes 99)
            jal(V['RNG']),
            sb('v0', 0x15, 's0'),        # store level in the delay slot
        ])

    # ---------- 3. Evolution table edits ----------
    ID = {}
    for line in monst_in.decode('cp932').split('\r\n'):
        m = re.match(r'(\d{3}),"([^"]+)"', line)
        if m: ID.setdefault(m.group(2).strip(), int(m.group(1)))
    T1, N1, T2, N2 = V['T1'], 58, V['T2'], 48
    pairs = [(T1 + 2 * i) for i in range(N1)] + [(T2 + 2 * i) for i in range(N2)]
    def find_pair(f, t):
        hits = [a for a in pairs if rd(a, 2) == bytes([ID[f], ID[t]])]
        assert len(hits) == 1, (f, t, hits); return hits[0]
    replace = [(('Death_Knight', 'Ninja'), ('Goblin', 'Orc')),
               (('Sorcerer', 'Knight'), ('Orc', 'Overlord')),
               (('Sorcerer', 'Death_Knight'), ('Wolfwere', 'Werewolf'))]
    for (f, t), (nf, nt) in replace:
        wr(find_pair(f, t), bytes([ID[nf], ID[nt]]))

    # ---------- 4. Fusion: remove Overlord recipes ----------
    # With Overlord's base level now 25, fusing Goblin+Orc would create a level-25
    # Overlord instantly. Disable those 3 recipes (pair no longer matches).
    F1 = V['F1']
    for i in range(42):
        a = F1 + 3 * i
        x, y, z = rd(a, 3)
        if z == ID['Overlord']:
            wr(a, b'\xff\xff\xff')

    # ---------- 5. Player summon lists, maps 0-5 ----------
    ST = V['ST']
    def set_list(stage, entries):
        a = ST + 72 * stage + 17
        assert len(entries) <= 8
        b = b''.join(bytes([ID[n] if n else 255, lv]) for n, lv in entries)
        b += bytes([255, 0]) * (8 - len(entries))
        wr(a, b)
    if opts['summon_lists'] == 'mod':
      set_list(0, [('Goblin', 1), ('Gremlin', 1), ('Skeleton', 1), ('Banshee', 1),
                 ('Ghost', 1), ('Roc', 1), ('Wolfwere', 1), ('Troll', 1)])
      set_list(1, [('Cherub', 2), ('Witch', 2), ('Fairy', 2), ('Harpy', 2),
                 ('Goblin', 2), ('Ancient', 2), ('Dragon', 1), ('Unicorn', 2)])
      set_list(2, [('Wolfwere', 2), ('Amazon', 3), ('Barbarian', 3), ('Magician', 3),
                 ('Troll', 3), ('Elf', 2), ('Roc', 2), ('Banshee', 2)])
      set_list(3, [('Soldier', 4), ('Neophyte', 4), ('Cherub', 2), ('Gremlin', 2),
                 ('Skeleton', 3), ('Unicorn', 4), ('Dragon', 3), ('Roc', 3)])
      set_list(4, [('Fighter', 5), ('Serpent', 2), ('Elf', 4), ('Octopus', 2),
                 ('Mermaid', 2), ('Berserker', 5), ('Roc', 4), ('Ghost', 2)])
      # stage 5 (Knight): vanilla 7 + Lizardman, otherwise only a bad-luck fusion result
      set_list(5, [('Gremlin', 4), ('Banshee', 2), ('Dragon', 5), ('Roc', 4),
                 ('Cherub', 4), ('Mermaid', 2), ('Serpent', 3), ('Lizardman', 6)])
    elif opts['summon_lists'] == 'balanced':
      # Public early lists: every map offers about three Law, two to three Neutral and three Chaos units
      # (each disciple has cheap summons whatever their alignment), a flyer or two, humans and monsters
      # mixed, at the original maps' levels. Every human base unit stays summonable somewhere.
      set_list(0, [('Soldier', 1), ('Witch', 1), ('Fairy', 1), ('Amazon', 1),
                   ('Troll', 1), ('Barbarian', 1), ('Goblin', 1), ('Gremlin', 1)])
      set_list(1, [('Cherub', 2), ('Elf', 2), ('Ancient', 2), ('Unicorn', 2),
                   ('Dragon', 1), ('Magician', 2), ('Skeleton', 2), ('Banshee', 2)])
      set_list(2, [('Soldier', 3), ('Witch', 3), ('Elf', 2), ('Amazon', 3),
                   ('Harpy', 2), ('Barbarian', 3), ('Magician', 3), ('Roc', 2)])
      set_list(3, [('Soldier', 4), ('Cherub', 2), ('Elf', 3), ('Neophyte', 4),
                   ('Unicorn', 4), ('Wolfwere', 3), ('Gremlin', 2), ('Skeleton', 3)])
      set_list(4, [('Fighter', 5), ('Cherub', 3), ('Mermaid', 2), ('Serpent', 2),
                   ('Harpy', 4), ('Berserker', 5), ('Octopus', 2), ('Ghost', 2)])
      set_list(5, [('Witch', 4), ('Cherub', 4), ('Mermaid', 2), ('Dragon', 5),
                   ('Serpent', 3), ('Gremlin', 4), ('Banshee', 2), ('Lizardman', 6)])
    elif isinstance(opts['summon_lists'], dict):
        for stage, entries in opts['summon_lists'].items():
            assert len(entries) <= 8
            b = b''.join(bytes([mid, lv]) for mid, lv in entries) + bytes([255, 0]) * (8 - len(entries))
            wr(ST + 72 * int(stage) + 17, b)
    else:
        assert opts['summon_lists'] == 'vanilla'

    # ---------- 7. Combat experience (v2) ----------
    # After every fight the game gave both units +1 exp (if exp < 99).
    # New: each unit gets max(1, 8 + oppLevel - ownLevel), capped at 150 (v10.1: was 99, which blocked the
    # no-kill level-up hook; 150 + a kill's max 100 still fits the exp byte).
    # Replaces 36 instructions at 0x8002B534..0x8002B5C0; v0 = 0x800D0000 on entry
    # and must be again at the end. Units: 0x800D6928 and 0x800CEEC0 (indices).
    R.update({'t0': 8, 't1': 9, 'a2': 6, 'a3': 7, 's7': 23})
    lhu = lambda rt, o, rs: I(0x25, rs, rt, o)
    subu = lambda rd_, rs, rt: Rr(rs, rt, rd_, 0, 0x23)
    def br(op, rs, rt, frm, to): return I(op, rs, rt, (to - frm - 4) >> 2)
    if opts['combat_exp']:
        A0 = V['CEXP']
        assert rd(A0, 4) == struct.pack('<I', lhu('v1', V['IDXA'], 'v0'))
        assert rd(A0 + 36 * 4, 4) == struct.pack('<I', lhu('v1', V['IDXA'], 'v0'))  # next block untouched
        pc = lambda n: A0 + 4 * (n - 1)          # address of instruction number n (1-based)
        code = [
            lhu('v1', V['IDXA'], 'v0'),          # 1  idx A
            lhu('a0', V['IDXB'], 'v0'),          # 2  idx B
            addiu('t1', 'zero', 74),             # 3  unit size
            multu('v1', 't1'),                   # 4
            mflo('a1'),                          # 5
            addu('a1', 'a1', V['UREG']),         # 6  unit A
            lbu('v0', 0x15, 'a1'),               # 7  lvA
            multu('a0', 't1'),                   # 8
            mflo('a2'),                          # 9
            addu('a2', 'a2', V['UREG']),         # 10 unit B
            lbu('v1', 0x15, 'a2'),               # 11 lvB
            lbu('a0', 0x2c, 'a1'),               # 12 expA
            subu('a3', 'v1', 'v0'),              # 13 d = lvB - lvA
            addiu('t0', 'a3', 8),                # 14 gA
            None,                                # 15 bgtz t0 -> 19
            addu('a0', 'a0', 't0'),              # 16 (delay)
            subu('a0', 'a0', 't0'),              # 17 undo when gA <= 0
            addiu('a0', 'a0', 1),                # 18 ... and give 1
            sltiu('at', 'a0', 151),              # 19
            None,                                # 20 bnez at -> 24
            sb('a0', 0x2c, 'a1'),                # 21 (delay)
            addiu('a0', 'zero', 150),            # 22
            sb('a0', 0x2c, 'a1'),                # 23
            lbu('a0', 0x2c, 'a2'),               # 24 expB
            addiu('t0', 'zero', 8),              # 25
            subu('t0', 't0', 'a3'),              # 26 gB = 8 - d
            None,                                # 27 bgtz t0 -> 31
            addu('a0', 'a0', 't0'),              # 28 (delay)
            subu('a0', 'a0', 't0'),              # 29
            addiu('a0', 'a0', 1),                # 30
            sltiu('at', 'a0', 151),              # 31
            None,                                # 32 bnez at -> 36
            sb('a0', 0x2c, 'a2'),                # 33 (delay)
            addiu('a0', 'zero', 150),            # 34
            sb('a0', 0x2c, 'a2'),                # 35
            lui('v0', 0x800d),                   # 36
        ]
        code[14] = br(0x07, 't0', 'zero', pc(15), pc(19))   # bgtz
        code[19] = br(0x05, 'at', 'zero', pc(20), pc(24))   # bnez
        code[26] = br(0x07, 't0', 'zero', pc(27), pc(31))
        code[31] = br(0x05, 'at', 'zero', pc(32), pc(36))
        assert len(code) == 36
        words(A0, code)

    # ---------- 8. Magic attacks use their per-level bonus (v3) ----------
    # Unit magic block: 0x45 power, 0x47 bonus min, 0x48 bonus max (+1 per level).
    # Original: dmg = p/2 + rand%(p/2) + 1 (bonus ignored).
    # New:      dmg = p/2 + rand%(p/2) + 1 + min + rand%(max-min+1)
    # Replaces 19 instructions 0x8002AF60..0x8002AFA8 (incl. compiler div-by-zero traps).
    divu = lambda rs, rt: Rr(rs, rt, 'zero', 0, 0x1b)
    mfhi = lambda rd_: Rr('zero', 'zero', rd_, 0, 0x10)
    R.update({'s1': 17, 's2': 18, 's3': 19})
    M0 = V['MAGIC']
    assert rd(M0, 4) == struct.pack('<I', lbu('s3', 0x45, 's0'))
    assert rd(M0 + 19 * 4, 4) == bytes.fromhex('ffffc332')  # andi v1,s6,0xffff at 0x8002AFAC
    magic = [
        lbu('s3', 0x45, 's0'),        # 1 power
        lbu('s1', 0x47, 's0'),        # 2 bonus min
        lbu('s2', 0x48, 's0'),        # 3 bonus max
        jal(V['RNG']),                # 4
        srl('a0', 's3', 1),           # 5 (delay) half power; RNG doesn't touch a0
        sltiu('at', 'a0', 1),         # 6
        addu('a0', 'a0', 'at'),       # 7 avoid /0
        subu('v1', 's2', 's1'),       # 8
        addiu('v1', 'v1', 1),         # 9 bonus range
        divu('v0', 'v1'),             # 10
        mfhi('v1'),                   # 11
        addu('s1', 's1', 'v1'),       # 12 bonus
        jal(V['RNG']),                # 13
        NOP,                          # 14
        divu('v0', 'a0'),             # 15
        mfhi('v1'),                   # 16
        addiu('v1', 'v1', 1),         # 17
        addu('s3', 'a0', 'v1'),       # 18 original roll
        addu('s3', 's3', 's1'),       # 19 + bonus
    ]
    words(M0, magic)

    # ---------- 9. Replaceable equipment (v5) ----------
    # Equipping onto a unit that already holds an item now swaps: the old item's
    # bonus is removed and the old item goes back into the inventory slot the new
    # one came from. Removal routine lives in an unreferenced function at
    # 0x80044540 (checked: no jal, pointer or lui/addiu reference anywhere).
    R.update({'t2': 10, 't3': 11, 't4': 12, 'sp': 29, 't8': 24, 't5': 13, 't6': 14, 't7': 15, 't9': 25, 's4': 20})
    def asm(base, prog):
        """prog: list of ('label',name) or (fn, args...) with branch targets as label strings."""
        labels, pc = {}, base
        for it in prog:
            if it[0] == 'label': labels[it[1]] = pc
            else: pc += 4
        out, pc = [], base
        for it in prog:
            if it[0] == 'label': continue
            op = it[0]
            if op in ('beq', 'bne', 'beqz'):
                if op == 'beqz': opc, rs, rt, tgt = 4, it[1], 'zero', it[2]
                else: opc, rs, rt, tgt = (4 if op == 'beq' else 5), it[1], it[2], it[3]
                out.append(I(opc, rs, rt, (labels[tgt] - pc - 4) >> 2))
            elif op == 'j': out.append((2 << 26) | ((it[1] >> 2) & 0x3ffffff))
            else: out.append(it[0](*it[1:]))
            pc += 4
        return out
    andi = lambda rt, rs, imm: I(0x0c, rs, rt, imm)
    NOPF = (lambda: 0,)
    sll = lambda rd_, rt, sh: Rr('zero', rt, rd_, sh, 0x00)
    CAVE = V['CAVE']
    assert rd(CAVE, 4) == bytes.fromhex('d0ffbd27')  # addiu sp,sp,-0x30 (original dead function)
    P = [
        (addiu, 'sp', 'sp', -24), (sw, 'ra', 16, 'sp'), (sw, 's0', 20, 'sp'),
        (addu, 's0', 'a0', 'zero'),                       # s0 = unit
        (lbu, 't0', 0x2d, 's0'),                          # old item id
        (lui, 't1', 0x8008), (addiu, 't1', 't1', V['ITEMLO']),
        (sll, 't2', 't0', 1), (addu, 't2', 't2', 't0'), (sll, 't2', 't2', 2), (addu, 't2', 't2', 't1'),
        (lbu, 't2', 6, 't2'),                             # value
        # swords 35-39: melee power -= value
        (addiu, 't3', 't0', -35), (sltiu, 't3', 't3', 5), ('beqz', 't3', 'bow'), (lbu, 't4', 0x39, 's0'), NOPF,  # load delay
        (subu, 't4', 't4', 't2'), (sb, 't4', 0x39, 's0'),
        ('label', 'bow'),
        (addiu, 't3', 't0', -40), (sltiu, 't3', 't3', 3), ('beqz', 't3', 'wand'), (lbu, 't4', 0x3f, 's0'), NOPF,  # load delay
        (subu, 't4', 't4', 't2'), (sb, 't4', 0x3f, 's0'),
        ('label', 'wand'),
        (addiu, 't3', 't0', -43), (sltiu, 't3', 't3', 3), ('beqz', 't3', 'arm1'), (lbu, 't4', 0x45, 's0'), NOPF,  # load delay
        (subu, 't4', 't4', 't2'), (sb, 't4', 0x45, 's0'),
        # Arms: 49 melee, 50 ranged, 51 magic, 52 all -> halve
        ('label', 'arm1'),
        (addiu, 't3', 'zero', 49), ('beq', 't0', 't3', 'm1'), (addiu, 't3', 'zero', 52), ('bne', 't0', 't3', 'arm2'), NOPF,
        ('label', 'm1'), (lbu, 't4', 0x39, 's0'), NOPF, (srl, 't4', 't4', 1), (sb, 't4', 0x39, 's0'),
        ('label', 'arm2'),
        (addiu, 't3', 'zero', 50), ('beq', 't0', 't3', 'm2'), (addiu, 't3', 'zero', 52), ('bne', 't0', 't3', 'arm3'), NOPF,
        ('label', 'm2'), (lbu, 't4', 0x3f, 's0'), NOPF, (srl, 't4', 't4', 1), (sb, 't4', 0x3f, 's0'),
        ('label', 'arm3'),
        (addiu, 't3', 'zero', 51), ('beq', 't0', 't3', 'm3'), (addiu, 't3', 'zero', 52), ('bne', 't0', 't3', 'move'), NOPF,
        ('label', 'm3'), (lbu, 't4', 0x45, 's0'), NOPF, (srl, 't4', 't4', 1), (sb, 't4', 0x45, 's0'),
        # Speed Boots 53 / Warp Ring 54 / Wing Ring 55: restore movement + type from monster data
        ('label', 'move'),
        (addiu, 't3', 't0', -53), (sltiu, 't3', 't3', 3), ('beqz', 't3', 'end'), NOPF,
        (lbu, 'a0', 1, 's0'), (jal, V['PARSE']), NOPF,
        (lui, 't4', 0x800f), (lbu, 't3', V['TPL_MOVE'], 't4'), (lbu, 't4', V['TPL_MP'], 't4'),
        (sb, 't3', 0x2a, 's0'), (sb, 't4', 0x2b, 's0'),
        ('label', 'end'),
        (lbu, 'v0', 0x2d, 's0'), (lw, 'ra', 16, 'sp'), (lw, 's0', 20, 'sp'),
        (jr, 'ra'), (addiu, 'sp', 'sp', 24),
    ]
    cave = asm(CAVE, P)
    assert len(cave) <= 120, len(cave)
    words(CAVE, cave)
    # Equip handler: replace the "already has an item" refusal (0x80033674, 20 instrs)
    H = V['EQ_H']
    expect(V['EQ_CHECK'], struct.pack('<I', lbu('v0', 0x2d, 'v1')).hex())
    if US:
        # US: the branch delay slot before this path overwrites v1 (unit address), so recompute it from the
        # unit index at 0x274(sp). Exactly fills the 17-instruction refusal path (next word is the empty-slot path).
        eq = asm(H, [
            (lhu, 'a0', 0x274, 'sp'), (addiu, 't0', 'zero', 74), (multu, 'a0', 't0'), (mflo, 'a0'),
            (addu, 'a0', 'a0', 'fp'), (jal, CAVE), NOPF,
            (lhu, 'v1', 0x260, 'sp'), (lui, 't8', 0x800e), (sll, 'v1', 'v1', 1),
            (addiu, 't8', 't8', V['INVLO']), (addu, 't8', 't8', 'v1'),
            (sb, 'v0', 0, 't8'), (addiu, 'v1', 'zero', 1), (sb, 'v1', 1, 't8'),
            ('j', V['EQ_CONT']), NOPF,
        ])
        assert H + 4 * len(eq) == 0x80033378 and rd(0x80033378, 4) == struct.pack('<I', lhu('a0', 0x260, 'sp'))
    else:
        eq = asm(H, [
            (jal, CAVE), (addu, 'a0', 'v1', 'zero'),        # a0 = unit address
            (lhu, 'v1', 0x260, 'sp'), (lui, 't8', 0x800e), (sll, 'v1', 'v1', 1),
            (addiu, 't8', 't8', V['INVLO']), (addu, 't8', 't8', 'v1'),
            (sb, 'v0', 0, 't8'),                            # slot item = old item
            (addiu, 'v1', 'zero', 1), (sb, 'v1', 1, 't8'),  # slot count = 1
            ('j', V['EQ_CONT']), NOPF,                      # continue the normal equip path
        ])
    words(H, eq)

    # ---------- 10. Experience carry-over (v6) ----------
    # a) Kill award no longer trimmed to reach exactly 100 (max 99 + 100 = 199, fits a byte).
    GA = V['KILLB']
    assert rd(GA, 4) == struct.pack('<I', I(5, 'v0', 'zero', (V['KILLT'] - GA - 4) >> 2))  # bnez v0
    words(GA, [I(4, 'zero', 'zero', (V['KILLT'] - GA - 4) >> 2)])                        # always skip trim
    # b) Kill level-up: level+1 (cap 99) and exp -= 100 instead of exp = 0. Routine in the dead function.
    CAVE2 = CAVE + 0x140
    assert CAVE2 >= CAVE + 4 * len(cave)
    words(CAVE2, asm(CAVE2, [
        (lbu, 'v0', 0x15, 'a0'), (lbu, 'v1', 0x2c, 'a0'),
        (sltiu, 'at', 'v0', 99), (addu, 'v0', 'v0', 'at'), (sb, 'v0', 0x15, 'a0'),
        (addiu, 'v1', 'v1', -100), (sb, 'v1', 0x2c, 'a0'),
        (jr, 'ra'), NOPF,
    ]))
    L1 = V['LVUP'][0]
    assert rd(L1, 4) == struct.pack('<I', lbu('v0', 0x15, 's0'))
    words(L1, [jal(CAVE2), addu('a0', 's0', 'zero'), jal(V['RNG']), NOP, NOP, NOP])

    # ---------- 12. (v9) Equipment swap plays the item animation ----------
    # 0x80031B38: equipment (item byte4 0xCE) on a unit that already has an item jumped straight to state 0x37
    # (the old "can't equip" path, now our swap) and skipped the use animation + charge use. Remove the early
    # exit so swaps take the normal flow; the handler at 0x80033664 still sees 0x2d != 0 and swaps.
    EA = V['ANIM']
    assert rd(EA, 4) == struct.pack('<I', I(5, 'v0', 'zero', (V['ANIM_T'] - EA - 4) >> 2))
    words(EA, [NOP])

    # ---------- 11. (v8) Tower items stack onto an existing copy ----------
    # Tower reward (0x80029F98..0x80029FEC) wrote [id, charges] into the first empty slot s4.
    # CAVE3(a0=id, a1=empty slot): non-equipment (effect != 14) items add their charges to an existing
    # slot with the same id (cap 99); otherwise write the new slot as before. Leaf, t-regs only.
    CAVE3 = CAVE + 0x180
    assert CAVE3 >= CAVE2 + 4 * 9
    cave3 = asm(CAVE3, [
        (lui, 't0', 0x8008), (addiu, 't0', 't0', V['ITEMLO']),
        (sll, 't1', 'a0', 1), (addu, 't1', 't1', 'a0'), (sll, 't1', 't1', 2), (addu, 't1', 't1', 't0'),
        (lbu, 't2', 9, 't1'),                       # charges
        (lbu, 't3', 4, 't1'),                       # effect
        (lui, 't4', 0x800e), (addiu, 't4', 't4', V['INVLO']),   # inventory [id,count] x 50
        (andi, 't3', 't3', 0x3f), (addiu, 't5', 'zero', 14),
        ('beq', 't3', 't5', 'new'), (addiu, 't6', 'zero', 0),
        ('label', 'loop'),
        (sll, 't7', 't6', 1), (addu, 't7', 't7', 't4'),
        (lbu, 't8', 0, 't7'), (lbu, 't9', 1, 't7'),
        ('bne', 't8', 'a0', 'next'), NOPF,
        ('beqz', 't9', 'next'), NOPF,
        (addu, 't9', 't9', 't2'), (sltiu, 't8', 't9', 100),
        ('bne', 't8', 'zero', 'ok'), NOPF,
        (addiu, 't9', 'zero', 99),
        ('label', 'ok'), (jr, 'ra'), (sb, 't9', 1, 't7'),
        ('label', 'next'), (addiu, 't6', 't6', 1), (sltiu, 't8', 't6', 50),
        ('bne', 't8', 'zero', 'loop'), NOPF,
        ('label', 'new'),
        (sll, 't7', 'a1', 1), (addu, 't7', 't7', 't4'),
        (sb, 'a0', 0, 't7'), (jr, 'ra'), (sb, 't2', 1, 't7'),
    ])
    assert CAVE3 + 4 * len(cave3) <= V['CAVE_END']
    words(CAVE3, cave3)
    TW = V['TOWER']
    assert rd(TW, 4) == struct.pack('<I', andi('v1', 's4', 0xffff))
    assert rd(V['TOWER_MSG'], 4) == struct.pack('<I', jal(V['MSGFN']))
    tw = [lhu('a0', 0x260, 'sp'), andi('a1', 's4', 0xffff), jal(CAVE3), NOP,
          (2 << 26) | ((V['TOWER_MSG'] >> 2) & 0x3ffffff), lhu('a0', 0x260, 'sp')]   # a0 = item id for message
    tw += [NOP] * ((V['TOWER_MSG'] - TW) // 4 - len(tw))
    words(TW, tw)

    # ---------- 13. (v10) Level-ups without a kill ----------
    # Combat exp (step 7) can push a unit to 100 without a kill, but only the kill path ran the level-up check.
    # HOOK: if the attacker (0x800D6928) or defender (0x800CEEC0) is alive (byte0 & 3) with exp >= 100, hand it to
    # state 18 exactly like the spell code does (sh idx,0x26e(sp); v0=0x12; j 0x80038B14); else continue to the
    # normal end of action 0x80037334. Entered from the no-kill end of combat (0x8002B6C4), the zero-gain kill end
    # (0x8002BDD8) and the end of the evolution check (0x8002C868), so after one level-up the other unit (or a
    # second level-up) is caught on the next pass. Same register/stack frame as the battle function (s7 = units).
    if opts['combat_exp']:
        sh_ = lambda rt, o, rs: I(0x29, rs, rt, o)
        HOOK = CAVE + 0x240
        assert HOOK >= CAVE3 + 4 * len(cave3)
        hook = asm(HOOK, [
            (lui, 't0', 0x800d), (lhu, 't1', V['IDXA'], 't0'), (addiu, 't3', 'zero', 2), NOPF,
            ('label', 'loop'),
            (sltiu, 't2', 't1', 0x78), ('beqz', 't2', 'next'), NOPF,
            (sll, 't2', 't1', 3), (addu, 't2', 't2', 't1'), (sll, 't2', 't2', 2), (addu, 't2', 't2', 't1'),
            (sll, 't2', 't2', 1), (addu, 't2', 't2', V['UREG']),
            (lbu, 'v0', 0, 't2'), NOPF, (andi, 'v0', 'v0', 3), ('beqz', 'v0', 'next'), NOPF,
            (lbu, 'v0', 0x2c, 't2'), NOPF, (sltiu, 'v0', 'v0', 100), ('bne', 'v0', 'zero', 'next'), NOPF,
            (sh_, 't1', 0x26e, 'sp'), ('j', V['SETSTATE']), (addiu, 'v0', 'zero', 0x12),
            ('label', 'next'),
            (addiu, 't3', 't3', -1), ('beqz', 't3', 'done'), NOPF,
            (lhu, 't1', V['IDXB'], 't0'), ('beq', 'zero', 'zero', 'loop'), NOPF,
            ('label', 'done'),
            ('j', V['ENDACT']), NOPF,
        ])
        assert HOOK + 4 * len(hook) <= V['CAVE_END']
        words(HOOK, hook)
        jhook = (2 << 26) | ((HOOK >> 2) & 0x3ffffff)
        HS = V['HOOK_SITES']
        assert rd(HS[0], 4) == struct.pack('<I', (2 << 26) | ((V['ENDACT'] >> 2) & 0x3ffffff))
        words(HS[0], [jhook])
        for a in HS[1:]:
            assert rd(a, 4) == struct.pack('<I', I(4, 'v0', 'zero', (V['ENDACT'] - a - 4) >> 2))
            words(a, [I(4, 'v0', 'zero', (HOOK - a - 4) >> 2)])


    # ---------- 16. Difficulty lock (rando) ----------
    # Game Lev. (0 Easy / 1 Normal / 2 Hard) is read in two places in the damage code and once by the
    # Environment menu display. Replace those reads with the locked constant: the menu still cycles the
    # variable, but nothing reads it any more, and old saves can't bring Easy back.
    if opts['lock_difficulty']:
        L = {'normal': 1, 'hard': 2}[opts['lock_difficulty']]
        for a, reg in V['DIFF_READS']:
            ins = struct.unpack_from('<I', rd(a, 4))[0]
            assert ins >> 26 == 0x25 and (ins & 0xffff) == (V['DIFF_LO'] & 0xffff) and (ins >> 16) & 31 == R[reg], hex(a)
            words(a, [addiu(reg, 'zero', L)])

    # ---------- 17. Hardcore: no saving during battles (rando) ----------
    # Between-battle screens (unit/delete screen SYS 6, save screen SYS 7) go through the SYS default path,
    # which stores the sub number in the 'unit mode' halfword; every SYS call clears it, battles never set it.
    # The save routine now refuses (returns 1 -> "Unable to save data.") when it is 0, i.e. outside those
    # screens. (v1 used the battle flag, but in-battle event SYS calls clear that one -> saves went through.)
    if opts['hardcore']:
        HC = CAVE + 0x2c8                                     # right after the level-up HOOK
        SF = V['SAVEFN']
        assert rd(SF, 8) == struct.pack('<2I', addiu('sp', 'sp', -0x78), addiu('t9', 'zero', 6))
        # the SYS default path (= DRAFT_SITE, before step 18 patches its first 3 words) sets the mode flag
        assert rd(V['DRAFT_SITE'] + 12, 4) == struct.pack('<I', I(0x29, 'v0', 'v1', V['UNITMODE_LO']))
        hc = asm(HC, [
            (lui, 'v0', 0x8008), (lhu, 'v0', V['UNITMODE_LO'], 'v0'), NOPF,
            ('beq', 'v0', 'zero', 'refuse'), NOPF,
            (addiu, 'sp', 'sp', -0x78), ('j', SF + 8), (addiu, 't9', 'zero', 6),
            ('label', 'refuse'), (jr, 'ra'), (addiu, 'v0', 'zero', 1),
        ])
        assert HC + 4 * len(hc) <= V['CAVE_END']
        words(HC, hc)
        words(SF, [(2 << 26) | ((HC >> 2) & 0x3ffffff), NOP])

    draft_start = None
    # ---------- ADD(a0 = monster id, a1 = level): a carried roster unit for side 0 (draft mode, AP mailbox) ----------
    # create(slot, id, x, y, [sp+0x10] level) builds a unit in table slot `slot` for side *SIDE (a global),
    # flag byte 1; ADD picks the first free slot >= 4 (0-3 are commanders), forces side 0 and then marks the
    # unit carried (2), like the units kept between battles.
    def add_prog():
            CR = V['CREATE']
            ins = lambda a: struct.unpack_from('<I', rd(a, 4))[0]
            UNIT_LO = ins(CR + 0x88) & 0xffff                    # addiu a0,a0,<units lo> in create()
            assert ins(CR + 0x88) >> 16 == 0x2484 and ins(CR + 0x84) == lui('a0', 0x800c)
            SIDE_LO = ins(CR + 0x120) & 0xffff                   # lbu v0,<side lo>(v0) in create()
            assert ins(CR + 0x120) >> 16 == 0x9042
            hi = lambda a: ((a + 0x8000) >> 16) & 0xffff
            lo = lambda a: a & 0xffff
            R.update({'s2': 18, 's3': 19, 's5': 21})
            sw_ = sw
            lhu_ = lhu
            sh2 = lambda rt, o, rs: I(0x29, rs, rt, o)
            mul74 = lambda d, x, base: [(sll, d, x, 3), (addu, d, d, x), (sll, d, d, 2), (addu, d, d, x),
                                        (sll, d, d, 1), (addu, d, d, base)]
            return [   # ADD(a0 = monster id, a1 = level)
                (addiu, 'sp', 'sp', -40), (sw_, 'ra', 32, 'sp'), (sw_, 's0', 28, 'sp'), (sw_, 's1', 24, 'sp'),
                (sw_, 's2', 20, 'sp'),
                (addu, 's1', 'a0', 'zero'), (addu, 's2', 'a1', 'zero'),
                (lui, 't0', 0x800c), (addiu, 't0', 't0', UNIT_LO - 0x10000 if UNIT_LO & 0x8000 else UNIT_LO),
                (addiu, 's0', 'zero', 4),
                ('label', 'find')] + mul74('t1', 's0', 't0') + [
                (lbu, 't2', 0, 't1'), NOPF, ('beqz', 't2', 'found'), NOPF,
                (addiu, 's0', 's0', 1), (sltiu, 't2', 's0', 0x78), ('bne', 't2', 'zero', 'find'), NOPF,
                ('beq', 'zero', 'zero', 'done'), NOPF,
                ('label', 'found'),
                (lui, 't3', 0x800f), (lhu_, 't4', SIDE_LO, 't3'), (sh2, 'zero', SIDE_LO, 't3'),
                (sw_, 't4', 12, 'sp'), (sw_, 's2', 16, 'sp'),
                (addu, 'a0', 's0', 'zero'), (addu, 'a1', 's1', 'zero'), (addu, 'a2', 'zero', 'zero'),
                (jal, CR), (addu, 'a3', 'zero', 'zero'),
                (lw, 't4', 12, 'sp'), (lui, 't3', 0x800f), (sh2, 't4', SIDE_LO, 't3'),
                (lui, 't0', 0x800c), (addiu, 't0', 't0', UNIT_LO - 0x10000 if UNIT_LO & 0x8000 else UNIT_LO),
                ] + mul74('t1', 's0', 't0') + [
                (addiu, 't2', 'zero', 2), (sb, 't2', 0, 't1'),
                ('label', 'done'),
                (lw, 'ra', 32, 'sp'), (lw, 's0', 28, 'sp'), (lw, 's1', 24, 'sp'), (lw, 's2', 20, 'sp'),
                (jr, 'ra'), (addiu, 'sp', 'sp', 40),
            ]

    # ---------- 20. Archipelago mailbox (rando, needs the hub) ----------
    # MBOX = 8 x (monster id, level), id 255 = empty; not saved (plain RAM in the exe image). The client writes
    # the level first, then the id. MAIL turns every filled entry into a carried roster unit (ADD), empties it
    # and adds 1 to the received counter F[68..69] (saved with the game). Called at the post-battle unit screen
    # (SYS 6, before the screen lists the units), when the hub opens after a battle (SYS 19 tail) and when a
    # between-battle save is loaded. Lives at the end of CAVE5 (step 19 keeps below MAILBASE).
    MAILBASE = mailcore = None
    if opts.get('mailbox'):
        assert opts['hub'], 'the mailbox needs the hub'
        R.update({'s1': 17, 's2': 18})
        sh5 = lambda rt, o, rs: I(0x29, rs, rt, o)
        lhu5 = lambda rt, o, rs: I(0x25, rs, rt, o)
        hi5 = lambda a: ((a + 0x8000) >> 16) & 0xffff
        addp = add_prog()
        def mail_prog(MBOX, MADD, MAILA):
          return [
            ('label', 'MAIL'),          # saves everything it uses except t*
            (addiu, 'sp', 'sp', -40), (sw, 'ra', 32, 'sp'), (sw, 's0', 28, 'sp'), (sw, 's1', 24, 'sp'),
            (sw, 'v0', 20, 'sp'), (sw, 'v1', 16, 'sp'), (sw, 'a0', 12, 'sp'), (sw, 'a1', 8, 'sp'),
            (sw, 'a2', 4, 'sp'), (sw, 'a3', 0, 'sp'),
            (lui, 's0', hi5(MBOX)), (addiu, 's0', 's0', MBOX & 0xffff),
            (addiu, 's1', 's0', 16),
            ('label', 'ml'),
            (lbu, 'a0', 0, 's0'), (addiu, 't0', 'zero', 255), ('beq', 'a0', 't0', 'mn'), (sltiu, 't0', 'a0', 136),
            ('beqz', 't0', 'mc'), NOPF,                                  # bad id: just clear it
            (jal, MADD), (lbu, 'a1', 1, 's0'),
            (lui, 't0', 0x800d), (lhu5, 't1', V['FLAGS_LO'] + 68, 't0'), NOPF,
            (addiu, 't1', 't1', 1), (sh5, 't1', V['FLAGS_LO'] + 68, 't0'),
            ('label', 'mc'),
            (addiu, 't0', 'zero', 255), (sb, 't0', 0, 's0'),
            ('label', 'mn'),
            (addiu, 's0', 's0', 2), ('bne', 's0', 's1', 'ml'), NOPF,
            (lw, 'ra', 32, 'sp'), (lw, 's0', 28, 'sp'), (lw, 's1', 24, 'sp'),
            (lw, 'v0', 20, 'sp'), (lw, 'v1', 16, 'sp'), (lw, 'a0', 12, 'sp'), (lw, 'a1', 8, 'sp'),
            (lw, 'a2', 4, 'sp'), (lw, 'a3', 0, 'sp'),
            (jr, 'ra'), (addiu, 'sp', 'sp', 40),
            ('label', 'MAIL6'),         # SYS default path (no draft): sub 6 -> MAIL; then the replaced code
            (andi, 't0', V['SUBREG'], 0xffff), (addiu, 't1', 'zero', 6), ('bne', 't0', 't1', 'm6'), NOPF,
            (addiu, 'sp', 'sp', -8), (sw, 'ra', 0, 'sp'), (jal, MAILA), NOPF,
            (lw, 'ra', 0, 'sp'), (addiu, 'sp', 'sp', 8),
            ('label', 'm6'),
            (addiu, 'v1', 'zero', 1), (lui, 'v0', 0x8008), (jr, 'ra'), (sh5, 'v1', V['DRAFT_LO'], 'v0'),
        ]
        nm = sum(1 for it in mail_prog(0, 0, 0) if it[0] != 'label')
        na = sum(1 for it in addp if it[0] != 'label')
        MAILBASE = (V['CAVE5_END'] - 16 - 4 * (nm + na)) & ~3
        MBOX, MADD, MCODE = MAILBASE, MAILBASE + 16, MAILBASE + 16 + 4 * na
        assert MBOX == V['MBOX'], 'mailbox moved: update V[MBOX] and the BizHawk client (%x)' % MBOX
        lab, pc = {}, MCODE
        for it in mail_prog(0, 0, 0):
            if it[0] == 'label': lab[it[1]] = pc
            else: pc += 4
        assert pc <= V['CAVE5_END']
        wr(MBOX, b'\xff' * 16)
        words(MADD, asm(MADD, addp))
        words(MCODE, asm(MCODE, mail_prog(MBOX, MADD, lab['MAIL'])))
        mailcore = lab['MAIL']
        if not opts['draft']:
            DS = V['DRAFT_SITE']
            assert rd(DS, 8) == struct.pack('<2I', addiu('v1', 'zero', 1), I(0x29, 'v0', 'v1', V['DRAFT_LO']))
            words(DS, [jal(lab['MAIL6']), NOP])

    # ---------- 18. Draft mode (rando) ----------
    # Story post-battle sequence: SYS(0,6,65535) = unit screen (delete monsters), SYS(0,19) cleanup, F[51]++.
    # SYS 6 enters the giant SYS function's default path (0x800232C8). DRAFT runs there: for the story screen it
    # creates this stage's drafted monsters as carried roster units (flag byte 2) and sets LIMVAR = the roster
    # limit (other SYS calls through this path set LIMVAR = 29). Only story scripts call SYS 6 (VS uses SYS 2,
    # free maps SYS 14): SYS(0,6,65535) after a battle, SYS(0,6,1) after a battle resumed from a save. The screen's exit check (count of side-0
    # units incl. the commander < 31) becomes count < LIMVAR + 2. START adds the starting monsters right after
    # the commander is created at new game (SYS 5). create(slot, id, x, y, [sp+0x10] level) builds a unit in
    # table slot `slot` for side *SIDE (a global), flag byte 1; ADD picks the first free slot >= 4 (0-3 are
    # commanders), forces side 0 and then marks the unit carried (2).
    if opts['draft']:
        dr = opts['draft']
        NROW, NR = 6, 27                                      # rows: F 0-22, F 30/32/34 -> 23-25, start = 26
        rowof = lambda F: F if F < 23 else (F >> 1) + 8
        assert [rowof(F) for F in (30, 32, 34)] == [23, 24, 25]
        DATA = CAVE + 0x2c8 + 40                              # after HOOK + hardcore routine
        LVO, LMO = NR * NROW, NR * NROW + NR
        LIMVAR = DATA + LMO + NR
        data = bytearray([255] * (NR * NROW)) + bytearray(NR) + bytearray([29] * NR) + bytes([29])
        data += bytes(-len(data) % 4)
        rows = {rowof(F): ids for F, ids in dr['rows'].items()}; rows[26] = dr['start']
        levels = {rowof(F): lv for F, lv in dr['levels'].items()}; levels[26] = dr['start_level']
        for r, ids in rows.items():
            assert 0 <= r < NR and len(ids) <= NROW
            data[r * NROW:r * NROW + len(ids)] = bytes(ids)
        for r, lv in levels.items(): data[LVO + r] = lv
        for F, lim in dr['limits'].items(): data[LMO + rowof(F)] = min(29, lim)
        assert len(data) % 4 == 0
        CODE = DATA + len(data)
        hi = lambda a: ((a + 0x8000) >> 16) & 0xffff
        lo = lambda a: a & 0xffff
        R.update({'s2': 18, 's3': 19, 's5': 21})
        sw_ = sw
        sh2 = lambda rt, o, rs: I(0x29, rs, rt, o)
        ADD = CODE
        add = add_prog()
        addc = asm(ADD, add)
        ROWS = ADD + 4 * len(addc)
        rowsub = [   # ROWADD(a0 = row F): add every id in row F at that row's level
            (addiu, 'sp', 'sp', -32), (sw_, 'ra', 24, 'sp'), (sw_, 's0', 20, 'sp'), (sw_, 's2', 16, 'sp'),
            (sw_, 's3', 12, 'sp'),
            (lui, 's2', hi(DATA)), (addiu, 's2', 's2', lo(DATA)),
            (addu, 't0', 's2', 'a0'), (lbu, 's3', LVO, 't0'),           # level
            (sll, 't0', 'a0', 1), (addu, 't0', 't0', 'a0'), (sll, 't0', 't0', 1),   # F*6
            (addu, 's0', 's2', 't0'), (addiu, 's2', 's0', NROW),         # s0 = row ptr, s2 = row end
            ('label', 'rl'),
            (lbu, 'a0', 0, 's0'), (addiu, 't0', 'zero', 255), ('beq', 'a0', 't0', 'rn'), NOPF,
            (jal, ADD), (addu, 'a1', 's3', 'zero'),
            ('label', 'rn'),
            (addiu, 's0', 's0', 1), ('bne', 's0', 's2', 'rl'), NOPF,
            (lw, 'ra', 24, 'sp'), (lw, 's0', 20, 'sp'), (lw, 's2', 16, 'sp'), (lw, 's3', 12, 'sp'),
            (jr, 'ra'), (addiu, 'sp', 'sp', 32),
        ]
        rowc = asm(ROWS, rowsub)
        DRAFT = ROWS + 4 * len(rowc)
        # the default path's own code compares the subcommand register with 8: check that it is SUBREG
        assert rd(V['DRAFT_SITE'] + 40, 4) == struct.pack('<I', andi('v1', V['SUBREG'], 0xffff)), 'subcommand register'
        draftc = asm(DRAFT, [   # called from the SYS default path; SUBREG = subcommand, caller frame at sp+32
            (addiu, 'sp', 'sp', -32), (sw_, 'ra', 24, 'sp'),
            (lui, 't3', hi(LIMVAR)), (addiu, 't2', 'zero', 29), (sb, 't2', lo(LIMVAR), 't3'),
            (andi, 't0', V['SUBREG'], 0xffff), (addiu, 't1', 'zero', 6), ('bne', 't0', 't1', 'out'), NOPF,
            # (SYS 6 is only used by the story: param 65535 after a battle, 1 after a battle resumed from a save)
            (lui, 't0', 0x800d), (lbu, 'a0', (V['FLAGS_LO'] + 0x33) & 0xffff, 't0'), NOPF,
            (sltiu, 't0', 'a0', 23), ('bne', 't0', 'zero', 'row'), NOPF,
            (srl, 'a0', 'a0', 1), (addiu, 'a0', 'a0', 8),         # F 30/32/34 -> rows 23/24/25
            (sltiu, 't0', 'a0', 26), ('beqz', 't0', 'out'), NOPF,
            ('label', 'row'),
            (lui, 't3', hi(DATA)), (addiu, 't3', 't3', lo(DATA)), (addu, 't3', 't3', 'a0'),
            (lbu, 't2', LMO, 't3'), (lui, 't3', hi(LIMVAR)), (sb, 't2', lo(LIMVAR), 't3'),
            (jal, ROWS), NOPF,
        ] + ([(jal, mailcore), NOPF] if mailcore else []) + [
            ('label', 'out'),
            (lw, 'ra', 24, 'sp'), (addiu, 'sp', 'sp', 32),
            (addiu, 'v1', 'zero', 1), (lui, 'v0', 0x8008), (jr, 'ra'), (sh2, 'v1', V['DRAFT_LO'], 'v0'),
        ])
        START = DRAFT + 4 * len(draftc)
        startc = asm(START, [   # after the commander is created at new game; must return v0 = 0x800F0000, s4 = 0
            (addiu, 'sp', 'sp', -24), (sw_, 'ra', 16, 'sp'),
            (jal, ROWS), (addiu, 'a0', 'zero', 26),
            (lw, 'ra', 16, 'sp'), (addiu, 'sp', 'sp', 24),
            (lui, 'v0', 0x800f), (jr, 'ra'), (addu, 's4', 'zero', 'zero'),
        ])
        LIMF = START + 4 * len(startc)
        limc = asm(LIMF, [      # v0 = unit count (incl. commander) -> v0 = count < LIMVAR + 2
            (lui, 't0', hi(LIMVAR)), (lbu, 't1', lo(LIMVAR), 't0'), NOPF, (addiu, 't1', 't1', 2),
            (jr, 'ra'), (Rr, 'v0', 't1', 'v0', 0, 0x2b),
        ])
        END = LIMF + 4 * len(limc)
        assert END <= V['CAVE_END'], hex(END - V['CAVE_END'])
        wr(DATA, bytes(data))
        for a, c in ((ADD, addc), (ROWS, rowc), (DRAFT, draftc), (START, startc), (LIMF, limc)): words(a, c)
        # hook sites
        DS = V['DRAFT_SITE']
        assert rd(DS, 8) == struct.pack('<2I', addiu('v1', 'zero', 1), sh2('v1', V['DRAFT_LO'], 'v0'))
        words(DS, [jal(DRAFT), NOP])
        SS = V['START_SITE']
        assert rd(SS, 8) == struct.pack('<2I', addu('s4', 'zero', 'zero'), lui('v0', 0x800f))
        draft_start = START                                   # step 19 chains to it when the hub is on
        if not opts['hub']: words(SS, [jal(START), NOP])
        LS = V['LIMIT_SITE']
        assert rd(LS, 8) == struct.pack('<2I', NOP, sltiu('v0', 'v0', 0x1f))
        words(LS, [jal(LIMF), NOP])

    # ---------- 19. Stage-select hub (rando) ----------
    # After every story battle the script runs SYS(0,6) (unit screen), SYS(0,19) (cleanup), then F[51]++ and
    # picks the next stage's script block by F[51] (ustart0/1 hand off to each other for any value). With the
    # hub, SYS 19 continues into the Map Mode select screen: SYS 11's main loop, minus its unit wipe, with the
    # SYS default path's flags (unit mode 1 is what lets the loop return to the script at state 0), in a third
    # mode (2). Battle ids: 0 tutorial, 1-22 story, 23-25 finals, 26-28 extras (= F 30/32/34). Picking the
    # tutorial after a battle writes F[51] = 255, and the script's +1 wraps it to 0 (F is a byte array). Battle b plays on
    # MAP(b+1).DAT, so the preview loader reads MAP01..29 into slots 0..28 (slot = id).
    # Saved state (story flags, saved with every save; unused by scripts and code): F[60..63] unlocked battle
    # bits, F[64..67] cleared battle bits, F[68..69] items received (Archipelago client), F[70] spare,
    # F[71] spare.
    # Post-battle: the clear bit is set, the offline unlock table ORed in, and (progressive mode) a first clear
    # opens the next locked stage of a fixed order; the hub opens unless the battle
    # was 22 or a final (-> ending) or nothing is unlocked. Confirm writes F[51] = F(id) - 1 (the script adds 1).
    # Loading a between-battle save (game mode 1 -> result 0x1234) opens the hub too; there confirm writes
    # F(id) and result 0x1234, so the script re-dispatches as on a normal load. Triangle is ignored.
    # New game: unlock bits = start mask. skip_tutorial: the title script's story new game calls SYS 12 instead
    # of SYS 5 (= SYS 5 + hub at its end, confirm returns F as the result) and stores F[51] = S instead of 0,
    # so the story starts at the picked stage; the tutorial (id 0) is just a hub stage.
    # Code + data live in an unreachable libgpu block (CAVE4; reachability-checked on both exes).
    if opts['hub']:
        hub = opts['hub']
        R.update({'s1': 17, 's2': 18, 's3': 19, 's5': 21, 't1': 9, 't0': 8})
        lhu2 = lambda rt, o, rs: I(0x25, rs, rt, o)
        sh3 = lambda rt, o, rs: I(0x29, rs, rt, o)
        or_ = lambda rd_, rs, rt: Rr(rs, rt, rd_, 0, 0x25)
        srlv = lambda rd_, rt, rs: Rr(rs, rt, rd_, 0, 0x06)
        sllv = lambda rd_, rt, rs: Rr(rs, rt, rd_, 0, 0x04)
        hi = lambda a: ((a + 0x8000) >> 16) & 0xffff
        lo = lambda a: a & 0xffff
        s16 = lambda x: struct.unpack('<h', struct.pack('<H', x & 0xffff))[0]
        wd = lambda a: struct.unpack_from('<I', rd(a, 4))[0]
        jmp = lambda t: (2 << 26) | ((t >> 2) & 0x3ffffff)
        M = V['MODE_LO']; FL = V['FLAGS_LO']
        F51, UNL, CLR = FL + 0x33, FL + 60, FL + 64                  # lui 0x800d based
        assert (0x800d0000 + UNL) % 4 == 0
        init, table = hub['start'], hub.get('unlocks', {})
        HUBIDS = [b for b in range(0, 29) if not 23 <= b <= 25]
        assert init and not init & ~sum(1 << b for b in HUBIDS), hex(init)
        C4, C4E = V['CAVE4'], V['CAVE4_END']
        assert rd(C4, 12) == struct.pack('<3I', addiu('v0', 'zero', 3), sb('v0', 3, 'a0'), addiu('v0', 'zero', 0x40))
        # CAVE5 (another unreachable library function): UTAB[29] = unlock mask per cleared battle
        C5 = V['CAVE5']
        assert wd(C5) == addiu('sp', 'sp', -0x20) and wd(C5 + 8) == addu('s0', 'a0', 'zero')
        UTAB = C5
        utab = b''.join(struct.pack('<I', table.get(b, 0)) for b in range(29))
        # progressive unlocks: every NEW clear opens the first still-locked stage of ORD (0xff-terminated)
        prog_order = hub.get('progressive') or []
        assert all(b in HUBIDS for b in prog_order) and len(prog_order) <= 31
        ORD = C5 + len(utab)
        utab += bytes(prog_order) + b'\xff' * (32 - len(prog_order))
        PROGF = C5 + len(utab)
        pcode = asm(PROGF, [
            ('bne', 't9', 'zero', 'po'), (lui, 't6', hi(ORD)),          # t9 != 0: stage was cleared before
            (addiu, 't6', 't6', lo(ORD)), (lw, 't5', UNL, 't0'),
            ('label', 'pl'),
            (lbu, 't7', 0, 't6'), (addiu, 't6', 't6', 1), (addiu, 't8', 'zero', 0xff),
            ('beq', 't7', 't8', 'po'), (addiu, 't8', 'zero', 1),
            (sllv, 't8', 't8', 't7'), (Rr, 't5', 't8', 't9', 0, 0x24),  # and t9,t5,t8
            ('bne', 't9', 'zero', 'pl'), NOPF,
            (or_, 't5', 't5', 't8'), (sw, 't5', UNL, 't0'),
            ('label', 'po'),
            (jr, 'ra'), NOPF])
        utab += b''.join(struct.pack('<I', w) for w in pcode)
        C5END = MAILBASE or V['CAVE5_END']
        assert C5 + len(utab) <= C5END
        wr(C5, utab)
        # CAVE4 data: HUBX byte (1 = script adds 1) | ENDV | template
        d = b''
        HUBX = C4 + len(d); d += bytes(4)
        ENDV = C4 + len(d); d += bytes(4)
        HUBT = C4 + len(d); d += b'STG01\xa5Story'.ljust(16, b'\x00')
        CODE = C4 + len(d)
        # original-code checks
        LS, LE = V['HUB_LIST'], V['HUB_LIST'] + 0x44
        assert wd(LS) == addu('s4', 'zero', 'zero') and rd(LE, 4) == struct.pack('<I', lui('v0', 0x800d))
        LIST_LO = wd(LS + 8) & 0xffff; COUNT_LO = wd(LS + 0x24) & 0xffff
        assert wd(LS + 8) >> 16 == 0x2445 and wd(LS + 0x24) >> 16 == 0x9462     # addiu a1,v0 / lhu v0,(v1)
        PS = V['HUB_PREV']
        assert wd(PS + 4) == lhu2('v0', M, 'v0') and wd(PS + 16) == addiu('s5', 'zero', 0x33) \
            and wd(PS + 20) == addiu('s5', 'zero', 0x1f)
        ES = V['HUB_END']
        assert wd(ES + 8) == addiu('v0', 'v0', 0x14) and wd(ES + 4) == andi('v0', 's5', 0xffff)
        LOOPANDI, ENDBNE = wd(ES), wd(ES + 12)
        assert LOOPANDI >> 16 in (0x3263, 0x3243) and ENDBNE >> 16 == 0x1462        # andi v1,s3|s2 / bne v1,v0
        LB = V['HUB_LABEL']
        assert wd(LB) == lui('v0', 0x8001) and wd(LB + 4) >> 16 == 0x2446
        TPL_LO = wd(LB + 4) & 0xffff
        CS = V['HUB_CONF']
        assert wd(CS) == addiu('s4', 's4', 0x32) and wd(CS - 4) == addiu('s4', 's4', 0x1e)
        KS = V['HUB_CANC']
        assert wd(KS) == andi('v0', 't7', 0x10) and wd(KS + 8) == lui('v0', 0x800b)
        assert wd(KS + 4) == I(4, 'v0', 'zero', (V['CANC_IGN'] - KS - 8) >> 2)       # beqz v0,CANC_IGN
        SJ = V['HUB_SYS19J']
        assert rd(SJ, 8) == struct.pack('<2I', jmp(V['SYSRET']), NOP) and wd(SJ - 8) >> 26 == 3
        SUB = V['SUBREG']
        DS = V['DRAFT_SITE']                                    # SYS default path (subs 6/7/8/11...)
        assert wd(DS + 12) == sh3('v1', V['UNITMODE_LO'], 'v0') and wd(DS + 20) >> 16 == 0xa443 \
            and wd(DS + 28) >> 16 == 0xa440 and wd(DS + 36) >> 16 == 0xa440
        X1, X2, X3 = (s16(wd(DS + k)) for k in (20, 28, 36))
        # result of a between-battle load: lui v1,0x800c; addiu v0,0x1234; j SYSRET; sw v0,S(v1)
        LR = V['HUB_LOADRES']
        assert wd(LR) == lui('v1', 0x800c) and wd(LR + 4) == addiu('v0', 'zero', 0x1234) \
            and wd(LR + 8) == jmp(V['SYSRET']) and wd(LR + 12) >> 16 == 0xac62
        S_LO = s16(wd(LR + 12))
        STAGE_LO = s16(wd(V['HUB_LOOP'] - 0x24))                # lhu v0,<stage>(0x800b) in the SYS 11 branch
        assert wd(V['HUB_LOOP'] - 0x24) >> 16 == 0x9442 and wd(V['HUB_LOOP'] - 0x28) == lui('v0', 0x800b)
        B1 = V['SYS1_BODY']                                     # SYS 1 (battle) branch body
        assert wd(B1) == lui('v0', 0x8008) and wd(B1 + 4) == sh3('v1', V['DRAFT_LO'], 'v0')
        assert any(wd(B1 - 4 * k) == lhu2('t7', 0x248, 'sp') for k in range(0, 200)), 'SYS param slot'
        SS = V['START_SITE']
        assert rd(SS, 8) == struct.pack('<2I', addu('s4', 'zero', 'zero'), lui('v0', 0x800f))
        C5W = V['SYS5_CMP']
        assert wd(C5W) == addiu('v0', 'zero', 5) and wd(C5W + 8) == addiu('v0', 'zero', 0xd) \
            and wd(C5W + 4) >> 16 == 0x1462 and rd(V['SYS5_END'], 8) == struct.pack('<2I', jmp(V['SYSRET']), NOP)
        NOT5 = C5W + 8 + 4 * s16(wd(C5W + 4))                      # target of bne v1,v0 (next sub compare)
        prog = [
            ('label', 'HUBJ'),          # SYS 19 tail (after the post-battle cleanup)
        ] + ([(jal, mailcore), NOPF] if mailcore else []) + [
            (lui, 't0', 0x800d), (lbu, 't1', F51, 't0'), NOPF,
            (sltiu, 't2', 't1', 26), ('bne', 't2', 'zero', 'hid'), (addu, 't3', 't1', 'zero'),
            (srl, 't3', 't1', 1), (addiu, 't3', 't3', 11),                  # F 30/32/34 -> 26/27/28
            ('label', 'hid'),
            (sltiu, 't2', 't3', 29), ('beqz', 't2', 'ret'), NOPF,
            (addiu, 't4', 'zero', 1), (sllv, 't4', 't4', 't3'),
            (lw, 't5', CLR, 't0'), NOPF, (Rr, 't5', 't4', 't9', 0, 0x24),    # t9 = already cleared?
            (or_, 't5', 't5', 't4'), (sw, 't5', CLR, 't0'),                  # cleared
            (jal, PROGF), NOPF,                                              # progressive unlock (if any)
            (lui, 't6', hi(UTAB)), (addiu, 't6', 't6', lo(UTAB)), (sll, 't4', 't3', 2), (addu, 't6', 't6', 't4'),
            (lw, 't4', 0, 't6'), (lw, 't5', UNL, 't0'), NOPF,
            (or_, 't5', 't5', 't4'), (sw, 't5', UNL, 't0'),                  # offline unlocks
            (addiu, 't2', 't1', -22), (sltiu, 't2', 't2', 4), ('bne', 't2', 'zero', 'ret'), NOPF,
            ('beqz', 't5', 'ret'), (addiu, 't2', 'zero', 1),
            (lui, 't6', hi(HUBX)), (sb, 't2', lo(HUBX), 't6'),
            ('label', 'go'),            # what the SYS default path sets for SYS 11, then the main loop
            (lui, 't0', 0x8008), (addiu, 't3', 'zero', 1),
            (sh3, 't3', V['DRAFT_LO'], 't0'), (sh3, 't3', V['UNITMODE_LO'], 't0'), (sh3, 't3', X1, 't0'),
            (sh3, 'zero', X2, 't0'), (sh3, 'zero', X3, 't0'),
            (addiu, 't3', 'zero', 2), (sh3, 't3', M, 't0'),
            ('j', V['HUB_LOOP']), (addiu, SUB, 'zero', 11),
            ('label', 'ret'),
            ('j', V['SYSRET']), NOPF,

            ('label', 'LOADH'),         # a between-battle save was loaded
        ] + ([(jal, mailcore), NOPF] if mailcore else []) + [
            (lui, 't0', 0x800d), (lbu, 't1', F51, 't0'), (lw, 't5', UNL, 't0'),
            (addiu, 't2', 't1', -23), (sltiu, 't2', 't2', 3), ('bne', 't2', 'zero', 'lret'), NOPF,
            ('beqz', 't5', 'lret'), NOPF,
            (lui, 't6', hi(HUBX)), ('beq', 'zero', 'zero', 'go'), (sb, 'zero', lo(HUBX), 't6'),
            ('label', 'lret'),
            (lui, 'v1', 0x800c), (addiu, 'v0', 'zero', 0x1234), ('j', V['SYSRET']), (sw, 'v0', S_LO, 'v1'),

            ('label', 'LISTF'),         # build the select list (vanilla: ids 0..19; hub: unlocked battles)
            (lui, 't0', 0x8008), (lhu2, 't1', M, 't0'), (lui, 'a1', 0x800e),
            (addiu, 'a1', 'a1', LIST_LO), (addiu, 't2', 'zero', 2),
            ('beq', 't1', 't2', 'lh'), (addiu, 't3', 'zero', 0),
            ('label', 'lv'),
            (sll, 't4', 't3', 1), (addu, 't4', 't4', 'a1'), (sh3, 't3', 0, 't4'), (addiu, 't3', 't3', 1),
            (sltiu, 't5', 't3', 20), ('bne', 't5', 'zero', 'lv'), NOPF,
            ('beq', 'zero', 'zero', 'ld'), NOPF,
            ('label', 'lh'),
            (lui, 't6', 0x800d), (lw, 't7', UNL, 't6'), (addiu, 't5', 'zero', 0),
            ('label', 'hl'),
            (srlv, 't4', 't7', 't5'), (andi, 't4', 't4', 1), ('beqz', 't4', 'hn'), (addiu, 't9', 't5', -23),
            (sltiu, 't9', 't9', 3), ('bne', 't9', 'zero', 'hn'), (sll, 't4', 't3', 1),
            (addu, 't4', 't4', 'a1'), (sh3, 't5', 0, 't4'), (addiu, 't3', 't3', 1),
            ('label', 'hn'),
            (addiu, 't5', 't5', 1), (sltiu, 't9', 't5', 29), ('bne', 't9', 'zero', 'hl'), NOPF,
            ('label', 'ld'),
            (lui, 't0', 0x800e), (jr, 'ra'), (sh3, 't3', COUNT_LO, 't0'),

            ('label', 'PREVF'),         # preview loader range: s5 = first MAP number, ENDV = one past the last
            (lui, 't0', 0x8008), (lhu2, 't1', M, 't0'), (addiu, 's5', 'zero', 0x1f),
            ('beqz', 't1', 'ps'), (addiu, 't2', 'zero', 2),
            ('bne', 't1', 't2', 'ps'), (addiu, 's5', 'zero', 0x33),
            (addiu, 's5', 'zero', 1), ('beq', 'zero', 'zero', 'pw'), (addiu, 't3', 'zero', 30),
            ('label', 'ps'),
            (addiu, 't3', 's5', 0x14),
            ('label', 'pw'),
            (lui, 't0', hi(ENDV)), (jr, 'ra'), (sh3, 't3', lo(ENDV), 't0'),

            ('label', 'LABF'),          # label template: hub -> HUBT
            (lui, 't0', 0x8008), (lhu2, 't1', M, 't0'), (lui, 'a2', 0x8001), (addiu, 't2', 'zero', 2),
            ('bne', 't1', 't2', 'lbs'), (addiu, 'a2', 'a2', TPL_LO),
            (lui, 'a2', hi(HUBT)), (jr, 'ra'), (addiu, 'a2', 'a2', lo(HUBT)),
            ('label', 'lbs'),
            (jr, 'ra'), NOPF,

            ('label', 'CONFF'),         # confirm: hub -> F[51]; Map Mode -> id + 50
            (lui, 't0', 0x8008), (lhu2, 't1', M, 't0'), (addiu, 't2', 'zero', 2),
            ('bne', 't1', 't2', 'cm'), NOPF,
            (sltiu, 't3', 's4', 23), ('bne', 't3', 'zero', 'cf'), (addu, 't4', 's4', 'zero'),
            (sll, 't4', 's4', 1), (addiu, 't4', 't4', -22),            # 26/27/28 -> F 30/32/34
            ('label', 'cf'),
            (lui, 't6', hi(HUBX)), (lbu, 't5', lo(HUBX), 't6'), (addiu, 't2', 'zero', 1),
            ('beq', 't5', 't2', 'cx'), (lui, 't6', 0x800c),
            ('bne', 't5', 'zero', 'cw'), (sw, 't4', S_LO, 't6'),       # new game: result = F (script: F[51]=S)
            (addiu, 't5', 'zero', 0x1234),                             # after a load: exact F, result 0x1234
            ('beq', 'zero', 'zero', 'cw'), (sw, 't5', S_LO, 't6'),
            ('label', 'cx'),
            (addiu, 't4', 't4', -1),                                   # after a battle: the script adds 1
            ('label', 'cw'),
            (lui, 't0', 0x800d), (jr, 'ra'), (sb, 't4', F51, 't0'),
            ('label', 'cm'),
            (jr, 'ra'), (addiu, 's4', 's4', 0x32),

            ('label', 'CANCF'),         # triangle: ignored in the hub
            ('beqz', 'v0', 'ki'), (lui, 't0', 0x8008),
            (lhu2, 't1', M, 't0'), (addiu, 't2', 'zero', 2),
            ('beq', 't1', 't2', 'ki'), NOPF,
            ('j', V['CANC_CONT']), NOPF,
            ('label', 'ki'),
            ('j', V['CANC_IGN']), (lui, 'v0', 0x800b),

            ('label', 'HSTART'),        # new game (after the commander is created): start unlocks
            (addiu, 'sp', 'sp', -24), (sw, 'ra', 16, 'sp')]
        if draft_start: prog += [(jal, draft_start), NOPF]
        prog += [
            (lui, 't0', 0x800d), (lui, 't1', init >> 16), (ori, 't1', 't1', init & 0xffff),
            (sw, 't1', UNL, 't0'), (sw, 'zero', CLR, 't0'), (sh3, 'zero', FL + 68, 't0'),
            (sh3, 'zero', FL + 70, 't0'),
            (lw, 'ra', 16, 'sp'), (addiu, 'sp', 'sp', 24),
            (lui, 'v0', 0x800f), (jr, 'ra'), (addu, 's4', 'zero', 'zero')]
        if hub.get('skip_tutorial'):
            prog += [
                ('label', 'SUBCHK'),    # SYS 5 compare: sub 12 = story new game (title script patched) = 5 + hub
                (addiu, 'v0', 'zero', 5), ('bne', 'v1', 'v0', 'c12'), (lui, 't0', hi(HUBX)),
                (sb, 'zero', lo(HUBX), 't0'),                                   # plain SYS 5 (Map Mode, VS)
                ('j', V['SYS5_CMP'] + 12), (addiu, 'v0', 'zero', 0xd),
                ('label', 'c12'),
                (addiu, 'v0', 'zero', 12), ('bne', 'v1', 'v0', 'not5'), (addiu, 't1', 'zero', 2),
                (sb, 't1', lo(HUBX), 't0'),                                     # HUBX 2 = new game pending
                ('j', V['SYS5_CMP'] + 12), (addiu, 'v0', 'zero', 0xd),
                ('label', 'not5'),
                ('j', NOT5), (addiu, 'v0', 'zero', 0xd),
                ('label', 'NEWHUB'),    # end of SYS 5: open the hub if this was the story new game
                (lui, 't0', hi(HUBX)), (lbu, 't1', lo(HUBX), 't0'), (addiu, 't2', 'zero', 2),
                ('beq', 't1', 't2', 'go'), NOPF,
                ('j', V['SYSRET']), NOPF]
        labels, pc = {}, CODE
        for it in prog:
            if it[0] == 'label': labels[it[1]] = pc
            else: pc += 4
        code = asm(CODE, prog)
        assert CODE + 4 * len(code) <= C4E, hex(CODE + 4 * len(code) - C4E)
        wr(C4, d); words(CODE, code)
        # hook sites
        words(SJ, [jmp(labels['HUBJ']), NOP])
        words(LR, [jmp(labels['LOADH']), NOP])
        words(LS, [jal(labels['LISTF']), NOP, jmp(LE), NOP] + [NOP] * 13)
        words(PS, [jal(labels['PREVF']), NOP, NOP, NOP, NOP, NOP])
        words(ES, [lui('v0', hi(ENDV)), lhu2('v0', lo(ENDV), 'v0'), LOOPANDI, ENDBNE])
        words(LB, [jal(labels['LABF']), NOP])
        words(CS, [jal(labels['CONFF'])])
        words(KS, [jmp(labels['CANCF']), andi('v0', 't7', 0x10)])
        words(SS, [jal(labels['HSTART']), NOP])
        if hub.get('skip_tutorial'):
            words(V['SYS5_CMP'], [jmp(labels['SUBCHK']), NOP])
            words(V['SYS5_END'], [jmp(labels['NEWHUB']), NOP])
            # title script, story new game only: SYS(0,5,..) -> SYS(0,12,..) (x6) and F[51] = 0 -> F[51] = S
            rm = bytearray(text_in[V['RESET_MES']])
            tail = b'\x0a\x07\xcf\x30\x03\x04\x1e\x06' + (b'ustart0.mes' if not US else b'start0.mes')
            k = rm.find(tail); assert k > 0 and rm.find(tail, k + 1) < 0
            seg = rm[k - 150:k]; call5 = bytes.fromhex('19300302350302')
            assert seg.count(call5) == 6
            rm[k - 150:k] = seg.replace(call5, bytes.fromhex('193003023c0302'))
            rm[k + 3] = 0x53                                     # value expression: variable S
            text_out[V['RESET_MES']] = bytes(rm)
        # Beaten stages: the select list's text is drawn once into a texture and shown through display-list
        # sprites (8 halfwords: clut, u, v, w, v2, 1, 8, 1); the cursor row is redrawn with clut 0x31d (cyan).
        # Before that, CLRROWS adds the same sprite with another text clut for every visible cleared row.
        HL = V['HUB_HILITE']
        assert wd(HL) == lui('v0', 0x800d) and wd(HL + 4) == lui('v1', 0x800f) and wd(HL + 8) == lui('a2', 0x800f)
        assert wd(HL + 56) == addiu('v0', 'zero', 0x31d) and wd(HL + 40) >> 16 == 0x8c42
        CUR, SCR, IDX, DL = s16(wd(HL + 12)), s16(wd(HL + 16)), s16(wd(HL + 20)), s16(wd(HL + 40))
        CLUT = hub.get('clear_color', 0x31e)
        CR = C5 + len(utab)
        crp = [
            (lui, 't0', 0x8008), (lhu2, 't1', M, 't0'), (addiu, 't2', 'zero', 2),
            ('bne', 't1', 't2', 'out'), NOPF,
            (lui, 't0', 0x800d), (lhu2, 't3', CUR, 't0'), (lw, 't7', CLR, 't0'),
            (lui, 't1', 0x800f), (lhu2, 't4', SCR, 't1'),
            (lui, 't1', 0x800e), (lhu2, 't5', COUNT_LO, 't1'),
            (addiu, 't6', 'zero', 0),
            ('label', 'loop'),
            (addu, 't8', 't4', 't6'), (Rr, 't8', 't5', 't9', 0, 0x2b),          # t9 = idx < count
            ('beqz', 't9', 'out'), NOPF,
            ('beq', 't8', 't3', 'next'), NOPF,
            (lui, 't1', 0x800e), (addiu, 't1', 't1', LIST_LO), (sll, 't9', 't8', 1), (addu, 't1', 't1', 't9'),
            (lhu2, 't9', 0, 't1'), NOPF,
            (srlv, 't9', 't7', 't9'), (andi, 't9', 't9', 1), ('beqz', 't9', 'next'), NOPF,
            (lui, 't1', 0x800f), (lhu2, 't9', IDX, 't1'), (lui, 't2', 0x800e), (lw, 't2', DL, 't2'),
            (sll, 'a0', 't9', 1), (addu, 'a0', 'a0', 't2'), (addiu, 't9', 't9', 8), (sh3, 't9', IDX, 't1'),
            (addiu, 'a1', 'zero', CLUT), (sh3, 'a1', 0, 'a0'),
            (addiu, 'a1', 'zero', 0x28), (sh3, 'a1', 2, 'a0'),
            (sll, 'a1', 't6', 2), (addu, 'a1', 'a1', 't6'), (sll, 'a1', 'a1', 1),
            (addiu, 'a2', 'a1', 0x28), (sh3, 'a2', 4, 'a0'),
            (addiu, 'a2', 'zero', 0x97), (sh3, 'a2', 6, 'a0'),
            (addiu, 'a2', 'a1', 0x31), (sh3, 'a2', 8, 'a0'),
            (addiu, 'a2', 'zero', 1), (sh3, 'a2', 10, 'a0'), (sh3, 'a2', 14, 'a0'),
            (addiu, 'a2', 'zero', 8), (sh3, 'a2', 12, 'a0'),
            ('label', 'next'),
            (addiu, 't6', 't6', 1), (sltiu, 't9', 't6', 10), ('bne', 't9', 'zero', 'loop'), NOPF,
            ('label', 'out'),
            (jr, 'ra'), (lui, 'v0', 0x800d),       # the caller's next instructions expect v0 = 0x800d0000
        ]
        crc = asm(CR, crp)
        assert CR + 4 * len(crc) <= C5END, hex(CR + 4 * len(crc) - C5END)
        words(CR, crc)
        words(HL, [jal(CR)])                          # delay slot = original lui v1,0x800f

    # ---------- 21. Faster disc loading ----------
    # The file reader (CD path) reads 10 sectors at a time into a 20 KB stack buffer: Setloc + CdRead + wait
    # + byte copy per chunk, and every new CdRead makes the drive seek and spin up again, so a 150 KB image
    # takes 2-4 s. FASTRD reads the whole file in 3 requests: the head sectors into the stack buffer, every
    # full sector of the middle straight into the destination (DMA needs a word-aligned address, so it lands
    # 0-3 bytes early and is moved up with a backwards byte copy), the last partial sector into the buffer.
    # Nothing outside [dst, dst + size) is written. Files that fit the 20 KB buffer use the old loop (1 request).
    if opts.get('fast_load'):
        R.update({'s0': 16, 's1': 17, 's2': 18, 's3': 19, 's4': 20, 's5': 21, 's6': 22,
                  't0': 8, 't1': 9, 't2': 10, 't3': 11, 't4': 12, 't5': 13, 't6': 14, 't7': 15, 't8': 24, 't9': 25})
        wd6 = lambda a: struct.unpack_from('<I', rd(a, 4))[0]
        s16_ = lambda x: x - 0x10000 if x & 0x8000 else x
        RDR = V['READER']; CP = RDR + 0x9c; EPI = RDR + 0x148
        assert wd6(CP) == addiu('a0', 'zero', 2) and wd6(EPI) == lw('ra', 0x502c, 'sp')
        assert wd6(RDR + 0xa0) >> 16 == 0x3c02 and wd6(RDR + 0xa4) >> 16 == 0x2454       # lui v0 / addiu s4,v0,LOC
        LOC = ((wd6(RDR + 0xa0) & 0xffff) << 16) + s16_(wd6(RDR + 0xa4) & 0xffff)
        assert wd6(RDR + 0xcc) >> 16 == 0x3c02 and wd6(RDR + 0xd0) >> 16 == 0x8c44       # lui v0 / lw a0,OFF(v0)
        OFF = ((wd6(RDR + 0xcc) & 0xffff) << 16) + s16_(wd6(RDR + 0xd0) & 0xffff)
        assert wd6(RDR + 0xbc) == jal(V['CDREAD']) and wd6(RDR + 0xac) == jal(V['CDCTL']) \
            and wd6(RDR + 0xc4) == jal(V['CDSYNC']) and wd6(RDR + 0x104) == jal(V['POS2INT']) \
            and wd6(RDR + 0x110) == jal(V['INT2POS'])
        hi6 = lambda a: ((a + 0x8000) >> 16) & 0xffff
        sltu_ = lambda rd_, rs, rt: Rr(rs, rt, rd_, 0, 0x2b)
        and_ = lambda rd_, rs, rt: Rr(rs, rt, rd_, 0, 0x24)
        subu_ = lambda rd_, rs, rt: Rr(rs, rt, rd_, 0, 0x23)
        sll_ = lambda rd_, rt, sh: Rr('zero', rt, rd_, sh, 0x00)
        def readsec(first_reg, count, buf):        # IntToPos(first) -> LOC; Setloc; CdRead(count, buf); wait
            return [(addu, 'a0', first_reg, 'zero'), (lui, 'a1', hi6(LOC)), (jal, V['INT2POS']), (addiu, 'a1', 'a1', LOC & 0xffff),
                    (addiu, 'a0', 'zero', 2), (lui, 'a1', hi6(LOC)), (addiu, 'a1', 'a1', LOC & 0xffff),
                    (jal, V['CDCTL']), (addu, 'a2', 'zero', 'zero')] + count + buf + [
                    (jal, V['CDREAD']), (addiu, 'a2', 'zero', 0x80),
                    (jal, V['CDSYNC']), NOPF]
        # Load cache: the file reader skips a file whose bytes are provably still at the destination: 8 entries
        # (dst, CdlLOC word, r << 20 | size, checksum of the loaded bytes) written after every 1-request read;
        # before reading, an entry with the same dst/position/size whose checksum still matches = skip.
        # Fights reuse the same sprite buffers (0x80160000...), so a monster that fights again is not reloaded.
        C8 = V['CAVE8']
        LCTAB = C8
        def lcsum(lab):   # v0 = rolling checksum of a1 bytes at a0 (clobbers t0, t1, a0, a1)
            return [(addu, 'v0', 'zero', 'zero'), ('beqz', 'a1', lab + 'e'), NOPF,
                    ('label', lab), (lbu, 't0', 0, 'a0'), (sll_, 't1', 'v0', 5), (srl, 'v0', 'v0', 27),
                    (Rr, 'v0', 't1', 'v0', 0, 0x25), (addu, 'v0', 'v0', 't0'), (addiu, 'a1', 'a1', -1),
                    ('bne', 'a1', 'zero', lab), (addiu, 'a0', 'a0', 1), ('label', lab + 'e')]
        lcprog = [
            ('label', 'CHK'),                     # a0 dst, a1 size, a2 r -> v0 = 1 if still loaded
            (sll_, 't9', 'a2', 20), (Rr, 'a1', 't9', 't9', 0, 0x25),
            (lui, 't8', hi6(LOC)), (lw, 't8', LOC & 0xffff, 't8'),
            (lui, 't2', hi6(LCTAB)), (addiu, 't2', 't2', LCTAB & 0xffff), (addiu, 't3', 't2', 128),
            ('label', 'cl'),
            (lw, 't4', 0, 't2'), (lw, 't5', 4, 't2'), (lw, 't6', 8, 't2'),
            ('bne', 't4', 'a0', 'cn'), NOPF, ('bne', 't5', 't8', 'cn'), NOPF, ('bne', 't6', 't9', 'cn'), NOPF,
            (lw, 't7', 12, 't2'), (addu, 't3', 'ra', 'zero')] + lcsum('cs') + [
            (Rr, 'v0', 't7', 'v0', 0, 0x26), (jr, 't3'), (sltiu, 'v0', 'v0', 1),          # v0 = (sum == stored)
            ('label', 'cn'),
            (addiu, 't2', 't2', 16), ('bne', 't2', 't3', 'cl'), NOPF,
            (jr, 'ra'), (addu, 'v0', 'zero', 'zero'),
            ('label', 'STO'),                     # a0 dst, a1 size, a2 r: remember what was just loaded
            (sll_, 't9', 'a2', 20), (Rr, 't9', 'a1', 't9', 0, 0x25),
            (lui, 't8', hi6(LOC)), (lw, 't8', LOC & 0xffff, 't8'),
            (lui, 't2', hi6(LCTAB)), (addiu, 't2', 't2', LCTAB & 0xffff), (addiu, 't3', 't2', 128),
            ('label', 'sl'),                      # an entry for this dst, else the round-robin slot
            (lw, 't4', 0, 't2'), NOPF, ('beq', 't4', 'a0', 'sf'), NOPF,
            (addiu, 't2', 't2', 16), ('bne', 't2', 't3', 'sl'), NOPF,
            (srl, 't4', 'a0', 9), (andi, 't4', 't4', 0x70),                        # else slot by dst bits 13-15
            (addiu, 't2', 't3', -128), (addu, 't2', 't2', 't4'),
            ('label', 'sf'),
            (sw, 'a0', 0, 't2'), (sw, 't8', 4, 't2'), (sw, 't9', 8, 't2'),
            (addu, 't3', 'ra', 'zero')] + lcsum('ss') + [
            (jr, 't3'), (sw, 'v0', 12, 't2'),
        ]
        lab8, pc8 = {}, C8 + 128
        for it in lcprog:
            if it[0] == 'label': lab8[it[1]] = pc8
            else: pc8 += 4
        assert pc8 <= V['CAVE8_END'], hex(pc8 - V['CAVE8_END'])
        LCCHK, LCSTO = lab8['CHK'], lab8['STO']
        def copy(src, dst_, n, lab):              # byte copy n (reg) bytes, forwards; clobbers t0, v0, v1
            return [(addu, 't0', 'zero', 'zero'), ('beq', n, 'zero', lab + 'e'), NOPF,
                    ('label', lab), (addu, 'v0', src, 't0'), (lbu, 'v1', 0, 'v0'), (addu, 'v0', dst_, 't0'),
                    (addiu, 't0', 't0', 1), ('bne', 't0', n, lab), (sb, 'v1', 0, 'v0'), ('label', lab + 'e')]
        prog = [
            (lui, 't0', hi6(OFF)), (lw, 's3', OFF & 0xffff, 't0'), NOPF,           # s3 = r (byte offset in sector)
            (addu, 't1', 's3', 's1'), (sltiu, 't0', 't1', 0x5001),                   # r + size fits 10 sectors:
            ('bne', 't0', 'zero', 'old'), NOPF,                                      # the old loop reads it at once
            (lui, 't0', 0x8010), (sltu_, 't0', 's2', 't0'), ('bne', 't0', 'zero', 'old'), NOPF,   # dst in the heap
            (addu, 't1', 's2', 's1'), (addiu, 't1', 't1', 0x1000), (sltu_, 't0', 't1', 'sp'),
            ('beqz', 't0', 'old'), NOPF,                                             # and well below the stack
            (sw, 's3', 0x5008, 'sp'),                                                # keep r for LCSTO
            (addu, 'a0', 's2', 'zero'), (addu, 'a1', 's1', 'zero'),
            (jal, LCCHK), (addu, 'a2', 's3', 'zero'),                                # same file still there?
            ('bne', 'v0', 'zero', 'hit'), NOPF,
            (subu_, 's4', 's2', 's3'), (andi, 's6', 's4', 3), (subu_, 's4', 's4', 's6'),   # s4 = base, s6 = d
            (addu, 't1', 's3', 's1'), (addiu, 't1', 't1', 0x7ff), (srl, 's5', 't1', 11),  # s5 = sectors
            (addu, 's0', 's2', 's1'),                                                # s0 = end of the file data
            (sll_, 't1', 's5', 11), (addu, 't1', 's4', 't1'), (subu_, 's3', 't1', 's0'),   # s3 = bytes after end
            (subu_, 't2', 's2', 's4'), (sw, 't2', 0x500c, 'sp'),                     # bytes before dst
            ] + copy('s4', 'a3', 't2', 'c1')[:0] + [
            (addiu, 'a3', 'sp', 0x10)] + copy('s4', 'a3', 't2', 'c1') + [           # save [base, dst)
            (lw, 't2', 0x500c, 'sp'), (addiu, 'a3', 'sp', 0x1010)] + copy('s0', 'a3', 's3', 'c2') + [   # save tail
            (addiu, 'a0', 'zero', 2), (lui, 'a1', hi6(LOC)), (addiu, 'a1', 'a1', LOC & 0xffff),
            (jal, V['CDCTL']), (addu, 'a2', 'zero', 'zero'),
            (addu, 'a0', 's5', 'zero'), (addu, 'a1', 's4', 'zero'),
            (jal, V['CDREAD']), (addiu, 'a2', 'zero', 0x80),
            (jal, V['CDSYNC']), NOPF,
            # data landed at dst - d: move it up by d, backwards
            ('beqz', 's6', 'nomv'), (addu, 't3', 's1', 'zero'),
            (subu_, 't1', 's2', 's6'),
            ('label', 'mv'),
            (addiu, 't3', 't3', -1), (addu, 'v0', 't1', 't3'), (lbu, 'v1', 0, 'v0'), (addu, 'v0', 's2', 't3'),
            ('bne', 't3', 'zero', 'mv'), (sb, 'v1', 0, 'v0'),
            ('label', 'nomv'),
            (lw, 't2', 0x500c, 'sp'), (addiu, 'a3', 'sp', 0x10)] + copy('a3', 's4', 't2', 'c3') + [   # restore
            (addiu, 'a3', 'sp', 0x1010)] + copy('a3', 's0', 's3', 'c4') + [
            (lw, 'a2', 0x5008, 'sp'), (addu, 'a0', 's2', 'zero'), (addu, 'a1', 's1', 'zero'),
            (jal, LCSTO), NOPF,
            ('label', 'hit'),
            ('j', EPI), NOPF,
            ('label', 'old'),
            ('j', CP + 4), (addiu, 'a0', 'zero', 2),
        ]
        C6 = V['CAVE6']
        assert wd6(C6) == addiu('sp', 'sp', -0x28), hex(wd6(C6))
        code6 = asm(C6, prog)
        assert C6 + 4 * len(code6) <= V['CAVE6_END'], hex(C6 + 4 * len(code6) - V['CAVE6_END'])
        C6FREE = C6 + 4 * len(code6)
        words(C6, code6)
        wr(C8, bytes(128)); words(C8 + 128, asm(C8 + 128, lcprog))
        words(CP, [(2 << 26) | ((C6 >> 2) & 0x3ffffff)])      # delay slot = the original lui v0 (harmless)
        # After every movie the player waits 60 x VSync(2) (2 s) after stopping the stream and another 2 s after
        # clearing the screen: 4 s of black after each movie, also when one is skipped. 4 x VSync(2) each.
        for a in V['MOVIEWAIT']:
            assert wd6(a) == addiu('s1', 'zero', 0x3c) and wd6(a + 4) >> 26 == 3 and wd6(a + 8) == addiu('a0', 'zero', 2)
            words(a, [addiu('s1', 'zero', 4)])
        # Memory card: every save is a 3-block file (0x6000 bytes) but only the 0x200 header + 0x4000 data are
        # used; the reader (boot preload of all 7 slots, save/load screens) reads 0x4200 instead of 0x6000.
        SR = V['SAVEREAD']
        assert wd6(SR) == addiu('s2', 'zero', 0x6000) and wd6(SR + 0x14) == addiu('s1', 's3', 0x6000)
        words(SR, [addiu('s2', 'zero', 0x4200)])

        # Boot (SYS 1234): the game reads all 7 save slots from the memory card (0x6000 bytes each, at the card's
        # real speed: ~40 s in DuckStation with a few saves) but only uses slot 0 there (it restores it as the
        # current state when valid). BOOTRD reads slot 0 only and marks the other cached slots invalid (0xff,
        # bad checksum); the save and load screens still read every slot themselves.
        RA = V['READALL']
        assert wd6(RA + 0x5c) >> 16 == 0x8e63 and wd6(RA + 0x18) == lui('s3', 0x8008)   # lw v1,BUF(s3)
        BUFHI, BUFLO = 0x8008, wd6(RA + 0x5c) & 0xffff
        assert wd6(V['BOOTREAD']) == jal(RA) and wd6(V['BOOTREAD'] - 0x2c) == jal(V['CARDTEST'])
        assert wd6(RA + 0x34) == jal(V['CARDTEST']) and wd6(RA + 0x78) == jal(V['CARDEXISTS']) \
            and wd6(RA + 0x8c) == jal(V['READSLOT'])
        C7 = V['CAVE7']
        assert wd6(C7) == addiu('sp', 'sp', -0x18), hex(wd6(C7))
        bprog = [
            (addiu, 'sp', 'sp', -0x20), (sw, 'ra', 0x18, 'sp'), (sw, 's0', 0x14, 'sp'),
            # every cached slot: 0xff (= invalid)
            (lui, 't0', BUFHI), (lw, 't1', BUFLO, 't0'), (lui, 't2', 2), (addu, 't1', 't1', 't2'),
            (lui, 't3', 2), (ori, 't3', 't3', 0xc000), (addiu, 't4', 'zero', 0xff),          # 7 x 0x4000
            ('label', 'ff'),
            (addiu, 't3', 't3', -1), (sb, 't4', 0, 't1'), ('bne', 't3', 'zero', 'ff'), (addiu, 't1', 't1', 1),
            (jal, V['CARDTEST']), NOPF,
            ('bne', 'v0', 'zero', 'out'), (addiu, 's0', 'zero', 1),
            (addu, 's0', 'zero', 'zero'),
            (jal, V['CARDEXISTS']), (addu, 'a0', 'zero', 'zero'),
            ('bne', 'v0', 'zero', 'out'), NOPF,
            (lui, 't0', BUFHI), (lw, 'a1', BUFLO, 't0'), (addu, 'a0', 'zero', 'zero'),
            (jal, V['READSLOT']), (addiu, 'a2', 'zero', 0x4000),
            ('bne', 'v0', 'zero', 'out'), NOPF,
            # checksum: sum of bytes 0..0x3fdf == halfword at 0x3fee
            (lui, 't0', BUFHI), (lw, 't1', BUFLO, 't0'), (addu, 't2', 'zero', 'zero'), (addu, 't3', 'zero', 'zero'),
            (addiu, 't4', 'zero', 0x3fe0),
            ('label', 'cs'),
            (addu, 'v0', 't1', 't3'), (lbu, 'v0', 0, 'v0'), (addiu, 't3', 't3', 1), (addu, 't2', 't2', 'v0'),
            ('bne', 't3', 't4', 'cs'), NOPF,
            (lbu, 'v0', 0x3fef, 't1'), (lbu, 'v1', 0x3fee, 't1'), (sll_, 'v0', 'v0', 8), (Rr, 'v1', 'v0', 'v1', 0, 0x25),
            (andi, 't2', 't2', 0xffff), ('bne', 't2', 'v1', 'out'), NOPF,
            # copy to cached slot 0
            (lui, 't2', 2), (addu, 't2', 't1', 't2'), (addiu, 't3', 'zero', 0x4000),
            ('label', 'cp'),
            (lbu, 'v0', 0, 't1'), (addiu, 't3', 't3', -1), (sb, 'v0', 0, 't2'), (addiu, 't1', 't1', 1),
            ('bne', 't3', 'zero', 'cp'), (addiu, 't2', 't2', 1),
            ('label', 'out'),
            (addu, 'v0', 's0', 'zero'),
            (lw, 'ra', 0x18, 'sp'), (lw, 's0', 0x14, 'sp'), (jr, 'ra'), (addiu, 'sp', 'sp', 0x20),
        ]
        code7 = asm(C7, bprog)
        assert C7 + 4 * len(code7) <= V['CAVE7_END'], hex(C7 + 4 * len(code7) - V['CAVE7_END'])
        words(C7, code7)
        words(V['BOOTREAD'], [jal(C7)])
        # Save / load screens: readall tests the card (libcard info + events) before every one of the 7 slots,
        # then once more at the end. Test once: the loop jumps back past the test. The 0xff fill used a0 = slot
        # base; it now uses s1 directly so the jump target can be the 'a1 = 0' that the first pass also runs.
        bne_ = lambda s, t, frm, to: (5 << 26) | (R[s] << 21) | (R[t] << 16) | (((to - frm - 4) >> 2) & 0xffff)
        assert wd6(RA + 0x4c) == 0x02202021 and wd6(RA + 0x58) == 0x00851021          # move a0,s1 / addu v0,a0,a1
        assert wd6(RA + 0x114) == bne_('s2', 'v0', RA + 0x114, RA + 0x34)
        words(RA + 0x4c, [0x00002821])                                                  # move a1,zero
        words(RA + 0x58, [0x02251021])                                                  # addu v0,s1,a1
        words(RA + 0x114, [bne_('s2', 'v0', RA + 0x114, RA + 0x4c)])

    # ---------- 23. Game speed ----------
    # The battle-map loop and the two other main game loops end each frame with VSync(2): the game logic runs at
    # 30 Hz (cursor, unit movement, phase banners, menus). SPEEDV waits 1 or 2 vblanks following an 8-frame
    # pattern: 'fast' = 1,1,2,1,1,2,1,2 (11 vblanks / 8 frames, ~1.45x), 'faster' = all 1 (2x). Frames that
    # need longer than one vblank simply take longer, as before.
    if opts.get('game_speed'):
        R.update({'t0': 8, 't1': 9, 't2': 10})
        pat = {'fast': [1, 1, 2, 1, 1, 2, 1, 2], 'faster': [1] * 8}[opts['game_speed']]
        wd8 = lambda a: struct.unpack_from('<I', rd(a, 4))[0]
        C7S = V['CAVE7'] + 0x100
        assert wd8(V['CAVE7']) == addiu('sp', 'sp', -0x18) or opts.get('fast_load')
        if opts.get('fast_load'): assert C7S >= C7 + 4 * len(code7), 'CAVE7 overlap'
        VSYNC = None
        for a in V['LOOPVSYNC']:
            assert wd8(a) >> 26 == 3 and wd8(a + 4) == addiu('a0', 'zero', 2), hex(a)
            t = (wd8(a) & 0x3ffffff) << 2 | 0x80000000
            assert VSYNC in (None, t); VSYNC = t
        CNT = C7S; PAT = C7S + 4; SPD = C7S + 12
        hi8 = lambda x: ((x + 0x8000) >> 16) & 0xffff
        spd = asm(SPD, [
            (lui, 't0', hi8(CNT)), (lbu, 't1', CNT & 0xffff, 't0'), NOPF,
            (addiu, 't1', 't1', 1), (andi, 't1', 't1', 7), (sb, 't1', CNT & 0xffff, 't0'),
            (addiu, 't2', 't0', PAT & 0xffff), (addu, 't2', 't2', 't1'), (lbu, 'a0', 0, 't2'),
            ('j', VSYNC), NOPF])
        assert SPD + 4 * len(spd) <= V['CAVE7_END']
        wr(CNT, bytes(4) + bytes(pat)); words(SPD, spd)
        for a in V['LOOPVSYNC']: words(a, [jal(SPD), NOP])
        # Pad auto-repeat in the map loop (right after its VSync): a new press waits 10 frames before
        # repeating, then repeats every 2. Faster frames made that first delay short enough that a normal
        # press on a save slot also answered the "Overwrite?" prompt (cursor on No). Scale the first delay
        # back to the same real time; the repeat rate stays fast.
        L0, hits = V['LOOPVSYNC'][0], []
        for k in range(0x80, 0xb0, 4):
            w0, w2 = wd8(L0 + k), wd8(L0 + k + 8)
            if w0 >> 21 == 0x9 << 5 and w0 & 0xffff == 0xa and w2 & 0xffe0ffff == 0xa7a00280 \
                    and (w0 >> 16) & 31 == (w2 >> 16) & 31 and wd8(L0 + k + 4) >> 26 == 2:
                hits.append(L0 + k)
        assert len(hits) == 1, hits
        words(hits[0], [(wd8(hits[0]) & 0xffff0000) | {'fast': 15, 'faster': 20}[opts['game_speed']]])
        # "Overwrite?" prompt (cursor on No): it reads the held confirm button guarded by the input lock
        # (US 0x800ae65c != 5), but choosing the save slot never sets that lock. The prompt's first frames
        # used to be slow enough for the press to end; at 2x a normal press answered No. Entering the prompt
        # now sets the lock, so it needs a new press (or the auto-repeat delay).
        assert wd8(L0 + 0x20) >> 16 == 0x3c02 and wd8(L0 + 0x24) >> 16 == 0xa440, hex(wd8(L0 + 0x20))
        AE_HI, AE_LO = wd8(L0 + 0x20) & 0xffff, wd8(L0 + 0x24) & 0xffff      # lui v0,HI / sh zero,LO(v0)
        ent = []
        for k in range(off(0x80020000), len(exe) - 32, 4):
            if struct.unpack_from('<I', exe, k + 28)[0] != addiu('v0', 'zero', 0x5f): continue
            w = struct.unpack_from('<8I', exe, k)
            if w[0] == lui('v1', 0x8008) and w[1] == addiu('v0', 'zero', 3) and w[2] >> 16 == 0xa462 \
                    and w[3] == lui('v0', 0x800d) and w[4] & 0xffe0ffff == 0x24000001 and w[6] >> 26 == 2 \
                    and w[5] >> 16 == 0xa440 | ((w[4] >> 16) & 31):
                ent.append(k - 0x800 + BASE)
        assert len(ent) == 1, ent
        T = (wd8(ent[0] + 24) & 0x3ffffff) << 2 | 0x80000000            # lui t8,HI / j EXIT / sh v0,LO(t8)
        rT = (wd8(T) >> 16) & 31
        assert wd8(T) >> 21 == 0x1e0 and wd8(T + 4) >> 26 == 2 \
            and wd8(T + 8) >> 16 == 0xa402 | (rT << 5), hex(T)
        PROMPT = V['CAVE7'] + 0x180
        words(PROMPT, [wd8(T), wd8(T + 8), lui('v1', AE_HI), addiu('v0', 'zero', 5), wd8(T + 4),
                       I(0x29, 'v1', 'v0', AE_LO)])
        assert PROMPT + 24 <= V['CAVE7_END']
        words(ent[0] + 24, [(2 << 26) | ((PROMPT >> 2) & 0x3ffffff)])

    # ---------- 24. No battle music (opts battle_music=False) ----------
    # Every fight swaps the map BGM for the battle BGM (3 files: VH, VB, SEQ, ~130 KB) and back afterwards,
    # and every phase change swaps player/enemy phase music the same way. Off: the combat start no longer
    # selects a track, and the map-music selector (phase changes, after fights, stage start) only starts a
    # track when none is playing: one track per stage, no music loads during the battle. Story scripts still
    # change the music themselves (they call PlayBGM directly).
    if opts.get('battle_music') is False:
        R.update({'t0': 8, 't1': 9})
        wd9 = lambda a: struct.unpack_from('<I', rd(a, 4))[0]
        PB = V['PLAYBGM']
        assert wd9(V['BGM_COMBAT']) >> 26 == 3 and wd9(V['BGM_COMBAT'] + 4) == addiu('a0', 'zero', 2)
        assert wd9(V['BGM_SELECT']) == jal(PB)
        assert wd9(PB + 0x10) >> 16 == 0x3c13 and wd9(PB + 0x14) >> 16 == 0x8663       # lui s3 / lh v1,CUR(s3)
        CURHI, CURLO = wd9(PB + 0x10) & 0xffff, wd9(PB + 0x14) & 0xffff
        SB = V['CAVE7'] + 0x140
        if opts.get('game_speed'): assert SB >= SPD + 4 * len(spd)
        sbc = asm(SB, [
            (lui, 't0', CURHI), (lambda rt, o, rs: I(0x21, rs, rt, o), 't1', CURLO, 't0'),
            (addiu, 't0', 'zero', -1), ('bne', 't1', 't0', 'same'), NOPF,
            ('j', PB), NOPF,
            ('label', 'same'),
            (jr, 'ra'), NOPF])
        assert SB + 4 * len(sbc) <= V['CAVE7'] + 0x180      # prompt lock (step 23) lives at +0x180
        words(SB, sbc)
        words(V['BGM_COMBAT'], [NOP])
        words(V['BGM_SELECT'], [jal(SB)])

    # ---------- 25. Faster map build (with fast_load) ----------
    # Entering a battle map or the post-battle unit screen draws the whole map into a RAM bitmap from 8x8 tiles
    # (four copies of the loop: plain / flipped). The per-pixel loop is 15 instructions (base pointer reloaded,
    # 16-bit counter sign extension); ~50 frames of CPU per map. Same 22-word block rewritten as a 7-instruction
    # pixel loop (row source pointer computed once per row, end-pointer compare). Same pixels, same registers out.
    if opts.get('fast_load'):
        R.update({'t0': 8, 't1': 9, 't2': 10, 't3': 11, 't4': 12, 't6': 14})
        sig = struct.pack('<3I', andi('v0', 'v0', 0xffff), addu('v1', 'v1', 'v0'), lbu('v0', 0, 'v1'))
        blocks, i = [], exe.find(sig)
        while i >= 0:
            a = i - 0x800 + BASE - 12
            w = lambda k: struct.unpack_from('<I', rd(a + 4 * k, 4))[0]
            TO = w(2) & 0xffff                          # tile base pointer offset (US 0xb8, PAL 0x968)
            ds, rs = w(15) & 0xffff, w(21) & 0xffff
            ds, rs = (ds - 0x10000 if ds & 0x8000 else ds), (rs - 0x10000 if rs & 0x8000 else rs)
            orig = [addu('t1', 'zero', 'zero'), addu('v0', 't2', 'zero'), lw('v1', TO, 't6'),
                    andi('v0', 'v0', 0xffff), addu('v1', 'v1', 'v0'), lbu('v0', 0, 'v1'), 0,
                    I(4, 'v0', 'zero', 2), addiu('t2', 't2', 1), sb('v0', 0, 't0'), addiu('v0', 't1', 1),
                    addu('t1', 'v0', 'zero'), sll('v0', 'v0', 16), Rr('zero', 'v0', 'v0', 16, 3),
                    I(5, 'v0', 't4', -14), addiu('t0', 't0', ds), addiu('v0', 't3', 1), addu('t3', 'v0', 'zero'),
                    sll('v0', 'v0', 16), Rr('zero', 'v0', 'v0', 16, 3), I(5, 'v0', 't4', -21), addiu('t0', 't0', rs)]
            if [w(k) for k in range(22)] != orig:      # another loop with the same load sequence
                i = exe.find(sig, i + 4)
                continue
            new = asm(a, [
                ('label', 'row'),
                (lw, 'v1', TO, 't6'), (andi, 'v0', 't2', 0xffff), (addu, 'v1', 'v1', 'v0'),
                (addiu, 't1', 'v1', 8), (addiu, 't2', 't2', 8),
                ('label', 'px'),
                (lbu, 'v0', 0, 'v1'), (addiu, 'v1', 'v1', 1), ('beqz', 'v0', 'skip'), (addiu, 't0', 't0', ds),
                (sb, 'v0', -ds, 't0'),
                ('label', 'skip'),
                ('bne', 'v1', 't1', 'px'), NOPF,
                (addiu, 't3', 't3', 1), ('bne', 't3', 't4', 'row'), (addiu, 't0', 't0', rs)])
            words(a, new + [NOP] * (22 - len(new)))
            blocks.append(a)
            i = exe.find(sig, i + 4)
        assert len(blocks) == 4, [hex(b) for b in blocks]
        # The same map build clears a 0xC00-byte strip buffer (fixed at 0x80140000) a byte at a time, 6
        # instructions per byte, ~140 times per map: clear it a word at a time instead.
        orig = [andi('v0', 'a2', 0xffff), None, addiu('a2', 'a2', 1), addu('v1', 'v1', 'v0'),
                andi('v0', 'a2', 0xffff), None, sb('zero', 0, 'v1')]
        i, done = 0, False
        while not done:
            i = exe.find(struct.pack('<I', orig[0]), i + 4)
            assert i >= 0, 'strip clear loop not found'
            a = i - 0x800 + BASE
            ws = [struct.unpack_from('<I', rd(a + 4 * k, 4))[0] for k in range(7)]
            if all(o is None or o == x for o, x in zip(orig, ws)) and ws[1] >> 16 == 0x8d03 \
                    and ws[5] == I(5, 'v0', 'a3', -5) & 0xffffffff and ws[-1] == orig[-1]:
                assert struct.unpack_from('<I', rd(a - 0x24, 4))[0] == addiu('a3', 'zero', 0xc00)
                words(a, [ws[1], addiu('a2', 'zero', 0xc00), addu('v0', 'v1', 'a2'), addiu('v1', 'v1', 4),
                          I(5, 'v1', 'v0', -2), sw('zero', -4, 'v1'), NOP])
                done = True

    # ---------- 14. (v12) Localization fixes ----------
    # Spell tiers: the base spell had no number and "Lv1" was the second tier. Now Lv1..Lv4 (Heal),
    # Lv1..Lv3 (Revive, Charge). Names live in 20-byte slots (16 chars space-padded + 4 NULs).
    def rename_slot(old, new, count=1):
        o16, n16 = old.ljust(16).encode(), new.ljust(16).encode()
        assert len(n16) == 16
        hits = [m.start() for m in re.finditer(re.escape(b'\x00' + o16 + b'\x00'), bytes(exe))]
        assert len(hits) == count, (old, hits)
        for h in hits: exe[h + 1:h + 17] = n16
    for base, top in (('Heal', 3), ('Revive', 2), ('Charge', 2)):
        for k in range(top, 0, -1):
            rename_slot('%s_Lv%d' % (base, k), '%s_Lv%d' % (base, k + 1))
        rename_slot(base, base + '_Lv1')
    # Attack names cut off / garbled when romanized from katakana (user checked a JP let's play for Korish)
    rename_slot('Korish', 'Colichemarde')         # Shadow Master, Shade (コリシュマルド)
    rename_slot('Barudisshu', 'Bardiche')         # Destroyer, Monk, Greater Demon (バルディッシュ)
    rename_slot('Corseska', 'Corsesca')           # Angel Warrior, Pixie Lord, Wyvern (コルセスカ)
    rename_slot('Timu', 'Charmy')                 # Blessed Angel (チャーミー; Cherub's チャーム = Charm)
    rename_slot('Sheikluma', 'Schweitzer')        # Archangel (シュヴァイツァー; JP name ミカエル, ranged Holy Plasma)


    # ---------- 6. MONST.TBL edits ----------
    mt = bytearray(monst_in)
    lines = mt.split(b'\r\n')
    def edit(mid, pairs_):
        for i, ln in enumerate(lines):
            s = ln.decode('cp932')
            head = s.split(',')[0].strip()
            if head.isdigit() and int(head) == mid and s.count('"') >= 2:
                for old, new in pairs_:
                    assert len(old) == len(new) and s.count(old) == 1, (mid, old, s)
                    s = s.replace(old, new)
                nb = s.encode('cp932'); assert len(nb) == len(ln)
                lines[i] = nb; return
        raise KeyError(mid)
    # Goblin line: chaotic; Orc evolves at 8, Overlord at 25
    edit(127, [('",01,N,', '",01,C,')])
    edit(128, [('",01,N,', '",08,C,')])
    edit(129, [('",01,N,', '",25,C,')])
    # Slime: small buff (keeps its 99% physical reduction and kill reward)
    edit(134, [('008ｰ012/01ｰ02', '018ｰ022/01ｰ03'), ('001ｰ003/01ｰ02', '004ｰ006/01ｰ02'),
               ('134ｰ03ｰ001 02', '134ｰ03ｰ004 02')])
    # Commander buffs (Justice unchanged)
    if opts['commander_buffs']:
        edit(137, [('101ｰ116/02ｰ16', '115ｰ130/03ｰ16'), ('023ｰ027/01ｰ04', '028ｰ032/01ｰ04'),
                   ('30/30/30/20/30', '30/30/30/40/30'), ('137ｰ03ｰ012 02', '137ｰ03ｰ015 02')])
        edit(138, [('061ｰ075/01ｰ07', '085ｰ099/02ｰ10'), ('002ｰ003/01ｰ02', '012ｰ015/01ｰ03'),
                   ('30/10/10/10/60', '30/10/10/30/60'), (',05W,', ',06W,')])
        edit(0, [('081ｰ090/01ｰ13', '100ｰ110/02ｰ13'), ('009ｰ009/01ｰ01', '015ｰ018/01ｰ02'),
                 ('60/10/10/20/10', '60/10/10/40/10')])
        edit(1, [('091ｰ104/01ｰ16', '105ｰ118/02ｰ16'), ('005ｰ005/01ｰ01', '012ｰ015/01ｰ02'),
                 ('10/60/10/20/10', '10/60/10/40/10')])
        edit(2, [('086ｰ093/01ｰ09', '100ｰ108/02ｰ11'), ('017ｰ019/01ｰ03', '020ｰ023/01ｰ03'),
                 ('10/10/60/10/30', '10/10/60/30/30')])
    # (v12) Demon -> Imp: chain reads Gremlin > Imp > Lesser Demon > Greater Demon > Necron
    edit(39, [('"Demon           "', '"Imp             "')])
    # (rando) names misread from katakana (developers' own labels in MEN_TBL): ペリュトン, セイレーン
    edit(121, [('"Unisus          "', '"Peryton         "')])
    edit(119, [('"Syrian          "', '"Siren           "')])
    nm = b'\r\n'.join(lines)
    assert len(nm) == len(mt)

    # ---------- 15. (v12) Text files (full-width Shift-JIS). Sizes must not change. ----------
    FW = {chr(c): chr(c + 0xfee0) for c in range(0x21, 0x7f)}; FW[' '] = '\u3000'
    def fw(x): return ''.join(FW.get(ch, ch) for ch in x)
    def fix_size(lines, orig_len, prefer):
        """Pad/trim trailing full-width spaces so the encoded file has orig_len bytes (2 bytes each)."""
        cur = len('\r\n'.join(lines).encode('cp932')); diff = (orig_len - cur)
        assert diff % 2 == 0, diff
        n = diff // 2
        order = prefer + [i for i in range(len(lines)) if i not in prefer]
        for i in order:
            if n == 0: break
            if n > 0 and lines[i].strip() and len(lines[i]) < 34:
                add = min(n, 34 - len(lines[i])); lines[i] += '\u3000' * add; n -= add
            elif n < 0:
                t = len(lines[i]) - len(lines[i].rstrip('\u3000')); cut = min(-n, t)
                if cut: lines[i] = lines[i][:len(lines[i]) - cut]; n += cut
        assert n == 0, 'no room: %d' % n
        return lines
    def text_edit(name, subs):
        raw = text_in[name]; t = raw.decode('cp932')
        lines = t.split('\r\n'); touched = []
        for sub in subs:
            old, new = sub[0], sub[1]; want = sub[2] if len(sub) > 2 else 1
            o, nw = fw(old), fw(new)
            hit = [i for i, l in enumerate(lines) if o in l]
            assert len(hit) == want and all(lines[i].count(o) == 1 for i in hit), (name, old, hit)
            for i in hit: lines[i] = lines[i].replace(o, nw); touched.append(i)
        lines = fix_size(lines, len(raw), touched)
        out = '\r\n'.join(lines).encode('cp932'); assert len(out) == len(raw)
        text_out[name] = out
    # Spell descriptions: tier names, and "all friendly units" -> "all allies" (matches "one ally"; frees space)
    text_edit('MAHOU.TXT', [
        ('【Heal Lv. 3】', '【Heal Lv. 4】'), ('【Heal Lv. 2】', '【Heal Lv. 3】'), ('【Heal Lv. 1】', '【Heal Lv. 2】'),
        ('【Heal】', '【Heal Lv. 1】'),
        ('【Revive Lv. 2】', '【Revive Lv. 3】'), ('【Revive Lv. 1】', '【Revive Lv. 2】'), ('【Revive】', '【Revive Lv. 1】'),
        ('【Charge Lv. 2】', '【Charge Lv. 3】'), ('【Charge Lv. 1】', '【Charge Lv. 2】'), ('【Charge】', '【Charge Lv. 1】'),
        ('to all friendly units.', 'to all allies.', 4),   # 3x Revive + Charge All
    ])
    # Tutorial: the PAL menu button reads CALL but its tutorial says PLACE (left over from the US script, where
    # the button really is PLACE). Only PAL needs the fix.
    if not US:
        text_edit('TUTORI.TXT', [('PLACE:', 'CALL:'), ('the PLACE command', 'the CALL command', 2)])
    # Encyclopedia: Demon -> Imp
    text_edit('UNTIKU.TBL', [('【Demon】', '【Imp】'), ('【Unisus】', '【Peryton】'), ('【Syrian】', '【Siren】'),
                             ('The Syrians', 'The Sirens')])
    # ---------- 26. Proofread text (opts text_fixes). Story scripts are rewritten in core.generate. ----------
    if opts.get('text_fixes'):
        from . import textfix
        TX = textfix.load()
        def cur(n): return text_out.get(n, text_in[n])
        text_out['TUTORI.TXT'] = textfix.tutorial(cur('TUTORI.TXT'), TX['tutorial'], pal=not US)
        item_names = {}
        text_out['UNTIKU.TBL'] = textfix.entries(cur('UNTIKU.TBL'), TX['encyclopedia'], names=TX['monsters'], pad=36)
        text_out['MAHOU.TXT'] = textfix.entries(cur('MAHOU.TXT'), TX['spells'], block=4)
        # item names: the exe holds the menu names; ITEM.TXT's 【headers】 follow them
        it = cur('ITEM.TXT').decode('cp932')
        for old, new in TX['messages']:
            for m in re.finditer(r'☆№(\d+)【%s[\u3000]*】' % re.escape(textfix.fw(old)), it): item_names[m.group(1)] = new
        text_out['ITEM.TXT'] = textfix.entries(cur('ITEM.TXT'), TX['items'], names=item_names, block=4)
        nm = textfix.monst_names(nm, TX['monsters'])
        # exe: messages (old -> new) and the monster name table (32-byte slots, by id)
        exe[:] = textfix.exe_names(bytes(exe), TX['messages'])
        e8, nasc = textfix.exe_ascii_names(bytes(exe), TX['messages'])
        exe[:] = e8; assert nasc == 8, nasc            # the four Arm items, two tables each
        e8 = bytes(exe); w0 = textfix.fw('Warlock').encode('cp932') + b'\x81\x40' * 8 + b'\x00\x00'
        assert e8.count(w0) == 1; MT0 = e8.index(w0)
        assert e8[MT0 + 32:MT0 + 32 + 22] == textfix.fw('Necromancer').encode('cp932')
        for mid, new in TX['monsters'].items():
            a = MT0 + 32 * int(mid); n = textfix.fw(new).encode('cp932')
            assert e8[a + 30:a + 32] == b'\x00\x00' and len(n) <= 30, (mid, new)
            exe[a:a + 30] = n + b'\x81\x40' * ((30 - len(n)) // 2)

    # ---------- 22. Tutorials: one disc read instead of two (with fast_load) ----------
    # Every Raphael/Defender tutorial loads FACE.B8 (the 2688-byte portrait, 48 MB into BIND.DAT) and then
    # TUTORI.TXT (8 MB in): two long seeks, ~2 s of freeze. The portrait is packed into TUTORI.TXT instead: its
    # long "-----" separator lines (comments for the writers) shrink to "--" (the reader only needs "--" as
    # the entry end) and FACE.B8 goes at the end, 4-byte aligned; the loader reads TUTORI.TXT once and
    # converts the portrait from there.
    if opts.get('fast_load'):
        R.update({'v0': 2, 'a0': 4, 'a1': 5, 'a2': 6, 'a3': 7})
        face = face_in
        tut = text_out.get('TUTORI.TXT', text_in['TUTORI.TXT'])
        lines = tut.split(b'\r\n')
        lines = [b'--' if l.startswith(b'---') else l for l in lines]
        body = b'\r\n'.join(lines)
        FO = (len(tut) - len(face)) & ~3
        assert len(body) + 1 <= FO, 'TUTORI.TXT: no room for the portrait'
        packed = body + b'\x1a' * (FO - len(body)) + face
        packed += b'\x1a' * (len(tut) - len(packed))
        assert len(packed) == len(tut) and packed[FO:FO + len(face)] == face
        text_out['TUTORI.TXT'] = packed
        e8 = bytes(exe)
        k = e8.find(b'FACE.B8\x00TUTORI.TXT\x00'); assert k > 0
        FSTR = k - 0x800 + BASE; TSTR = FSTR + 8
        wd7 = lambda a: struct.unpack_from('<I', rd(a, 4))[0]
        hits = [a for a in range(BASE, BASE + len(e8) - 0x800, 4) if wd7(a) == addiu('a0', 'a0', FSTR & 0xffff)]
        assert len(hits) == 1; TF = hits[0] - 8                        # function start (addiu sp,sp,-0x28)
        assert wd7(TF) == addiu('sp', 'sp', -0x28) and wd7(TF + 4) == lui('a0', 0x8001)
        LOADF = (wd7(TF + 0x10) & 0x3ffffff) << 2 | 0x80000000; CONV = (wd7(TF + 0x3c) & 0x3ffffff) << 2 | 0x80000000
        assert wd7(TF + 0x10) >> 26 == 3 and wd7(TF + 0x3c) >> 26 == 3 and wd7(TF + 0x4c) == jal(LOADF)
        assert wd7(TF + 0x48) == addiu('a0', 'a0', TSTR & 0xffff) and wd7(TF + 0x60) == NOP
        args = [wd7(TF + o) for o in (0x18, 0x1c, 0x20, 0x24)]            # a0=x, a1=0, v0=w, sw v0,0x10
        tail = [wd7(TF + o) for o in (0x30, 0x34, 0x38, 0x40)]            # v0=h, move a2, a3=, sw v0,0x18 (delay)
        assert wd7(TF + 0x28) == lui('v0', 0x8018) and wd7(TF + 0x2c) == sw('v0', 0x14, 'sp')
        words(TF + 4, [
            lui('a0', 0x8001), addiu('a0', 'a0', TSTR & 0xffff), sw('ra', 0x20, 'sp'),
            jal(LOADF), lui('a1', 0x8018)] + args + [
            lui('v0', 0x8018), ori('v0', 'v0', FO), sw('v0', 0x14, 'sp')] + tail[:3] + [
            jal(CONV), tail[3],
            lw('ra', 0x20, 'sp'), NOP, jr('ra'), addiu('sp', 'sp', 0x28), NOP])
        assert TF + 4 + 4 * 23 <= TF + 0x64

    return bytes(exe), nm, text_out

