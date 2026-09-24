TASK: extend tools/afterburner/decode_profiles.py so it can read the RTX 3070 Ti profile store

Return the COMPLETE new contents of `tools/afterburner/decode_profiles.py` as one Python file, and
nothing else: no explanation before or after it. The current file is included above as context.

## YOU HAVE NO TOOLS AND CANNOT READ ANY FILE

Everything you need is in this message. Do not claim to have run anything. Your output will be
checked afterwards by a script you have not seen, against real data, and by the existing test suite.

## The situation

The decoder reads MSI Afterburner's VFCurve blobs. Each blob is 3224 bytes: an 8-byte header,
then 127 records of three little-endian float32 values `(offset_mhz, voltage_mv, base_mhz)`, then a
tail. It was written for a 5060 Ti store with five profile slots. A second card, an RTX 3070 Ti,
has a store the decoder refuses, for two reasons:

1. **It has three profile slots, not five.** The file has sections `Startup` (every value empty,
   including `VFCurve`), `Profile1`, `Profile2` and `Profile3`. There is no `Profile4` or `Profile5`.
   `load_profiles` raises "missing profiles: Profile4, Profile5".
2. **Its tail is not zero-filled.** After the 127 records the 5060 Ti files repeat the final offset
   once and then contain only zero bytes. The 3070 Ti blobs carry nonzero values further into the
   tail (the floats 1785.0 and 83.0 repeating). `decode_hex` raises "VFCurve tail is not final
   offset repeated, then zero-filled". Nobody knows what those tail values mean. Do not decode them.

There is also a pairing question. Read naively, `applied = base + offset` of the same record. On
both cards the evidence says the stored offset lags by one record: the value the curve editor
shows at record `i` is `base[i] + offset[i+1]`. This is established for this project by the curve
editor's own tooltip on the 3070 Ti (831.25 mV: 1215 MHz) and by one point on the 5060 Ti. It is
**not** documented by MSI. The naive reading must stay the default.

## What to change

Everything that exists must keep working exactly as it does now. The existing tests in
`analysis/test_decode_profiles.py` call `decode_hex(hex_text)`, `load_profiles(path)` and
`verify_rung(snapshot, profiles, rung)` with their current arguments and must still pass unchanged.
Do not rename, remove or change the behaviour of any existing function, class, field, constant or
CLI flag. Only ADD:

1. `decode_hex(hex_text, *, allow_tail=False)`. With `allow_tail=True`, skip ONLY the tail check;
   keep every other check (length, header, 127 records, finite values, ascending voltages).
2. `load_profiles(path, *, allow_partial=False, allow_tail=False)`. With `allow_partial=True`,
   decode every section named `Profile1` to `Profile5` that exists AND has a non-empty `VFCurve`,
   in slot order, and raise `ValueError` if there is none. Pass `allow_tail` through to
   `decode_hex`. With both left False, behave exactly as now.
3. A module-level function `next_record_pairing(points)` that takes a profile's `points` tuple and
   returns a tuple of the same length: element `i` is `points[i].base_mhz + points[i + 1].offset_mhz`,
   and the LAST element is `None` (there is no next record). It reads stored fields only; it must
   not use `applied_mhz` or `offset_boundary`.
4. Two CLI flags, both off by default:
   - `--lenient` calls `load_profiles(..., allow_partial=True, allow_tail=True)`;
   - `--pairing {stored,next}`, default `stored`, which is today's output. With `next`, print for
     each profile one line per point whose next-paired clock is not None and is <= 3090 MHz, in the
     form `  {voltage_mv:g} mV: {clock:g} MHz (next-record pairing)`, after a header line
     `{name}: next-record pairing, {count} points <=3090 MHz; NOT the committed default reading`.
   - With `--json`, add a `"next_pair_mhz"` list to each profile beside `"points"`, whatever
     `--pairing` says.
   - `--verify-rung` stays 5060 Ti only. If it is combined with `--lenient`, exit with a parser
     error.
5. Update the module docstring: say what the two new modes do, that next-record pairing is
   supported by two files and one editor tooltip rather than by documentation, and that the tail
   values are not decoded.

## Style

Match the file: the same comment density, and comments that say why rather than what.
Python 3.10+. Standard library only.
