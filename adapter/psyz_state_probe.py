"""Read-only own-slot probe for an isolated minqlx test server.

Not a movement adapter. Runtime compatibility has not been verified.
Requires qlx_psyzTestInstance=1, qlx_psyzProbeSlot=<target slot>.
Writes only the selected slot's state through the plugin logger.
"""
import json
import time
import os
from pathlib import Path
import minqlx

class psyz_state_probe(minqlx.Plugin):
    def __init__(self):
        super().__init__()
        self.last_sample = 0.0
        self.sequence = 0
        home = self.get_cvar('fs_homepath')
        self.output = Path(home) / 'psyz_probe.json' if home else None
        self.add_hook('frame', self.sample)
        minqlx.console_print('PSYZ_PROBE_LOADED: read-only own slot probe')

    def sample(self):
        if self.get_cvar('qlx_psyzTestInstance') != '1':
            return
        configured = self.get_cvar('qlx_psyzProbeSlot')
        if configured is None:
            return
        try:
            slot = int(configured)
            max_clients = int(self.get_cvar('sv_maxclients'))
        except (TypeError, ValueError):
            return
        if not 0 <= slot < max_clients:
            return
        now = time.monotonic()
        if now - self.last_sample < 0.1:
            return
        self.last_sample = now
        info = minqlx.player_info(slot)
        if info is None or info.connection_state != minqlx.CS_ACTIVE:
            if self.output:
                self.write_record({'status': 'waiting_for_active_target', 'slot': slot,
                                   'own_state_verified': False, 'command_sent': False})
            return
        state = minqlx.player_state(slot)
        if state is None:
            return
        self.sequence += 1
        record = {
            'seq': self.sequence, 'monotonic_seconds': now, 'slot': slot,
            'name': info.name, 'connection_state': info.connection_state,
            'own_state_verified': True,
            'health': state.health, 'armor': state.armor,
            'position': list(state.position), 'velocity': list(state.velocity),
            'weapon': state.weapon, 'ammo': list(state.ammo),
            'alive': state.is_alive, 'view_angles': None,
            'view_angles_status': 'not exposed in inspected PlayerState API',
            'command_sent': False,
        }
        self.write_record(record)

    def write_record(self, record):
        if self.output:
            temporary = self.output.with_suffix('.tmp')
            temporary.write_text(json.dumps(record), encoding='utf-8')
            os.replace(temporary, self.output)
