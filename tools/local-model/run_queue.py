"""Run a queue of local-model jobs unattended, check each answer, and stop the server afterwards.

Written 2026-09-23 so the 5060 Ti's idle day could be used while Raymond was away. One command:

    python tools/local-model/run_queue.py tools/local-model/queue-20260924.json

For every job in the queue it runs `ask_local.py` once per attempt (different seeds), saves each
answer, and runs the job's acceptance script on it. Results go to `runs/<queue name>/`: every
answer, every acceptance report, and `summary.md`. **A PASS here is the acceptance script's
verdict, not a review.** Nothing is committed and nothing is copied into the repository's code.
Claude reviews the results and records them in docs/local-model-findings/.

THE HAZARD this guards: the model runs on the 5060 Ti, the card the research measures
(tools/local-model/README.md). The runner refuses to start if a sweep, suite or bench session is
running, and it stops the server it started when the queue ends, so the card is left free.
"""

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import ask_local  # noqa: E402  (SERVER_COMMAND and the port live there, once)

MEASUREMENT_MARKERS = ("Invoke-FrequencySweep", "Invoke-LoggedSweep", "Collect.ps1", "Run-Plan.ps1",
                       "gpu_workload.py", "Run-OffsetLadder", "Run-ActivityAB")


def measurement_running():
    """Command lines of anything that is measuring the GPU right now."""
    probe = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process | ForEach-Object { $_.CommandLine }"],
        capture_output=True, text=True, timeout=60)
    return [line for line in probe.stdout.splitlines()
            if any(marker in line for marker in MEASUREMENT_MARKERS)]


def server_up():
    try:
        with urllib.request.urlopen(ask_local.BACKENDS["llamacpp"] + "/health", timeout=5) as reply:
            return reply.status == 200
    except OSError:
        return False


def start_server(log_path, wait_seconds):
    # A cold --no-mmap load reads the whole 14 GB file; its duration has never been measured,
    # so wait generously and fail loudly rather than guess.
    log = open(log_path, "w", encoding="utf-8")
    process = subprocess.Popen(ask_local.SERVER_COMMAND, stdout=log, stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"llama-server exited with {process.returncode}; see {log_path}")
        if server_up():
            return process
        time.sleep(5)
    process.terminate()
    raise RuntimeError(f"llama-server not healthy after {wait_seconds} s; see {log_path}")


def run_job(job, attempt, out_dir, log):
    out = out_dir / f"{job['id']}-attempt{attempt}{job['extension']}"
    command = [sys.executable, str(HERE / "ask_local.py"), str(ROOT / job["spec"]),
               "--out", str(out), "--num-predict", str(job["num_predict"]), "--seed", str(attempt)]
    for context in job.get("context", []):
        command += ["--context", str(ROOT / context)]
    started = time.time()
    ask = subprocess.run(command, capture_output=True, text=True, timeout=job.get("timeout", 3600), cwd=ROOT)
    log.write(f"\n== {job['id']} attempt {attempt}: ask_local exit {ask.returncode}\n{ask.stdout}\n{ask.stderr}\n")
    result = {"job": job["id"], "attempt": attempt, "output": str(out.relative_to(ROOT)),
              "ask_exit": ask.returncode, "seconds": round(time.time() - started, 1),
              "accept_exit": None, "accept_report": None}
    if ask.returncode == 0 and out.is_file() and job.get("accept"):
        check = subprocess.run([sys.executable, str(ROOT / job["accept"]), str(out)],
                               capture_output=True, text=True, timeout=600, cwd=ROOT)
        report = out.with_suffix(out.suffix + ".accept.txt")
        report.write_text(check.stdout + check.stderr, encoding="utf-8")
        result["accept_exit"] = check.returncode
        result["accept_report"] = str(report.relative_to(ROOT))
    return result


def verdict(result):
    if result["ask_exit"] != 0:
        return "NO ANSWER"
    if result["accept_exit"] is None:
        return "ANSWERED, NOT CHECKED"
    return "PASSED ACCEPTANCE" if result["accept_exit"] == 0 else "FAILED ACCEPTANCE"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("queue", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="print the plan and exit; start nothing")
    parser.add_argument("--wait", type=int, default=900, help="seconds to wait for the server to load")
    args = parser.parse_args()
    queue = json.loads(args.queue.read_text(encoding="utf-8"))
    out_dir = HERE / "runs" / args.queue.stem
    for job in queue["jobs"]:
        needed = [job["spec"], *job.get("context", [])] + ([job["accept"]] if job.get("accept") else [])
        missing = [path for path in needed if not (ROOT / path).is_file()]
        if missing:
            sys.exit(f"{job['id']}: missing {', '.join(missing)}")
    total = sum(job["attempts"] for job in queue["jobs"])
    print(f"Queue {args.queue.name}: {len(queue['jobs'])} jobs, {total} attempts. Output: {out_dir}")
    if args.dry_run:
        for job in queue["jobs"]:
            print(f"  {job['id']}: {job['attempts']} x {job['spec']}, checked by {job.get('accept', 'nothing')}")
        return 0
    busy = measurement_running()
    if busy:
        print("Refusing to start: something is measuring the GPU, and the model would share its card.")
        for line in busy[:5]:
            print("  " + line[:160])
        return 2
    if out_dir.exists() and any(out_dir.iterdir()):
        sys.exit(f"Refusing to overwrite {out_dir}; move it or use a new queue name.")
    out_dir.mkdir(parents=True, exist_ok=True)
    server = None
    results = []
    with open(out_dir / "run.log", "w", encoding="utf-8") as log:
        try:
            if server_up():
                print("llama-server already running on 8099; using it, and leaving it running.")
            else:
                print("Starting llama-server (a cold load can take minutes)...")
                server = start_server(out_dir / "llama-server.log", args.wait)
                print("llama-server is healthy.")
            for job in queue["jobs"]:
                for attempt in range(1, job["attempts"] + 1):
                    print(f"{job['id']} attempt {attempt} of {job['attempts']}...", flush=True)
                    result = run_job(job, attempt, out_dir, log)
                    results.append(result)
                    log.flush()
                    print(f"  {verdict(result)} in {result['seconds']} s")
                    (out_dir / "summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        finally:
            if server is not None:
                server.terminate()
                try:
                    server.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    server.kill()
                print("llama-server stopped; the card is free.")
    lines = [f"# Local-model queue {args.queue.name}: results", "",
             "**A pass is the acceptance script's verdict, not a review.** Claude reviews each answer and",
             "records it in docs/local-model-findings/ before anything is used.", "",
             "| job | attempt | verdict | seconds | answer | acceptance report |", "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['job']} | {r['attempt']} | {verdict(r)} | {r['seconds']} | `{r['output']}` | "
                     f"{'`' + r['accept_report'] + '`' if r['accept_report'] else '-'} |")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    passed = sum(1 for r in results if verdict(r) == "PASSED ACCEPTANCE")
    print(f"Done: {passed} of {len(results)} attempts passed their acceptance check. See {out_dir / 'summary.md'}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
