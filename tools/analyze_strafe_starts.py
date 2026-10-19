"""Measure non-combat two-jump starts in exported Quake Live POV snapshots.

The demo format does not contain verified raw keys or mouse deltas.  This tool
therefore reports observable motion only: ground/air transitions, velocity and
view yaw.  Its output may calibrate a controller, but must never be described
as recovered player input.
"""
import argparse
import gzip
import json
import math
from pathlib import Path


AIR = 1023
# Direct solo POV uses pm_type 0; the validated spectated QL exports use 2.
# Both must remain continuous and alive. Neither implies recovered raw input.
ACTIVE_PM_TYPE = 2


def angle_delta(a, b):
    return (a - b + 180.0) % 360.0 - 180.0


def percentile(values, q):
    values = sorted(values)
    if not values:
        return None
    p = (len(values) - 1) * q
    lo, hi = int(p), min(int(p) + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (p - lo)


def summary(values):
    if not values:
        return {name: None for name in ("p10", "p25", "median", "p75", "p90")}
    return {name: round(percentile(values, q), 3) for name, q in
            (("p10", .10), ("p25", .25), ("median", .50),
             ("p75", .75), ("p90", .90))}


def continuous(a, b):
    return (a["segment"] == b["segment"] and a["client"] == b["client"] and
            0 < b["time_ms"] - a["time_ms"] <= 100 and
            a["pm_type"] == b["pm_type"] and a["pm_type"] in (0, ACTIVE_PM_TYPE) and
            a.get("health", 1) > 0 and b.get("health", 1) > 0)


def has_combat(rows):
    return any(any(e.get("kind") == "weapon_fired" for e in r.get("events", []))
               for r in rows)


def analyse_rows(rows, source):
    samples = []
    for i in range(1, len(rows)):
        before, takeoff = rows[i - 1], rows[i]
        if not continuous(before, takeoff):
            continue
        if before["ground_entity"] == AIR or takeoff["ground_entity"] != AIR:
            continue
        if not 180 <= takeoff["velocity"][2] <= 360:
            continue
        prior = [r for r in rows[max(0, i - 20):i + 1]
                 if r["segment"] == takeoff["segment"] and
                 r["client"] == takeoff["client"]]
        if not prior or takeoff["time_ms"] - prior[0]["time_ms"] < 250:
            continue
        if any(not continuous(a,b) for a,b in zip(prior,prior[1:])):
            continue
        # A start after a real pause/slow approach, rather than a later hop.
        slow = [r for r in prior if r["speed_xy"] <= 80]
        if not slow:
            continue
        start = slow[-1]
        if not 75 <= takeoff["time_ms"] - start["time_ms"] <= 500:
            continue
        horizon = [r for r in rows[i:min(len(rows), i + 165)]
                   if r["segment"] == takeoff["segment"] and
                   r["client"] == takeoff["client"] and
                   r["time_ms"] - takeoff["time_ms"] <= 4000]
        bounded=[]
        for r in horizon:
            if bounded and not continuous(bounded[-1],r):break
            if bounded and 'position' in r and 'position' in bounded[-1] and math.dist(r['position'],bounded[-1]['position'])>128:break
            bounded.append(r)
        horizon=bounded
        if has_combat(prior + horizon):
            continue
        if any(((a.get('health') or 0)-(b.get('health') or 0)>2) or ((a.get('armor') or 0)-(b.get('armor') or 0)>2)
               for a,b in zip(prior+horizon,(prior+horizon)[1:])):continue
        if any(a['ground_entity']==b['ground_entity']==AIR and math.hypot(b['velocity'][0]-a['velocity'][0],b['velocity'][1]-a['velocity'][1])>30
               for a,b in zip(horizon,horizon[1:])):continue
        landing = next((j for j in range(1, len(horizon))
                        if horizon[j - 1]["ground_entity"] == AIR and
                        horizon[j]["ground_entity"] != AIR), None)
        if landing is None:
            continue
        second = next((j for j in range(landing + 1, len(horizon))
                       if horizon[j - 1]["ground_entity"] != AIR and
                       horizon[j]["ground_entity"] == AIR and
                       180 <= horizon[j]["velocity"][2] <= 360), None)
        if second is None:
            continue
        if horizon[second]["time_ms"] - horizon[landing]["time_ms"] > 100:
            continue
        first_air = horizon[:landing + 1]
        second_air = horizon[second:]
        end2 = next((j for j in range(1, len(second_air))
                     if second_air[j - 1]["ground_entity"] == AIR and
                     second_air[j]["ground_entity"] != AIR), len(second_air))
        second_air = second_air[:end2]
        start_yaw = start["viewangles"][1]
        takeoff_yaw = takeoff["viewangles"][1]
        first_end_yaw = first_air[-1]["viewangles"][1]
        second_takeoff_yaw = horizon[second]["viewangles"][1]
        samples.append({
            "source": source,
            "segment": takeoff["segment"],
            "client": takeoff["client"],
            "first_takeoff_ms": takeoff["time_ms"],
            "ground_prestrafe_ms": takeoff["time_ms"] - start["time_ms"],
            "pre_jump_speed": round(before["speed_xy"], 3),
            "first_air_max_speed": round(max(r["speed_xy"] for r in first_air), 3),
            "second_air_max_speed": round(max(r["speed_xy"] for r in second_air), 3),
            "ground_yaw_sweep_deg": round(angle_delta(takeoff_yaw, start_yaw), 3),
            "first_air_yaw_sweep_deg": round(angle_delta(first_end_yaw, takeoff_yaw), 3),
            "second_setup_yaw_sweep_deg": round(angle_delta(second_takeoff_yaw, first_end_yaw), 3),
            "second_takeoff_delay_ms": horizon[second]["time_ms"] - takeoff["time_ms"],
            "landing_to_second_takeoff_ms": horizon[second]["time_ms"] - horizon[landing]["time_ms"],
            "raw_mouse_or_keys_verified": False,
            "observed_horizon_ms":horizon[-1]['time_ms']-takeoff['time_ms'],
            "peak_2s":round(max(r['speed_xy'] for r in horizon if r['time_ms']-takeoff['time_ms']<=2000),3),
            "peak_4s":round(max(r['speed_xy'] for r in horizon),3),
            "jump_takeoffs_in_window":sum(a['ground_entity']!=AIR and b['ground_entity']==AIR for a,b in zip(horizon,horizon[1:])),
            "view_trace":[dict(elapsed_ms=r['time_ms']-takeoff['time_ms'],yaw=r['viewangles'][1],pitch=r['viewangles'][0],velocity=r['velocity'],speed=r['speed_xy']) for r in horizon],
        })
        samples[-1]["first_air_speed_gain"] = round(samples[-1]["first_air_max_speed"] - samples[-1]["pre_jump_speed"], 3)
        samples[-1]["second_air_speed_gain"] = round(samples[-1]["second_air_max_speed"] - samples[-1]["first_air_max_speed"], 3)
        samples[-1]["ground_yaw_sweep_abs_deg"] = abs(samples[-1]["ground_yaw_sweep_deg"])
        samples[-1]["first_air_yaw_sweep_abs_deg"] = abs(samples[-1]["first_air_yaw_sweep_deg"])
    return samples


def analyse(paths):
    samples = []
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            rows = [json.loads(line) for line in stream if line.strip()]
        samples.extend(analyse_rows(rows, str(path)))
    fields = ("ground_prestrafe_ms", "pre_jump_speed", "first_air_max_speed",
              "second_air_max_speed", "ground_yaw_sweep_deg",
              "first_air_yaw_sweep_deg", "second_setup_yaw_sweep_deg",
              "ground_yaw_sweep_abs_deg", "first_air_yaw_sweep_abs_deg",
              "first_air_speed_gain", "second_air_speed_gain",
              "second_takeoff_delay_ms", "landing_to_second_takeoff_ms", "peak_2s", "peak_4s")
    return {
        "method": "observable POV state transitions; no recovered keyboard or mouse input",
        "filters": {"minimum_prior_window_ms": 250, "prior_min_speed_max": 80,
                    "standard_takeoff_vertical_speed": [180, 360],
                    "weapon_fire_in_window": "excluded", "second_jump_required": True,
                    "landing_to_second_takeoff_max_ms": 100},
        "files_scanned": len(paths),
        "sample_count": len(samples),
        "metrics": {field: summary([s[field] for s in samples]) for field in fields},
        "samples": samples,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument('--extra-corpus',type=Path,action='append',default=[])
    parser.add_argument('--shard-index',type=int,default=0)
    parser.add_argument('--shard-count',type=int,default=1)
    args = parser.parse_args()
    paths = sorted({p for corpus in [args.corpus]+args.extra_corpus for p in corpus.glob('*/snapshots.jsonl.gz')})
    paths = [p for i,p in enumerate(paths) if i%args.shard_count==args.shard_index]
    if not paths:
        parser.error("no snapshots.jsonl.gz files found")
    result = analyse(paths)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "samples"}, indent=2))


if __name__ == "__main__":
    main()
