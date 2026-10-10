"""Read-only UDT 1.3.1 x64 custom-parser snapshot export for one dm_91 demo.

Separate offline analysis dependency; never exposes demo omniscience to the bot.
ABI descriptors mirror public packed API fields, not UDT's parser implementation.
"""
import argparse
import ctypes as c
import hashlib
import json
import math
from pathlib import Path
import struct

I, U, F, P = c.c_int32, c.c_uint32, c.c_float, c.c_void_p

class Packed(c.Structure):
    _pack_ = 1

class PlayerPrefix(Packed):
    _fields_ = [(n, I) for n in ('commandTime', 'pm_type', 'bobCycle', 'pm_flags', 'pm_time')]
    _fields_ += [('origin', F * 3), ('velocity', F * 3)]
    _fields_ += [(n, I) for n in ('weaponTime', 'gravity', 'speed')]
    _fields_ += [('delta_angles', I * 3)]
    _fields_ += [(n, I) for n in ('groundEntityNum', 'legsTimer', 'legsAnim', 'torsoTimer', 'torsoAnim', 'movementDir')]
    _fields_ += [('grapplePoint', F * 3), ('eFlags', I), ('eventSequence', I), ('events', I * 2), ('eventParms', I * 2)]
    _fields_ += [(n, I) for n in ('externalEvent', 'externalEventParm', 'externalEventTime', 'clientNum', 'weapon', 'weaponstate')]
    _fields_ += [('viewangles', F * 3)]
    _fields_ += [(n, I) for n in ('viewheight', 'damageEvent', 'damageYaw', 'damagePitch', 'damageCount')]
    _fields_ += [('stats', I * 16), ('persistant', I * 16), ('powerups', I * 16), ('ammo', I * 64)]

class Snapshot(Packed):
    _fields_ = [('mask', c.c_uint8 * 32), ('player', c.POINTER(PlayerPrefix))]
    _fields_ += [(n, P) for n in ('entities', 'flags', 'changed', 'removed', 'reserved')]
    _fields_ += [(n, I) for n in ('time', 'message', 'command')]
    _fields_ += [(n, U) for n in ('changed_count', 'removed_count', 'entity_count')]

class Message(Packed):
    _fields_ = [('state', P), ('commands', P), ('command_count', U), ('is_gamestate', U)]

class Input(Packed):
    _fields_ = [('buffer', P), ('reserved', P), ('sequence', I), ('length', U)]

def bind(dll, name, result, args):
    fn = getattr(dll, name)
    fn.restype, fn.argtypes = result, args
    return fn

