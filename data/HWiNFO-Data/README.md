<!-- dataset-grade: no -->

# data/HWiNFO-Data/

This directory holds raw HWiNFO sensor dumps. It is **not dataset-grade**: the files are
unprocessed input, and the whole directory is gitignored (`data/HWiNFO-Data/`), not just a file
pattern. Seven CSV files, about 9.6 MB.

🔑 The distilled extracts are what the project actually uses, and they live beside their sweep,
committed, as `*_sweep_voltage.csv`. This directory is the unprocessed input to that step, kept
only so an extract can be regenerated or audited. A reader wanting the voltage data should use
the extracts, not these files.

## Files

| File | Description |
|------|-------------|
| `hwinfo-20260908-p4-fullcurve-gemm.csv` | Raw HWiNFO log |
| `hwinfo-20260908-p5-splitcurve-gemm.csv` | Raw HWiNFO log |
| `hwinfo-silent-membw-matched2130.csv` | Raw HWiNFO log |
| `hwinfo-volt-OC-20260820-2108.csv` | Raw HWiNFO log |
| `hwinfo-volt-OCv2.CSV` | Raw HWiNFO log |
| `hwinfo-volt-ocsweep.CSV` | Raw HWiNFO log |
| `hwinfo-voltnonoc.CSV` | Raw HWiNFO log |

Three of these carry an uppercase `.CSV` extension. This is how HWiNFO wrote them and the
inconsistency is real, so it is not silently normalised.

## What the logs contain

These are raw HWiNFO logs carrying 300+ columns, covering every CPU, motherboard, drive and fan
sensor on the machine. Almost none of it is relevant.

Written by **HWiNFO itself**, at 2 s polling, with a voltage resolution of 5 mV.
`tools/frequency-sweep/join_hwinfo_voltage.py` **consumes** these logs — it does not produce
them — and emits the distilled `*_sweep_voltage.csv` extracts described above.

## Join behaviour

🔑 The join bins samples by core clock, not by timestamp, because a sweep CSV records durations
rather than absolute times.

⚠️ A single log must never span a profile change. Because the join bins by core clock, two
configurations measured at the same frequency would be silently merged into one median.

⚠️ A 30 W idle filter is load-bearing, not hygiene. HWiNFO polls continuously through the settle
gaps between sweep points, and an idle card sits at boost voltage, so keeping idle samples
manufactures a voltage-frequency slope out of nothing.

## Logging

⚠️ HWiNFO logging is started by hand from its GUI. It cannot be started remotely, which is why
several runs in this project have no voltage telemetry at all.
