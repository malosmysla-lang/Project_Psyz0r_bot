"""Apply our test-only hook to a separate minqlx checkout, never the live build."""
import argparse
from pathlib import Path
import shutil
p=argparse.ArgumentParser();p.add_argument('checkout',type=Path);a=p.parse_args()
root=Path(__file__).resolve().parents[1];hooks=a.checkout/'hooks.c'
s=hooks.read_text()
if '#include "psyz_control_lab.h"' not in s:
 old='void* qagame_dllentry;'; assert s.count(old)==1
 s=s.replace(old,old+'\n#include "psyz_control_lab.h"')
 old='G_RunFrame = *(G_RunFrame_ptr*)(vm_call_table + RELOFFSET_VM_CALL_RUNFRAME);';assert s.count(old)==1
 s=s.replace(old,old+'\n    Psyz_Install();')
 hooks.write_text(s)
shutil.copyfile(root/'adapter/native/psyz_control_lab.h',a.checkout/'psyz_control_lab.h')
print('Prepared separate checkout. Build with make -B nopy; verify pinned binary hashes before running.')
