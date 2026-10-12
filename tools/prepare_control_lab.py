"""Apply our test-only hook to a separate minqlx checkout, never the live build."""
import argparse
from pathlib import Path
import shutil
import hashlib
p=argparse.ArgumentParser();p.add_argument('checkout',type=Path);p.add_argument('--qagame',type=Path,required=True);a=p.parse_args()
expected='091d568f46a280afbf2deda4a5ba4c8bd5e02ed6d070ef56300b1f47c5f729be'
if hashlib.sha256(a.qagame.read_bytes()).hexdigest()!=expected:
    p.error('qagame SHA256 mismatch; refusing to prepare hooks')
root=Path(__file__).resolve().parents[1];hooks=a.checkout/'hooks.c'
s=hooks.read_text()
if '#include "psyz_control_lab.h"' not in s:
 old='void* qagame_dllentry;'; assert s.count(old)==1
 s=s.replace(old,old+'\n#include "psyz_control_lab.h"')
 old='G_RunFrame = *(G_RunFrame_ptr*)(vm_call_table + RELOFFSET_VM_CALL_RUNFRAME);';assert s.count(old)==1
 s=s.replace(old,old+'\n    Psyz_Install();')
 hooks.write_text(s)
shutil.copyfile(root/'adapter/native/psyz_control_lab.h',a.checkout/'psyz_control_lab.h')
shutil.copyfile(root/'adapter/native/psyz_stock_goal_observer.h',a.checkout/'psyz_stock_goal_observer.h')
shutil.copyfile(root/'adapter/native/psyz_prealpha.h',a.checkout/'psyz_prealpha.h')
shutil.copyfile(root/'adapter/native/psyz_bloodrun_bank.h',a.checkout/'psyz_bloodrun_bank.h')
shutil.copyfile(root/'adapter/native/psyz_opening.h',a.checkout/'psyz_opening.h')
shutil.copyfile(root/'adapter/native/psyz_opening_bank.h',a.checkout/'psyz_opening_bank.h')
shutil.copyfile(root/'adapter/native/psyz_nav_recovery.h',a.checkout/'psyz_nav_recovery.h')
shutil.copyfile(root/'adapter/native/psyz_red_routes.h',a.checkout/'psyz_red_routes.h')
shutil.copyfile(root/'adapter/native/psyz_loadout.h',a.checkout/'psyz_loadout.h')
print('Prepared separate checkout. Build with make -B nopy; verify pinned binary hashes before running.')