def extract(demo, output, dll_path):
    if struct.calcsize('P') != 8:
        raise RuntimeError('UDT x64 requires 64-bit Python')
    if demo.suffix.lower() != '.dm_91':
        raise ValueError('This exporter has only been validated for dm_91')
    if demo.resolve() == output.resolve():
        raise ValueError('Output must not replace the demo')
    before = hashlib.sha256(demo.read_bytes()).hexdigest()
    dll = c.CDLL(str(dll_path.resolve(strict=True)))
    init = bind(dll, 'udtInitLibrary', I, [])
    shutdown = bind(dll, 'udtShutDownLibrary', None, [])
    create = bind(dll, 'udtCuCreateContext', P, [])
    destroy = bind(dll, 'udtCuDestroyContext', I, [P])
    protocol = bind(dll, 'udtGetProtocolByFilePath', U, [c.c_char_p])
    start = bind(dll, 'udtCuStartParsing', I, [P, U])
    parse = bind(dll, 'udtCuParseMessage', I, [P, c.POINTER(Message), c.POINTER(U), c.POINTER(Input)])
    version = bind(dll, 'udtGetVersionString', c.c_char_p, [])
    magic = bind(dll, 'udtGetUDTMagicNumber', I, [c.POINTER(I), U, I, U, U])
    id_magic = bind(dll, 'udtGetIdMagicNumber', I, [c.POINTER(I), U, I, U, U])
    if init() != 0:
        raise RuntimeError('UDT initialization failed')
    if version() != b'1.3.1':
        shutdown()
        raise RuntimeError('ABI validated only for UDT 1.3.1')
    ctx = create()
    count, segments, maximum_speed, gaps = 0, 0, 0, 0
    game_state_number = 0
    previous = None
    last_event_sequence = None
    last_external = None
    event_gaps = 0
    finished = False
    temporary = output.with_suffix(output.suffix + '.tmp')
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        protocol_id = protocol(str(demo).encode('utf-8'))
        if not ctx or start(ctx, protocol_id) != 0:
            raise RuntimeError('UDT could not start parsing')
        with demo.open('rb') as source, temporary.open('w', encoding='utf-8') as target:
            while True:
                header = source.read(8)
                if len(header) != 8:
                    raise ValueError('Truncated demo framing')
                sequence, length = struct.unpack('<ii', header)
                if sequence == -1 and length == -1:
                    finished = True
                    break
                if not 0 <= length <= 131072:
                    raise ValueError('Invalid demo packet length')
                data = source.read(length)
                if len(data) != length:
                    raise ValueError('Truncated demo packet')
                buffer = c.create_string_buffer(data)
                incoming = Input(c.cast(buffer, P), None, sequence, length)
                message, keep = Message(), U()
                error = parse(ctx, c.byref(message), c.byref(keep), c.byref(incoming))
                if error != 0:
                    raise RuntimeError(f'UDT parse error {error} at packet {sequence}')
                if message.is_gamestate:
                    game_state_number += 1
                    segments += 1
                    previous = None
                    last_event_sequence = None
                    last_external = None
                elif message.state:
                    snap = c.cast(message.state, c.POINTER(Snapshot)).contents
                    if not snap.player:
                        continue
                    ps = snap.player.contents
                    values = list(ps.origin) + list(ps.velocity) + list(ps.viewangles)
                    if not all(math.isfinite(v) for v in values) or not 0 <= ps.clientNum < 64:
                        raise ValueError('Invalid player state: check UDT ABI/version')
                    if previous and (snap.time <= previous[0] or ps.clientNum != previous[1]):
                        segments += 1
                        previous = None
                        last_event_sequence = None
                        last_external = None
                    delta = snap.time - previous[0] if previous else None
                    gaps += bool(delta and delta > 100)
                    speed = math.hypot(ps.velocity[0], ps.velocity[1])
                    maximum_speed = max(maximum_speed, speed)
                    pickups, decoded_events = [], []
                    event_inputs = []
                    # PS has only a two-event ring. Never invent events missing from that ring.
                    if last_event_sequence is not None and ps.eventSequence >= last_event_sequence:
                        event_gaps += max(0, ps.eventSequence - last_event_sequence - 2)
                        for seq in range(max(last_event_sequence, ps.eventSequence - 2), ps.eventSequence):
                            slot = seq & 1
                            event_inputs.append((ps.events[slot], ps.eventParms[slot], seq, 'player_event_ring'))
                    external = ps.externalEvent, ps.externalEventParm, ps.externalEventTime
                    if ps.externalEvent and external != last_external:
                        event_inputs.append((ps.externalEvent, ps.externalEventParm, ps.externalEventTime, 'player_external_event'))
                    last_external = external
                    for raw, parm, seq, event_source in event_inputs:
                        event_type = I()
                        normalized = event_type.value if magic(c.byref(event_type), 5, raw & ~0x300, protocol_id, 0) == 0 else None
                        decoded_events.append(dict(protocol_event_id=raw, parameter=parm,
                                                   udt_event_id=normalized, event_sequence=seq, source=event_source,
                                                   kind='weapon_fired' if normalized == 1 else 'other_or_unknown'))
                        if normalized not in (2, 3):
                            continue
                        item_type = I()
                        if magic(c.byref(item_type), 12, parm, protocol_id, 0) != 0:
                            continue
                        item = {19: 'red', 20: 'yellow', 21: 'green', 32: 'mega'}.get(item_type.value)
                        if item:
                            pickups.append(dict(kind=item, event_sequence=seq, event_source=event_source, item_protocol_id=parm))
                    last_event_sequence = ps.eventSequence
                    health_index, armor_index = I(), I()
                    health_ok = id_magic(c.byref(health_index), 1, 0, protocol_id, 0) == 0 and 0 <= health_index.value < 16
                    armor_ok = id_magic(c.byref(armor_index), 1, 3, protocol_id, 0) == 0 and 0 <= armor_index.value < 16
                    health = ps.stats[health_index.value] if health_ok else None
                    armor = ps.stats[armor_index.value] if armor_ok else None
                    if health is not None and not -10000 <= health <= 10000:
                        raise ValueError('Invalid health: check player state ABI')
                    if armor is not None and not 0 <= armor <= 10000:
                        raise ValueError('Invalid armor: check player state ABI')
                    row = dict(segment=segments, game_state_number=game_state_number, time_ms=snap.time, message=snap.message,
                               client=ps.clientNum, position=list(ps.origin), velocity=list(ps.velocity),
                               viewangles=list(ps.viewangles), weapon_id=ps.weapon,
                               pm_type=ps.pm_type, pm_flags=ps.pm_flags, ground_entity=ps.groundEntityNum,
                               speed_xy=speed, snapshot_delta_ms=delta,
                               health=health, armor=armor,
                               current_weapon_ammo=ps.ammo[ps.weapon] if 0 <= ps.weapon < 64 else None,
                               events=decoded_events,
                               observed_pov_pickups=pickups,
                               raw_mouse_or_keys_verified=False)
                    target.write(json.dumps(row) + '\n')
                    previous = snap.time, ps.clientNum
                    count += 1
                if not keep.value:
                    finished = True
                    break
        if not count:
            raise ValueError('No player snapshots extracted')
        temporary.replace(output)
    finally:
        if ctx:
            destroy(ctx)
        shutdown()
        temporary.unlink(missing_ok=True)
    after = hashlib.sha256(demo.read_bytes()).hexdigest()
    if before != after:
        raise RuntimeError('Original demo changed')
    summary = dict(demo=demo.name, demo_sha256=before, unchanged=True, snapshots=count,
                   segments=segments, gaps_over_100ms=gaps, maximum_observed_speed_xy=maximum_speed,
                   parser_finished=finished, raw_mouse_or_keys_verified=False,
                   player_event_ring_missing_events=event_gaps,
                   interpretation='POV/spectated state; segments split on POV/time discontinuity; no routes inferred')
    output.with_suffix('.summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('demo', type=Path)
    parser.add_argument('--output', type=Path, default=Path('out/demo/movement.jsonl'))
    parser.add_argument('--dll', type=Path, default=Path(__file__).resolve().parent / 'udt/bin/UDT.dll')
    args = parser.parse_args()
    print(json.dumps(extract(args.demo.resolve(strict=True), args.output.resolve(), args.dll)))

if __name__ == '__main__':
    main()
