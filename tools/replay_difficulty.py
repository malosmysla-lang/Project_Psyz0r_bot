"""Synthetic, offline demonstration of the existing chat/session integration."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.chat import ChatPolicy
from runtime.difficulty import DuelResult


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('out/difficulty_trace.jsonl'))
    args = parser.parse_args()
    # Keep demonstration artifacts under out, never overwrite code/config/demos.
    out_root = Path(__file__).resolve().parents[1] / 'out'
    target = args.output.resolve()
    if out_root.resolve() not in target.parents:
        parser.error('Output must be inside the project out directory')
    p = ChatPolicy()
    p.start('synthetic-1', 'Human', 'demo-human', 0, map_id='bloodrun')
    p.tick(0, 0)
    r = DuelResult('synthetic-1', 'demo-human', 'bloodrun', 5, 20, 600, 40, verified=True)
    p.end(600, 'human_win', summary=r)
    message = p.tick(600, 600)
    before = p.difficulty.level('demo-human')
    p.opponent_chat('synthetic-chat-1', 601, sender_steam_id='demo-human', text='gg')
    gg_accepted = p.difficulty.pending['accepted']
    p.opponent_chat('synthetic-chat-2', 602, sender_steam_id='demo-human', text='да')
    after_consent = p.difficulty.level('demo-human')
    p.start('synthetic-2', 'Human', 'demo-human', 610, map_id='sinister')
    record = dict(source='synthetic_test', game_command_sent=False,
                  question=message, level_at_final=before, gg_accepted=gg_accepted,
                  level_after_consent=after_consent,
                  level_next_map=p.difficulty.level('demo-human'))
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = [record] + [dict(source='synthetic_test', game_command_sent=False, **row)
                       for row in p.difficulty.journal]
    target.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows), encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
