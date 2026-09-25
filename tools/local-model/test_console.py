"""Mock-only checks for the Local Model Console and streamed request logging."""

from contextlib import redirect_stdout
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "console"))
import ask_local
import server as console
import run_queue
from streaming import iter_sse_events


def chunk(delta=None, finish=None, usage=None, timings=None):
    value = {"choices": [{"delta": delta or {}, "finish_reason": finish}]}
    if usage is not None:
        value["usage"] = usage
    if timings is not None:
        value["timings"] = timings
    return ("data: " + json.dumps(value) + "\n\n").encode()


REPLY = "```python\nprint('same bytes')\n```"
STREAM = [chunk({"reasoning_content": "step "}), chunk({"reasoning_content": "two"}),
          chunk({"content": "```python\n"}), chunk({"content": "print('same bytes')\n```"}),
          chunk(finish="stop", usage={"prompt_tokens": 12, "completion_tokens": 8},
                timings={"prompt_per_second": 33, "predicted_per_second": 44}), b"data: [DONE]\n\n"]


class FakeModel(BaseHTTPRequestHandler):
    fail_midstream = False

    def log_message(self, *_):
        pass

    def do_GET(self):
        body = json.dumps({"default_generation_settings": {"n_ctx": 65536}}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        request = json.loads(self.rfile.read(length))
        if request.get("stream"):
            self.send_response(200); self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            for line in STREAM[:2] if self.fail_midstream else STREAM:
                self.wfile.write(line); self.wfile.flush()
        else:
            body = json.dumps({"choices": [{"message": {"content": REPLY,
                             "reasoning_content": "step two"}, "finish_reason": "stop"}],
                             "usage": {"prompt_tokens": 12, "completion_tokens": 8},
                             "timings": {"prompt_per_second": 33,
                                         "predicted_per_second": 44}}).encode()
            self.send_response(200); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)


class PassingResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        print(f"[PASS] {test.id()}")


