All values are in volts. Each measured value is the median over the full sweeps in its capture.

| Circuit | Source | VOH | VOL | VM | VIL | VIH | NML | NMH |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Baseline | Measured | 5.021 | 0.063 | 2.365 | 2.036\* | 2.593 | 1.974\* | 2.428 |
| Baseline | LTspice | 5.00 | 0.00 | 2.72 | 2.369 | 3.041 | 2.369 | 1.959 |
| Two PMOS in parallel | Measured | 5.042 | 0.064 | 2.543 | 2.377\* | 2.784 | 2.313\* | 2.258 |
| Two PMOS in parallel | LTspice | 5.00 | 0.00 | 2.925 | 2.663 | 3.328 | 2.663 | 1.672 |
| Two NMOS in parallel | Measured | 5.042 | 0.064 | 2.339 | 1.974\* | 2.527 | 1.910\* | 2.515 |
| Two NMOS in parallel | LTspice | 5.00 | 0.00 | ~2.50 | ~2.10 | ~2.75 | ~2.10 | ~2.25 |

\* The slope here spans an input step of 0.45 to 0.89 V, so this value is only as fine as that step.

Switching point shift from the baseline:

| Circuit | Measured VM (V) | Measured shift (mV) | LTspice VM (V) | LTspice shift (mV) |
|---|---:|---:|---:|---:|
| Baseline | 2.365 |  | 2.72 |  |
| Two PMOS in parallel | 2.543 | +178 | 2.925 | +205 |
| Two NMOS in parallel | 2.339 | -26 | ~2.50 | ~-220 |

Capture checks:

| File | Full sweeps | Steps per sweep | Input at the 0 V step (V) | VM spread over sweeps (mV) |
|---|---:|---:|---:|---:|
| Lab3-Part2.4.csv | 2 | 30 | 0.006 | 0.1 |
| Lab3-Part2.5-strongerPMOS.csv | 2 | 29 | -0.020 | 6.2 |
| Lab3-Part2.5-strongerNMOS.csv | 4 | 30 | -0.020 | 0.3 |
