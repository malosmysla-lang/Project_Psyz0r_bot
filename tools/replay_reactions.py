"""Replay offline C++ decisions through the existing chat; sends nothing to QL."""
import argparse
import json
from pathlib import Path
import random
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime.chat import ChatPolicy

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('journal', type=Path)
    parser.add_argument('--output', type=Path, default=Path('out/reaction_chat.jsonl'))
    parser.add_argument('--force-chat-for-test', action='store_true')
    args = parser.parse_args()
    if args.output.resolve() == args.journal.resolve():
        parser.error('Output must differ from input')
    policy = ChatPolicy(rng=random.Random(1))
    if args.force_chat_for_test:
        policy.config['gauntlet_reply_probability'] = 1
    policy.start('offline-review', 'Human', 123, 0)
    policy.pending.clear()  # focus on event messages, not opening
    records = [json.loads(line) for line in args.journal.read_text(encoding='utf-8').splitlines()]
    output = []
    for index, record in enumerate(records):
        policy.decision_record(index, record['time'], record)
        text = policy.tick(record['time'], record['time'])
        output.append(dict(time=record['time'], decision=record, chat=text,
                           game_command_sent=False, force_chat_for_test=args.force_chat_for_test))
    if records:
        now = records[-1]['time'] + policy.config['cooldown']
        output.append(dict(time=now, chat=policy.tick(now, now), game_command_sent=False))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in output), encoding='utf-8')
    args.output.with_suffix('.diagnostics.json').write_text(json.dumps(policy.diagnostics, ensure_ascii=False, indent=2), encoding='utf-8')
    print(args.output)

if __name__ == '__main__':
    main()
