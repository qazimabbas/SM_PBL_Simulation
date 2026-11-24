"""MUET Point bus discrete-event simulation (synthetic data). Python 3.10+."""
from collections import deque
from heapq import heappush, heappop
from itertools import count
from random import Random
from statistics import mean
import argparse
import csv
from pathlib import Path

FLEET, CAPACITY = 6, 40
TERMINALS = ('STC', 'Main Gate')
# Separate peak windows; rates are passengers per minute, not measured data.
PEAKS = {'Morning': (60, (2.2, 1.5)), 'Afternoon': (90, (3.2, 1.9))}
SCENARIOS = {'Normal': (1.0, 1.0), 'High demand': (1.3, 1.0),
             'Traffic delay': (1.0, 1.4)}


def simulate(peak, scenario, policy, seed):
    horizon, rates = PEAKS[peak]
    demand, traffic = SCENARIOS[scenario]
    queues = [deque(), deque()]
    events, serial = [], count()
    idle, now, last = FLEET, 0.0, 0.0
    busy_area, queue_area = 0.0, 0.0
    arrived, trips, boarded, max_queue = 0, 0, 0, 0
    backlog = None
    waits = []
    trip_rng = [Random(seed + 100003 + i) for i in range(2)]

    def schedule(t, kind, terminal=-1):
        # Arrivals, returns, then peak snapshot, then dispatch checks.
        priorities = {'arrival': 0, 'return': 1, 'snapshot': 2, 'slot': 3, 'check': 3}
        heappush(events, (t, priorities[kind], next(serial), kind, terminal))

    # Identical arrival stream in both policies for each paired replication.
    for i, rate in enumerate(rates):
        rng = Random(seed + 7919 * i)
        t = rng.expovariate(rate * demand)
        while t < horizon:
            schedule(t, 'arrival', i)
            t += rng.expovariate(rate * demand)
    schedule(horizon, 'snapshot')
    if policy == 'Fixed':
        # Alternating terminal slots, each terminal every 15 minutes.
        schedule(0, 'slot', 0)
        schedule(7.5, 'slot', 1)

    def dispatch(i):
        nonlocal idle, trips, boarded
        n = min(CAPACITY, len(queues[i]))
        assert idle > 0 and n > 0
        for _ in range(n):
            waits.append(now - queues[i].popleft())
        idle -= 1
        trips += 1
        boarded += n
        # Round trip includes loading and repositioning to the common pool.
        duration = traffic * trip_rng[i].triangular(24, 36, 30)
        schedule(now + duration, 'return')

    def adaptive():
        # Dispatch at 30 waiting or 10 minutes oldest wait, or drain after peak.
        while idle:
            eligible = [i for i, q in enumerate(queues) if q and
                        (len(q) >= 30 or now - q[0] >= 10 - 1e-9 or now >= horizon)]
            if not eligible:
                break
            i = max(eligible, key=lambda j: (now - queues[j][0], len(queues[j])))
            dispatch(i)

    while events:
        now, _, _, kind, i = heappop(events)
        dt = max(0.0, min(now, horizon) - min(last, horizon))
        busy_area += (FLEET - idle) * dt
        queue_area += sum(map(len, queues)) * dt
        last = now
        if kind == 'arrival':
            queues[i].append(now)
            arrived += 1
            if policy == 'Adaptive':
                schedule(now + 10, 'check')
        elif kind == 'return':
            idle += 1
        elif kind == 'snapshot':
            backlog = sum(map(len, queues))
        elif kind == 'slot':
            if idle and queues[i]:
                dispatch(i)
            if now < horizon or any(queues):
                schedule(now + 15, 'slot', i)
        max_queue = max(max_queue, sum(map(len, queues)))
        if policy == 'Adaptive':
            adaptive()
        assert 0 <= idle <= FLEET
        assert arrived == boarded + sum(map(len, queues))
        if now >= horizon and not any(queues) and backlog is not None:
            break  # All passengers boarded; no need to finish final return trips.

    assert arrived == boarded == len(waits) and backlog is not None
    sorted_waits = sorted(waits)
    from math import ceil
    return {'arrivals': arrived, 'mean_wait': mean(waits) if waits else 0,
            'p95_wait': sorted_waits[ceil(.95 * len(waits)) - 1] if waits else 0,
            'max_queue': max_queue, 'mean_queue': queue_area / horizon,
            'backlog': backlog, 'trips': trips,
            'utilization': 100 * busy_area / (FLEET * horizon),
            'load_factor': 100 * boarded / (trips * CAPACITY) if trips else 0}


def experiment(replications=40):
    rows = []
    for peak in PEAKS:
        for scenario in SCENARIOS:
            for policy in ('Fixed', 'Adaptive'):
                runs = [simulate(peak, scenario, policy, 2026 + 1009*r)
                        for r in range(replications)]
                rows.append({'peak': peak, 'scenario': scenario, 'policy': policy,
                             **{k: mean(run[k] for run in runs) for k in runs[0]}})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replications', type=int, default=40)
    parser.add_argument('--output', type=Path, default=Path('results.csv'))
    args = parser.parse_args()
    if args.replications < 1:
        parser.error('replications must be positive')
    rows = experiment(args.replications)
    with args.output.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    for r in rows:
        print(f"{r['peak']:9} {r['scenario']:13} {r['policy']:8} "
              f"wait={r['mean_wait']:6.2f} min | peak queue={r['max_queue']:6.1f} "
              f"| utilization={r['utilization']:5.1f}% | load={r['load_factor']:5.1f}%")

if __name__ == '__main__':
    main()
