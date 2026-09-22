# `hwinfo-logging` — start and stop HWiNFO logging without a human

**Added 2026-09-21.** `Invoke-HwinfoLogging.ps1 -Start -LogPath <abs> | -Stop | -Status`.

🔑 **What this unlocks.** Every multi-configuration item on the bench list is costed as *"the
operator must be present"* — `docs/GPU-WORKLIST-5060TI.md` item 4j says so explicitly — and the
only reason is clicking one button between runs. This removes that, which is the difference
between a session that needs Raymond at the desk for six hours and one that runs while he is at
school.

---

## Why the obvious routes are all closed

| route | why not |
|---|---|
| `HWiNFO64.exe -l -max_time=n -poll_rate=n` | ⛔ **Pro only.** The manual's §5.1 is titled *"Command Line Parameters (Pro Version)"* and the feature table lists *"Automatic sensor logging via command-line"* in the Pro column. `HWiNFO64.INI` here has no license keys |
| HWiNFO shared memory | ⚠️ **12-hour limit** on freeware |
| A computer-use agent clicking the button | ⛔ **Structurally impossible.** See below |
| `AutoLogging`-style INI key | Does not exist on this build; the INI carries `SensorInterval` and nothing logging-related |

### ⛔ Why an agent cannot click it, and elevating the agent is not the fix

HWiNFO runs elevated. **UIPI forbids a medium-integrity process from injecting input into an
elevated window**, and the failure is silent — no error, no effect, nothing in a log. Screenshots
keep working, because *reading* the screen is permitted and *injecting* is not. That asymmetry is
exactly what was observed.

Verified 2026-09-21 on the Codex desktop agent: its MSIX manifest declares `runFullTrust`,
`graphicsCaptureProgrammatic` and `graphicsCaptureWithoutBorder` but **no `allowElevation`**, and
no `TrustLevel`. Packaged apps take their integrity level from the manifest via the AppX
activation broker, so **no launch method elevates it** — not `RunAs`, not "Run as administrator",
not `--do-not-de-elevate`, which is a no-op for an app that cannot elevate at all.

✅ **So the clicker must be elevated, not the agent.** Elevated-to-elevated injection is
same-integrity and permitted. Run this script from a **scheduled task registered with highest
privileges**; the agent only needs `schtasks /run`, which works fine unelevated. The agent then
never touches a GUI, never takes a screenshot during a measurement, and cannot contaminate the
run — which matters, because desktop activity beside a sweep cost **9.38% of throughput at every
point** on 2026-09-18.

---

## ⛔ The two mistakes that cost an hour. Do not "simplify" either.

**1. `PostMessage`, never `SendMessage`, to press the log button.** `SendMessage` is synchronous
and the button opens a **modal** Save As dialog, so it blocks until that dialog closes — meaning
the script that opens the dialog can never be the script that fills it in. The first attempt
deadlocked and had to be killed with the dialog stranded on screen.

**2. `SetWindowTextW` on the filename box is not enough.** It puts the characters in the edit
control but raises no `EN_CHANGE`, so the Vista-style file dialog never updates the name it
intends to use and `IDOK` acts on an empty string. The dialog just sits there and nothing says
why. **`WM_SETTEXT` plus an explicit `EN_CHANGE` to the parent, then `IDOK`.**

Also: controls are found by **text, not HWND** — handles change every time HWiNFO starts. And the
string overload needs `EntryPoint="SendMessageW"` or the P/Invoke fails at call time.

## The control it drives

```
Sensors dialog (#32770, title matches "Sensors")
  └─ Button, dlg ctrl id 1437, text 'Log Start' / 'Log Stop'
```

🔑 **The label is the state, so the script reads it instead of assuming.** `Log Start` means
stopped; `Log Stop` means running.

## It verifies by growth, not by the click returning

A toggled label proves the button moved. **Two increasing file sizes prove samples are reaching
the disk**, which is what the run depends on — HWiNFO can hold a handle open and write nothing.
`-Start` fails with exit 7 if the file does not grow, and `-Stop` fails if it is still growing.

It also refuses to overwrite an existing log (one log per configuration is a provenance rule), and
refuses to start a second log while one is running, because the first one's path would then be
unrecoverable.

| exit | meaning |
|---|---|
| 0 | did what was asked and verified it |
| 2 | bad arguments (relative path, missing dir, existing file) |
| 3 | HWiNFO not running |
| 4 | no Sensors window with a log button |
| 5 | already logging / not logging |
| 6 | the Save As dialog never appeared or would not accept |
| 7 | the button toggled but the file disagrees |

## Verified

End-to-end on the real tool, 2026-09-21, freeware HWiNFO 8.50-6020:

```
-Status  Log button reads 'Log Start'.  Logging is stopped.
-Start   button now : 'Log Stop'    size : 22782 then 39102 bytes
-Stop    button now : 'Log Start'   size : 67516 then 67516 bytes   rows : 17
```

⚠️ **No automated test suite yet, and that is a real gap by this repo's standards.** The GUI path
is hard to test without HWiNFO present, but the argument-validation branches — relative path,
missing directory, existing file, both switches — are pure and cheap to cover. **They are
currently unverified except by reading.** It does not launch HWiNFO itself, deliberately: the
splash and the update nag are extra state to get wrong, and a run that begins by guessing at
dialogs is not a run worth having.