class ConsoleTests(unittest.TestCase):
    def test_real_fixture(self):
        path = HERE / "console" / "fixtures" / "claude-code-local-L1-apierror.jsonl"
        parsed = []
        for line in path.read_text(encoding="utf-8").splitlines():
            value = console.parse_transcript_line(line)
            parsed.extend(value if isinstance(value, list) else [value])
        self.assertEqual(sum(x["kind"] == "api_retry" for x in parsed), 10)
        self.assertEqual(sum(x["kind"] == "tool_use" for x in parsed), 0)
        result = next(x for x in parsed if x["kind"] == "result")
        self.assertTrue(result["is_error"])
        self.assertIn("System message must be at the beginning", result["text"])

    def test_progress_events_are_counted_not_listed(self):
        # The first live agent transcript (2026-09-24) held 10,047 system/thinking_tokens lines
        # around 42 real events, and the viewer listed every one as "other".
        for subtype in ("thinking_tokens", "task_summary"):
            line = json.dumps({"type": "system", "subtype": subtype, "session_id": "x"})
            self.assertEqual(console.parse_transcript_line(line), {"kind": "progress", "subtype": subtype})
        self.assertEqual(console.parse_transcript_line(json.dumps({"type": "system", "subtype": "init", "tools": []}))["kind"], "init")

    def test_synthetic_transcript_and_partial_tail(self):
        lines = [json.dumps({"type": "assistant", "message": {"content": [
            {"type": "thinking", "thinking": "reason"}, {"type": "text", "text": "answer"},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "x"}}]}}),
            json.dumps({"type": "user", "message": {"content": [{"type": "tool_result",
                       "tool_use_id": "a", "content": [{"type": "text", "text": "ok"}]}]}}),
            json.dumps({"type": "result", "subtype": "success", "is_error": False,
                        "num_turns": 1, "duration_ms": 8, "result": "done"}), "{broken"]
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "run.jsonl"
            file.write_text("\n".join(lines) + "\npart", encoding="utf-8")
            tail = console.tail_jsonl(file, 0, parser=console.parse_transcript_line)
            kinds = [e["kind"] for line in tail["events"] for e in (line if isinstance(line, list) else [line])]
            self.assertEqual(kinds, ["thinking", "text", "tool_use", "tool_result", "result", "malformed"])
            self.assertTrue(tail["more"])
            self.assertIn('"text": "ok"', tail["events"][1][0]["text"])
            self.assertEqual(tail["events"][-2]["text"], "done")

    def test_sse_parser(self):
        events = list(iter_sse_events(STREAM))
        self.assertEqual("".join(e["text"] for e in events if e["type"] == "reasoning"), "step two")
        self.assertEqual("".join(e["text"] for e in events if e["type"] == "answer"), REPLY)
        self.assertEqual(next(e for e in events if e["type"] == "stats")["timings"]["predicted_per_second"], 44)
        self.assertEqual(events[-1]["type"], "done")

    def test_traversal_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "runs"; root.mkdir()
            (Path(temp) / "secret.txt").write_text("secret")
            with self.assertRaises(ValueError):
                console.allowed_file({"runs": root}, "runs", "../secret.txt")
            with self.assertRaises(ValueError):
                console.allowed_file({"runs": root}, "other", "x")

    def test_listed_paths_use_forward_slashes(self):
        # Found in the first live run (2026-09-24): on Windows the list returned
        # "console\\requests-...", the page filters on "console/requests-", and the
        # Claude requests tab showed 0 while the log held a request.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "runs"; (root / "console").mkdir(parents=True)
            (root / "console" / "requests-20260925.jsonl").write_text("{}\n")
            listed = console.list_transcripts({"runs": root})
            self.assertEqual([row["path"] for row in listed], ["console/requests-20260925.jsonl"])
            self.assertTrue(console.allowed_file({"runs": root}, "runs", listed[0]["path"]).is_file())

    def test_start_refused_during_measurement(self):
        with tempfile.TemporaryDirectory() as temp:
            state = console.ConsoleState(Path(temp), Path(temp))
            with patch.object(console.run_queue, "measurement_running", return_value=["sweep"]), \
                 patch.object(console.subprocess, "Popen") as popen:
                with self.assertRaisesRegex(RuntimeError, "Measurement running"):
                    state.start_model()
                popen.assert_not_called()

    def test_loading_external_server_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as temp:
            state = console.ConsoleState(Path(temp), Path(temp))
            with patch.object(console.run_queue, "measurement_running", return_value=[]), \
                 patch.object(console.run_queue, "server_up", return_value=False), \
                 patch.object(console, "any_llama_process", return_value=True), \
                 patch.object(console.subprocess, "Popen") as popen:
                with self.assertRaisesRegex(RuntimeError, "already running"):
                    state.start_model()
                popen.assert_not_called()

    def test_stop_targets_only_owned_process(self):
        with tempfile.TemporaryDirectory() as temp:
            state = console.ConsoleState(Path(temp), Path(temp))
            owned = Mock(pid=1234); owned.poll.return_value = None
            state.started = owned
            self.assertEqual(state.stop_model(), 1234)
            owned.terminate.assert_called_once_with()
            with self.assertRaisesRegex(RuntimeError, "No console-started"):
                state.stop_model()

    def test_queue_writes_acceptance_event(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); out_dir = root / "runs" / "trial"; out_dir.mkdir(parents=True)
            job = {"id": "j1", "extension": ".py", "spec": "spec.md", "num_predict": 20}
            with patch.object(run_queue, "ROOT", root), \
                 patch.object(run_queue.subprocess, "run",
                              return_value=run_queue.subprocess.CompletedProcess([], 1, "", "failed")) as run, \
                 patch.object(run_queue.ask_local, "appendConsoleEvent") as record:
                result = run_queue.run_job(job, 2, out_dir, io.StringIO(), "trial")
            self.assertEqual(run_queue.verdict(result), "NO ANSWER")
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("--queue-name") + 1], "trial")
            self.assertEqual(command[command.index("--attempt") + 1], "2")
            self.assertEqual(record.call_args.args[0]["verdict"], "NO ANSWER")

    def test_chat_failure_is_logged(self):
        with tempfile.TemporaryDirectory() as temp:
            state = console.ConsoleState(Path(temp), Path(temp))
            emitted = []
            with patch.object(console.run_queue, "measurement_running", return_value=False), \
                 patch.object(console.urllib.request, "urlopen", side_effect=OSError("offline")):
                entry = console.chat_stream(state, {"prompt": "hello"}, emitted.append)
            self.assertIn("offline", entry["error"])
            file = next((Path(temp) / "console").glob("chat-*.jsonl"))
            self.assertEqual(json.loads(file.read_text(encoding="utf-8").splitlines()[0])["prompt"], "hello")
            self.assertEqual(emitted[-1]["type"], "complete")

    def test_streamed_ask_matches_nonstream_output_and_logs(self):
        FakeModel.fail_midstream = False
        http = ThreadingHTTPServer(("127.0.0.1", 0), FakeModel)
        thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp:
                folder = Path(temp); spec = folder / "spec.md"; spec.write_text("Write code", encoding="utf-8")
                expected = folder / "expected.py"; output = folder / "actual.py"
                with patch.object(ask_local, "HOST", f"http://127.0.0.1:{http.server_port}"), \
                     patch.object(ask_local, "BACKEND", "llamacpp"):
                    result, _ = ask_local.ask("ignored", "system", "user", False, 100, 5,
                                              ask_local.SAMPLING, 1)
                expected.write_text(ask_local.stripFences(result["content"]), encoding="utf-8")
                args = ["ask_local.py", str(spec), "--out", str(output), "--host",
                        f"http://127.0.0.1:{http.server_port}", "--num-predict", "100",
                        "--request-id", "test-request"]
                with patch.object(sys, "argv", args), patch.object(ask_local, "HERE", folder), \
                     redirect_stdout(io.StringIO()):
                    self.assertEqual(ask_local.runLoggedMain(), 0)
                self.assertEqual(output.read_bytes(), expected.read_bytes())
                events = [json.loads(line) for line in next((folder / "runs" / "console").glob("requests-*.jsonl")).read_text(encoding="utf-8").splitlines()]
                self.assertEqual([e["type"] for e in events], ["request_start", "reasoning", "reasoning", "answer", "answer", "request_end"])
                self.assertEqual("".join(e["text"] for e in events if e["type"] == "answer"), REPLY)
                self.assertEqual(events[-1]["done_reason"], "stop")
        finally:
            http.shutdown(); http.server_close()

    def test_midstream_failure_writes_request_end(self):
        FakeModel.fail_midstream = True
        http = ThreadingHTTPServer(("127.0.0.1", 0), FakeModel)
        thread = threading.Thread(target=http.serve_forever, daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory() as temp:
                folder = Path(temp); spec = folder / "spec.md"; spec.write_text("Write code", encoding="utf-8")
                args = ["ask_local.py", str(spec), "--host", f"http://127.0.0.1:{http.server_port}",
                        "--num-predict", "100"]
                with patch.object(sys, "argv", args), patch.object(ask_local, "HERE", folder), \
                     redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        ask_local.runLoggedMain()
                events = [json.loads(line) for line in next((folder / "runs" / "console").glob("requests-*.jsonl")).read_text(encoding="utf-8").splitlines()]
                self.assertEqual(events[-1]["type"], "request_end")
                self.assertIn("ended before", events[-1]["error"])
                self.assertFalse(events[-1]["output_written"])
        finally:
            http.shutdown(); http.server_close(); FakeModel.fail_midstream = False


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ConsoleTests)
    result = unittest.TextTestRunner(resultclass=PassingResult, verbosity=0).run(suite)
    raise SystemExit(not result.wasSuccessful())
