"""Reproduce 0.8.7 from a supplied stage; never deploy or rewrite the primary."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

STAGE = Path(__file__).resolve().parent
BUILD = Path('/home/qlserver/psyz0r-bot/build-087-20261021')
if not BUILD.exists():
    shutil.copytree('/home/qlserver/psyz0r-bot/build-085-20261020', BUILD)
for header in (STAGE / 'adapter/native').glob('*.h'):
    shutil.copy2(header, BUILD / header.name)
(BUILD / 'hooks.c').touch()
env = dict(os.environ, PATH='/home/qlserver/psyz0r-bot/toolchain-bin:/usr/bin:/bin')
with (STAGE / 'build087.log').open('w') as log:
    subprocess.run(['make', 'all'], cwd=BUILD, env=env, stdout=log, stderr=log, check=True)
for name in ['finish087_tests', 'finish087_bridge_tests', 'prealpha_native_tests',
             'nav_recovery_tests', 'lg_style_tests', 'combo_policy_tests',
             'item_arrival_tests', 'compact_policy_tests']:
    binary = STAGE / name
    subprocess.run(['g++', '-std=c++17', str(STAGE / 'tests' / (name + '.cpp')), '-o', str(binary), '-lm'], check=True)
    subprocess.run([str(binary)], check=True)
subprocess.run(['gcc', '-I' + str(BUILD), str(STAGE / 'tests/hook_pool_reload_test.c'), '-o', str(STAGE / 'hook_pool_reload_test')], check=True)
subprocess.run([str(STAGE / 'hook_pool_reload_test')], check=True)
print('BUILD087_AND_9_GROUPS_PASSED', hashlib.sha256((BUILD / 'bin/minqlx.x64.so').read_bytes()).hexdigest())
