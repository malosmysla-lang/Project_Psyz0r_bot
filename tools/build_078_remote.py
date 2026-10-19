"""Build only, safe while owner is playing; no live file replacement here."""
import json,os,shutil,subprocess
from pathlib import Path
STAGE=Path(__file__).resolve().parent
BUILD=Path('/home/qlserver/psyz0r-bot/build-078-20261019')
def main():
    if not BUILD.exists():shutil.copytree('/home/qlserver/psyz0r-bot/build-076-20261019',BUILD)
    for p in (STAGE/'adapter/native').glob('*.h'):shutil.copy2(p,BUILD/p.name)
    (BUILD/'hooks.c').touch()
    env=os.environ.copy();env['PATH']='/home/qlserver/psyz0r-bot/toolchain-bin:/usr/bin:/bin'
    with (STAGE/'build.log').open('w') as log:
        subprocess.run(['make','all'],cwd=BUILD,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    for name in ['prealpha_native_tests','nav_recovery_tests','lg_style_tests','combo_policy_tests','item_arrival_tests']:
        binary=STAGE/name
        subprocess.run(['g++','-std=c++17',str(STAGE/'tests'/(name+'.cpp')),'-o',str(binary),'-lm'],check=True)
        with (STAGE/(name+'.log')).open('w') as log:subprocess.run([str(binary)],stdout=log,stderr=log,check=True)
    subprocess.run(['python3',str(STAGE/'prepare_profile_078_remote.py')],check=True)
    print('LINUX_BUILD_AND_5_TESTS_PASSED')
if __name__=='__main__':main()
