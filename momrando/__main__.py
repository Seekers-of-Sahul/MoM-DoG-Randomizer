"""python -m momrando "Track 1.bin" [options]   (see --help)"""
import argparse, json, os, random, sys
from .core import generate
from .disc import make_ppf

def main(argv=None):
    p = argparse.ArgumentParser(prog='momrando', description=
        'Master of Monsters: Disciples of Gaia (PS1) rebalance + randomizer. '
        'Takes the Track 1 .bin of the US (SLUS-00595) or PAL (SLES-00244) disc.')
    p.add_argument('input', help='original Track 1 .bin (MODE2/2352)')
    p.add_argument('-o', '--output', help='patched .bin to write (default: <input>_rando_<seed>.bin)')
    p.add_argument('--ppf', help='also write a PPF patch here')
    p.add_argument('--seed', help='seed (any text); random if omitted')
    g = p.add_argument_group('rebalance')
    g.add_argument('--no-combat-exp', action='store_true', help='exp only from kills (vanilla)')
    g.add_argument('--no-commander-buffs', action='store_true', help='vanilla stats for the five non-Justice disciples')
    g.add_argument('--no-text-fixes', action='store_true', help='keep the original English text (no proofread '
                   'story, tutorial, item, spell and encyclopedia text, no monster/item renames)')
    g = p.add_argument_group('speed')
    g.add_argument('--fast-load', action='store_true', help='shorter loading (one disc request per file, load '
                   'cache, quick memory card check at boot, faster map drawing)')
    g.add_argument('--game-speed', choices=['fast', 'faster'], help='game logic at ~1.45x or 2x')
    g.add_argument('--no-battle-music', action='store_true', help='keep the map music in fights (no music '
                   'loads, so battles start faster)')
    g = p.add_argument_group('randomizer')
    g.add_argument('--summons', choices=['vanilla', 'mod', 'shuffle'], default='vanilla',
                   help="player summon lists: vanilla, the rebalance mod's early lists, or shuffled")
    g.add_argument('--hardcore', action='store_true', help='no saving during battles (save between them only)')
    g.add_argument('--lock-difficulty', choices=['normal', 'hard'], help='lock Game Lev. to this setting')
    g.add_argument('--hub', choices=['progressive', 'open', 'shuffled'],
                   help='stage select (Map Mode screen) after every battle and on loading. progressive: story '
                        'order, 2 open, every first clear opens the next; open: all stages; shuffled: random '
                        'order loosely following the story')
    g.add_argument('--skip-tutorial', action='store_true', help='with --hub: new game goes straight to the hub')
    g.add_argument('--mailbox', action='store_true', help='with --hub: Archipelago mailbox (the BizHawk client '
                   'delivers received monsters between battles)')
    g = p.add_argument_group('draft mode (roguelike: summoning disabled, monsters drafted after each battle)')
    g.add_argument('--draft', action='store_true', help='enable draft mode')
    g.add_argument('--draft-size', type=int, default=6, help='monsters offered after each battle (max 6)')
    g.add_argument('--roster-step', type=int, default=3, help='roster limit grows by this per battle (cap 29)')
    g.add_argument('--start', help='comma-separated starting monsters (default: 3 random)')
    a = p.parse_args(argv)

    seed = a.seed if a.seed is not None else str(random.randrange(10 ** 9))
    opts = dict(combat_exp=not a.no_combat_exp, commander_buffs=not a.no_commander_buffs,
                summons=a.summons, hardcore=a.hardcore, lock_difficulty=a.lock_difficulty,
                text_fixes=not a.no_text_fixes, fast_load=a.fast_load, game_speed=a.game_speed,
                battle_music=not a.no_battle_music)
    if a.hub:
        opts['hub'] = dict(mode=a.hub, skip_tutorial=a.skip_tutorial)
    if a.mailbox:
        assert a.hub, '--mailbox needs --hub'
        opts['mailbox'] = True
    if a.draft:
        assert 1 <= a.draft_size <= 6, '--draft-size must be 1-6'
        opts['draft'] = dict(size=a.draft_size, step=a.roster_step, start=a.start.split(',') if a.start else None)
    src = open(a.input, 'rb').read()
    out, d, spoiler = generate(src, opts, seed)
    if not d.known_dump:
        print('warning: input is not a known clean dump (MD5 %s); patching anyway' % d.md5, file=sys.stderr)
    base = os.path.splitext(a.input)[0]
    dst = a.output or '%s_rando_%s.bin' % (base, seed)
    open(dst, 'wb').write(out)
    if a.ppf:
        open(a.ppf, 'wb').write(make_ppf(src, out, 'MoM DoG rando %s %s' % (d.version, seed)))
    log = os.path.splitext(dst)[0] + '_spoiler.json'
    spoiler['options'] = opts
    json.dump(spoiler, open(log, 'w'), indent=1, ensure_ascii=False)
    print('%s disc, seed %s -> %s (spoiler log %s)' % (d.version, seed, dst, log))

if __name__ == '__main__':
    main()
