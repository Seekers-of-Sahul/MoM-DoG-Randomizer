# Master of Monsters: Disciples of Gaia — Rebalance & Randomizer

A rebalance mod, speed-up patch, proofread English script and randomizer for the PlayStation
strategy game *Master of Monsters: Disciples of Gaia* (US SLUS-00595 and European SLES-00244, English).

**Web patcher:** open the GitHub Pages site of this repository (`https://<user>.github.io/<repo>/`),
choose your Track 1 `.bin`, pick options, download the patched file. Everything runs in your browser
(Python via Pyodide); the disc image is never uploaded.

You need your own copy of the game as a bin/cue rip. Nothing from the game is included here.

## Using the patched file

- Patch the **Track 1 `.bin`** of a bin/cue rip (not MDF/MDS, not CHD).
  Known clean dumps: US `9e453ec3d3c20302e271eca5f272bcb7`, PAL `6fa52600f97e551313acceb96ce27d99`.
- Keep the audio tracks: point the first `FILE` line of your `.cue` at the new `.bin` (or rename the new file
  to the original Track 1 name). Without the audio tracks the game freezes after the intro video.
- PAL disc: the changes apply to the English language only.
- Same disc + same seed + same options = same game. Every patch writes a spoiler log (`.json`).

## What's in it

### Always included (rebalance)
- **Real random numbers.** The original "random" routine returned a counter that went up by 1 per call;
  hits, status effects, level-ups, tower rewards and fusions are now actually random.
- **Level cap 99** (no level-100 crash; a full bar at 99 still gives the stat gains).
- **Swappable equipment:** equipping a unit that already holds an item swaps them; the old item goes back
  to your inventory.
- **Stacking tower items:** a tower item you already have adds its charges to your copy (max 99).
- **Experience carry-over** past a level-up, **magic attack scaling** with level (like physical attacks).
- **Evolutions:** Goblin → Orc (8) → Overlord (25), Wolfwere → Werewolf (11); the Goblin line is Chaotic.
  Slime is a little sturdier. Stage 5 gets Lizardman as its 8th summon.
- Localization fixes from earlier versions (spell tiers Lv.1–Lv.4, Imp, Peryton, Siren, attack names).

### Options
| Option | Default | |
|---|---|---|
| Combat experience | on | every fight gives 8 + (enemy level − own level) exp; reaching 100 levels up without a kill |
| Stronger disciples | on | HP, defence and agility buffs for the five disciples other than Justice |
| Proofread English text | on | rewritten story, tutorials, encyclopedia, item and spell text; corrected monster and item names (e.g. Necron → Lucifer, Strong Arm → Strong Gloves) |
| Summon lists | rebalance | rebalance lists (every human base unit summonable early), original, or randomized (each slot keeps its movement type and a similar level) |
| Faster loading | on (web) | one disc request per file, a small load cache, quick memory card check at boot, faster map drawing, no 4 s black screen after videos |
| Game speed | faster (web) | normal, fast (~1.5×) or faster (2×): the game logic runs every frame instead of every other frame |
| Battle music | on | off keeps the map music during fights, so nothing has to load and battles start much faster |
| Hardcore | off | no saving during battles |
| Difficulty lock | off | Game Lev. fixed to Normal or Hard |
| Stage hub | off | after every battle pick the next stage on the Map Mode screen: progressive, open, or shuffled order |
| Skip tutorial | off | with the hub: a new game goes straight to the hub |
| Archipelago mailbox | off | with the hub: monsters a client puts in the mailbox join your army between battles |
| Draft mode | off | roguelike: no summoning, 3 starting monsters, new monsters offered after each battle, army limit grows by 3 per battle |

## Command line

Python 3.8+, no extra packages:

```
python -m momrando "Track 1.bin" --seed myseed --fast-load --game-speed faster --ppf my.ppf
python -m momrando --help
```

Writes `<input>_rando_<seed>.bin`, a spoiler log, and optionally a PPF patch.
Command-line defaults are the original game's: speed options are off unless you pass them.

---
Not affiliated with ASCII, Toshiba EMI or SystemSoft.
