# MUET Point Bus Scheduling — Discrete Event Simulation

Python 3.10+ event-calendar model for the Simulation & Modelling PBL assignment.
All input parameters are illustrative assumptions, not measured MUET data.

## Run

```bash
python simulation.py
```

This runs 40 paired replications per peak/scenario/policy combination and writes `results.csv`. The simulation uses only the Python standard library. Change the number of replications or output location as follows:

```bash
python simulation.py --replications 100 --output results.csv
```

To regenerate the report graphs:

```bash
python -m pip install matplotlib
python plot_results.py
```

## Model
- Two FCFS terminal queues (STC and Main Gate), a shared six-bus pool, capacity 40 per bus.
- Morning and afternoon are independent peak experiments, starting empty with all buses available.
- Exponential interarrival times and triangular round-trip times (including loading and repositioning).
- Fixed: departures scheduled every 15 minutes per terminal, offset 7.5 minutes; missed slots are skipped.
- Adaptive: dispatch at 30 passengers or 10 minutes oldest wait when a bus is available; prioritize longest waiting passenger. Drain after peak.
- Scenarios: normal, +30% passenger arrivals, +40% round-trip time.
- Queues drain after the arrival window; wait, trip count, maximum queue and load factor cover the full service run. Mean queue, backlog and bus utilization refer to the peak window; backlog is measured before dispatch at the closing time. P95 is averaged across replication-specific P95 values.
- Fixed random seeds and identical arrival streams for paired policy comparisons.
- Assertions check passenger conservation and fleet bounds at every event.

## Files
`simulation.py`: executable model; `plot_results.py`: chart generation; `results.csv`: computed metrics; PNGs: report figures; `report.tex`: IEEE-style LaTeX report; `README.md`: instructions.

## GitHub submission
Create an empty repository on GitHub, then from this folder run:

```bash
git init
git add .
git commit -m "MUET Point bus discrete-event simulation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

Replace the remote with your repository URL. No repository has been published automatically.
