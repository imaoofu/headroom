# Headroom Bench catalog schema v1

The catalog is UTF-8 JSON. `schemaVersion` is `1`. `Test-Plan.ps1 -PlanPath <absolute file>` validates it before any run. Run `catalog/build_sessiond.py` in the repository to regenerate the shipped Session D example.

Top level: `title`, `volumeLabel`, `card`, `revert`, `runs`, and optional `afterRevertHuman`. `card` has the exact `nvidia-smi` GPU name and the supported graphics clock bounds in MHz. The engine also checks the live card's supported-clock table. `revert` has a profile `slot` and a `witness` object; it runs in cleanup even after failure. `afterRevertHuman` describes a final hands-on action after the revert witness.

Each run has `id`, `name`, `why`, estimated `minutes`, numeric `priority` (lower first), `preselected`, `locked`, and a `steps` array. Optional `requires` lists run IDs that must be present earlier. Optional `group` keeps runs contiguous; `finalRun` requires that run to be last. The window opens with all `preselected` runs checked and ordered as written. A run stays atomic when dragged. Session D's stock/edit sequence stays contiguous and ordered. The operator may untick a run; the resulting selection and every edit are recorded in `customizations` in the generated plan and session JSON. Edit a run by double-clicking its row. A custom sweep is inserted before the final cleanup run.

Step `id` values are unique within a run. Every step has `type` and `name`. Optional `estimatedMinutes` is used only for the window's finish estimate; it never controls a workload or timeout.

| Type | Required fields | Effect and verdict |
|---|---|---|
| `gate-power` | `limit`, `default`, `max` in W | Exact comparison to `nvidia-smi` power limits; records driver. |
| `gate-quiet` | `maxUtil` percent | Five `pmon` samples; SM is summed across processes in each sample and must remain below threshold. Encoder and decoder must stay at zero. |
| `gate-hash` | `path`, `prefix` | Exactly one profile file and SHA-256 prefix match. |
| `gate-drift` | `firstRun`, `lastRun`, `workloads`, `maxMedianAbsPct` | For each workload, median absolute matched-target throughput change across two 13-point suites; fail if any workload exceeds the limit. |
| `apply-profile` | `slot` 1..5 | Applies Afterburner, waits eight seconds; following witness decides success. |
| `witness` | `workload`, `iterations`, `coreMin`, `coreMax`, `memoryMin`, `memoryMax` | Runs bundled Python, ignores the first four 1 s samples, checks loaded peaks. Optional `lockMhz`, `voltageMin`, `voltageMax` require a short active HWiNFO log. |
| `hwinfo-start` | `path` | Starts a new CSV with the existing HWiNFO script. Exit 4/6/7 asks the operator to start it and verifies file growth. |
| `hwinfo-stop` | none | Stops and checks the log. |
| `suite` | `label`, `settings`, `workloads`, `iterations`, `expectedMemoryClockMhz` | Calls `Collect.ps1`; verifies one new result directory and throughput-bearing CSVs. |
| `sweep` | `label`, `settings`, `workload`, `iterations`, `minMhz`, `maxMhz`, `points`, `direction`, `output` | Calls `Invoke-FrequencySweep.ps1`; checks its exit and CSV. `direction` is `ascending` or `descending`. |
| `human` | `instruction` | Pauses for Continue. Optional `launchHwinfo` starts the bundled HWiNFO first. |

The profile-store hash path may be an absolute Windows path. HWiNFO logs and sweep output must use `kit:/results/...`, resolved under the kit root found from the USB volume label; `..` is forbidden. Live plan and session files must also stay on the USB kit. No result or log path is overwritten. A resume keeps the original plan and records a fresh `-resume-<timestamp>` suffix for a restarted run's logs and sweep directory.

The validator requires a log around each suite and sweep and prevents one log from being shared. `iterations` is one integer for a sweep, so work cannot vary between points. It also checks custom sweep bounds against the catalog card range. Live execution is checked again against `nvidia-smi`'s supported graphics clocks.

For a new card, copy the catalog, replace the exact model and supported-clock range from that card, define stock and revert witnesses from measured same-card values, and check every profile and workload setting against its worklist. A filename alone is not a settings witness.
