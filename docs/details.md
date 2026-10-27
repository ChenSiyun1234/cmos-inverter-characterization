# CMOS inverter details

The front page covers what I built and what I found. This page has the setup and the method behind each number.

## Setup

The inverters ran on a breadboard from a 5 V supply. An ADALM2000 with Scopy drove the input and recorded both nodes at 1 kS/s. CH1 is the input and CH2 is the output.

The input was a staircase from the M2K signal generator. Steps were 500 mV far from the switching point and 50 mV near it, and each step lasted 100 ms. Each capture holds two to four full repeats of the staircase. The step plan of each capture is in [data/README.md](../data/README.md).

LTspice ran a DC sweep of the same three inverters from 0 to 5 V in 1 mV steps. The values I took from it are in [sim/ltspice_values.csv](../sim/ltspice_values.csv). A `~` there marks a value I recorded as approximate.

## How analyze.py gets each number

The script works on steps, not raw samples. A sample-by-sample slope is too noisy here, because the scope code of about 20 mV is close to the 50 mV step.

1. Split CH1 into flat steps. An edge is where the median of the next 10 ms differs from the median of the last 10 ms by more than 30 mV. Drop 5 ms at each end of a step, then keep the median input and output.
2. Split the steps into sweeps from 0 V to 5 V. Keep only the full sweeps.
3. VOH is the output at the lowest step. VOL is the output at the highest step.
4. VM is where the output equals the input. The script interpolates between the two steps around it.
5. The slope at each step is the line through its two neighbors. VIL and VIH are where this slope crosses -1 on each side of the steepest step.
6. NML = VIL - VOL and NMH = VOH - VIH. The tables show the median over the full sweeps.

A value gets a `*` in the tables when the slope behind it spans an input step wider than 0.1 V. In these captures that happens to all three VIL values, where the step is 0.45 to 0.89 V wide. NML gets the star from VIL. With two PMOS it runs from 1.5 V to 2.4 V. VM and VIH come from the 50 mV steps.

## How well the method works

The tests build synthetic tanh transfer curves with known answers. With the lab's 50 mV steps and 20 mV scope code, VM lands within 10 mV of the true value on those curves. VIL and VIH land within 40 mV.

On the real captures, repeated sweeps of the same circuit agree on VM within 7 mV.

## The numbers in more detail

- Two PMOS in parallel raised VM by 178 mV, from 2.365 V to 2.543 V. LTspice predicted 205 mV.
- The stronger pull-up also cut NMH from 2.428 V to 2.258 V.
- Two NMOS in parallel moved VM down by 26 mV, to 2.339 V. LTspice predicted a drop of about 220 mV.
- Both Part 2.5 captures read the 0 V step at -0.020 V, while the baseline capture reads 0.006 V. That 26 mV offset is small next to the PMOS shift. It's as large as the NMOS shift, so the NMOS shift is within the offset.
- Measured VM sits 355 mV below LTspice for the baseline and 382 mV below for two PMOS.

The full tables are in a collapsed section near the end of the front page, and in [results/summary.md](../results/summary.md).

## Square-wave check

The lab also drove three gates with a square wave. Each gate sat between a driver inverter and a load inverter, in LTspice and on the breadboard. These Vpp values come from my lab report, not from a capture in this repo.

| Gate | LTspice Vpp (V) | Measured Vpp (V) | Difference |
|---|---:|---:|---:|
| Inverter | 5.18 | 5.30 | 2.29% |
| NAND | 5.23 | 5.40 | 3.20% |
| NOR | 5.27 | 5.50 | 4.27% |

The difference is |measured - LTspice| divided by the mean of the two.

## Tests and CI

There are 34 pytest tests in [tests/test_analyze.py](../tests/test_analyze.py). Most of them build synthetic curves or fake Scopy files with known answers. Two run on the real captures. One checks that each capture splits into 100 ms steps, and the other checks that the tables in the README still match the data.

GitHub Actions runs on every push and pull request. It runs the tests and the analysis, then fails if the committed `results/summary.md` no longer matches what the script writes.

## Files

```
analyze.py   the analysis and the plots
data/        raw Scopy captures, unchanged, and their step plans
sim/         LTspice values from the lab
results/     summary.md and the two plots, written by analyze.py
tests/       pytest tests
docs/        this page
```
