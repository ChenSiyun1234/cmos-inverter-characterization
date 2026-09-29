# Raw captures

These are the Scopy exports from the lab bench, unchanged. I captured them on 2026-05-07.

| File | Circuit | Samples | Staircase |
|---|---|---:|---|
| `Lab3-Part2.4.csv` | Baseline inverter | 7,992 | 30 steps, repeats every 3.0 s |
| `Lab3-Part2.5-strongerPMOS.csv` | Two PMOS in parallel | 7,992 | 29 steps, repeats every 2.9 s |
| `Lab3-Part2.5-strongerNMOS.csv` | Two NMOS in parallel | 16,000 | 30 steps, repeats every 3.0 s |

## Instrument

- ADALM2000 (M2K) with the Scopy oscilloscope, version string `3d4c582`.
- 1,000 samples per second. The scope code size is about 20 mV.
- CH1 is the inverter input. CH2 is the inverter output.
- The M2K signal generator drove the input as a staircase. Each step lasts 100 ms.

## Step plans

I read these from CH1. They repeat inside each file.

- Baseline: 0 to 2.0 V in 0.5 V steps, then 2.2 V. Then 2.25 to 3.2 V in 50 mV steps. Then 3.5 to 5.0 V in 0.5 V steps.
- Two PMOS: 0 to 1.5 V in 0.5 V steps. Then 2.4 to 3.4 V in 50 mV steps. Then 3.5 to 5.0 V in 0.5 V steps.
- Two NMOS: 0 to 1.5 V in 0.5 V steps. Then 1.95 to 3.0 V in 50 mV steps. Then 3.5 to 5.0 V in 0.5 V steps.

The 0 V step reads 6 mV in the baseline file and -20 mV in the two Part 2.5 files.

## File format

Lines that start with `;` are the Scopy header. The export date is day/month/year. Scopy wrote that line in the PC's locale, so it is not UTF-8. `analyze.py` reads the files as bytes for this reason.
