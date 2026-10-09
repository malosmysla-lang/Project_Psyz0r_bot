import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from runtime.chat import ChatPolicy

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / 'out/msvc-x64/Debug/psyz0r_sandbox.exe'

@unittest.skipUnless(EXE.exists(), 'Build the C++ sandbox first')
class ConfigTests(unittest.TestCase):
    def run_config(self, text):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'core.ini'
            log = Path(directory) / 'trace.jsonl'
            config.write_text(text, encoding='ascii')
            result = subprocess.run([str(EXE), str(log), str(config)], capture_output=True, text=True)
            entries = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            return result, entries

    def test_live_configuration_and_forfeit_trace(self):
        result, entries = self.run_config((ROOT / 'config/core.ini').read_text())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(entries[0]['reason'], 'damage_estimate_push')
        self.assertEqual([entry['mood'] for entry in entries[1:]], ['surrender_tilt', 'surrender_tilt'])
        self.assertTrue(all(not entry['collect_resources'] for entry in entries[1:]))
        self.assertTrue(all(not entry['game_command_sent'] for entry in entries))

    def test_unknown_duplicate_and_probability_rejected(self):
        for text in ('surrender_probability 1.1\n', 'unknown 1\n',
                     'surrender_probability 0.1\nsurrender_probability 0.2\n',
                     'surrender_duration -1\n'):
            with self.subTest(text=text):
                result, _ = self.run_config(text)
                self.assertNotEqual(result.returncode, 0)

    def test_custom_push_threshold(self):
        result, entries = self.run_config('aggressive_push_damage 95\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(entries[0]['reason'], 'controlled_hold')

    def test_cpp_decision_feeds_chat(self):
        result, entries = self.run_config('')
        self.assertEqual(result.returncode, 0, result.stderr)
        chat = ChatPolicy()
        chat.start('integration', 'Human', 123, 0)
        chat.tick(0, 0)
        chat.decision_record('cpp-2', 20, entries[1])
        self.assertIsNotNone(chat.tick(20, 20))
        chat.decision_record('cpp-3', 40, entries[2])
        self.assertIsNone(chat.tick(40, 40))
