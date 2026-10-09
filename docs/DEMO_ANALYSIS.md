# Demo analysis — initial pass

## Completed parser pass — 2026-10-09

The previously missing parser is now available: official UDT 1.3.1 Windows x64 console package in `tools/udt/`, with source URL and observed SHA-256 in `tools/udt/PROVENANCE.md`. No compiler installation was needed. Run `python tools/analyze_demos.py --export` to repeat the export and tables.

- 170/170 demos produced syntactically valid JSON files with game states.
- 164 exported match-stat records are Duel; six demos have no match-stat records. Missing stats do not establish corruption or lack of effort.
- 387 player-stat rows exported. Stats include scores, weapon damage/accuracy and item pickup totals where present.
- All original demo SHA-256 values matched before/after the repeat export. Hash manifest: `analysis/demos/source_hashes.json`.
- Outputs: `analysis/demos/json/`, `matches.csv`, `players.csv`, `summary.json`, `export.log`.
- No demos excluded or labelled low effort. Successful export is a useful protocol check, not proof of complete event coverage.

Both PsyRoZ matches are 600,000 ms according to UDT:

| Demo | Result |
|---|---|
| `nekitz0r(POV)-vs-[D+B]PsyRoZ-bloodrun-2026_09_28-00_56_50.dm_91` | PsyRoZ 20, nekitz0r 3 |
| `nekitz0r(POV)-vs-[D+B]PsyRoZ-sinister-2026_09_28-01_08_19.dm_91` | PsyRoZ 19, nekitz0r 7 |

Bloodrun item totals: PsyRoZ 14 red armor, 15 yellow armor, 10 mega; nekitz0r 2 red armor, 18 yellow armor, 4 mega. PsyRoZ damage: lightning 1,782, rail 1,520, rocket 934. These totals motivate reviewing control of red armor/mega and lightning engagements; they do not establish routes, exact pickup timings or why a weapon was selected.

All five exported filenames containing C-RRREX have match stats. The earlier outer-framing concern remains unconfirmed; no demo was rejected for it.

Initial candidates for manual review of close games (score gap <=3, reported duration >=9 minutes): `nekitz0r(POV)-vs-@gZ@r-sinisterblue-2026_10_05-19_49_39.dm_91` (3:2), `nekitz0r(POV)-vs-ALekseych-aerowalk-2026_09_27-18_06_23.dm_91` (6:5), and `nekitz0r(POV)-vs-i_H4K2-bloodrunintel-2026_08_18-03_29_22.dm_91` (10:8). This is a review queue, not a final training selection. Bot-labelled opponents and human-labelled opponents need separate interpretation; filenames alone do not prove player type.

Next: review events in the two PsyRoZ matches and close-game candidates with timestamps; obtain snapshot-level position/item/weapon data or use client playback for movement and decision rules. The JSON exporter used here supplies game states, match stats, deaths and chat, not a ready movement-training dataset. Confirm the integration interface before constructing the C++ game controller.

The handoff below records the earlier stage. Its statements that no parser is available and only this report has been created are superseded by this section and `PROJECT_STATE.md`.

## Handoff for the next session

The project is at the research/prototype-planning stage. The user wants to continue in Codex; start by reading this file and the existing `botfiles/`, `bots/`, and `demos/` folders. Do not treat the preliminary scan below as a completed demo review.

### Bot concept

Build a strong, entertaining Quake Live practice opponent in C++/MSVC, subject to confirming how it can be connected to the game. Do not add a standalone AI model: derive explicit rules, scenarios, and behavior styles from demos and user-specified combat decisions.

Desired behaviors include:

- Learn map routes, spawns, trick jumps/rocket jumps, and item timings.
- Prioritize Mega over armor in the opening; become stricter and count Yellow Armor against strong opponents.
- Select weapons by range, position, and combat situation; exact rules are still to be provided.
- React to score and opponent behavior: play more aggressively in close games or while behind; sometimes relax when comfortably ahead; very rarely tilt and throw away a large lead.
- Adapt to opponent habits, including finishing corpses and pulling out the saw; use the saw more often at low health when appropriate.
- Track items without wallhack. Decide what pickup information is legitimately observable and do not grant hidden information.
- Connect behavioral state to the existing chat, which the user says is nearly ready.

### Project materials already inspected

- `botfiles/` and `zzz_bots.pk3`: legacy Quake III bot configuration/source-like weight and chat data; not a ready Quake Live C++ bot or a buildable project.
- `bots/`: seven Workshop sets. `botextension/`, `KETNAR/`, `bot-xaero-instagibbot/`, and `napoleon/` include bot profile/config files; `q3clan/`, `TAproskins/`, and `z-missing_models/` are primarily models, skins, and other assets.
- `demos/`: 170 `.dm_91` files, 146 named as nekitz0r POV recordings, including two versus `[D+B]PsyRoZ`.
- No original demo, bot, or Workshop files have been modified. The only project file added for this work is this report.

### Immediate next work

1. Obtain or build a parser that correctly supports `.dm_91` (UDT is the current candidate).
2. Batch-export demo metadata and verify parsing before making any match-quality exclusions.
3. Identify low-effort matches from match score/playback evidence, not file size alone; preserve originals.
4. Inspect useful POV matches for movement, item control/timings, weapon choices, and score/opponent reactions; record observations with demo filename and timestamps.
5. Confirm target deployment (local/private server vs another setup) before choosing the bot integration/build architecture.

## Scope

- Source folder: `demos/`
- Files found: 170 Quake Live demos (`.dm_91`)
- POV recordings named `nekitz0r(POV)`: 146
- POV recordings against `[D+B]PsyRoZ`: 2
- One recording against `C-RRREX` did not pass a simple outer-message framing scan. This is not enough to call the demo corrupt; it needs to be checked with a protocol-aware reader.

## What has and has not been established

The initial scan counted raw demo message frames and file sizes. Among the 146 nekitz0r POV demos, 113 had at least 20,000 frames, 16 had 10,000–19,999, and 17 had fewer than 10,000. These are only rough length indicators: frame counts and file size do not show the score, match quality, or whether either player stopped trying.

No demos have been excluded. In particular, no match has been classified as a low-effort or one-sided game based on file size alone. The final shortlist must be based on the actual match score and playback/events.

## Parser research

- The older `qldemo-python` project describes its summary tool as reading `dm_73`; it should not be assumed to correctly parse this `dm_91` collection.
- [Uber Demo Tools (UDT)](https://github.com/mightycow/uberdemotools) documents read/write support for Quake Live `dm_91` and provides a JSON-export command-line tool. This is the best candidate found so far for extracting map, players, game mode, scores, and other demo metadata.
- The UDT source can be built with Visual C++, but a C++ compiler/build tools are not currently available in this environment. Its documented Windows binary links could not be reached from here.
- Quake Live's public Bethesda page points players to Steam; the open browser page is not a playable Quake Live session. Browser research can help find tools and protocol documentation, but it cannot replace reading these local demo files or watching them in the game client.

## Next analysis step

Obtain a working UDT `UDT_json`/console binary (or build UDT with Visual C++), run it locally against the demos, and use the exported match metadata to shortlist actual one-sided games. Then inspect the remaining nekitz0r POV demos for movement, item timing/control, weapon choices, engagements, and reactions to score changes. Keep original demo files unchanged.
