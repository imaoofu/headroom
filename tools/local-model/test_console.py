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
from assembly import assemble_agent_lines, assemble_request_lines
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
    def test_partial_messages_reconcile_without_duplicates(self):
        def line(item):
            return json.dumps(item, ensure_ascii=False)
        items = [
            {"type": "user", "message": {"content": [{"type": "text", "text": "Inspect file"}]}},
            {"type": "stream_event", "event": {"type": "message_start", "message": {"role": "assistant", "id": "m1"}}},
            {"type": "stream_event", "event": {"type": "content_block_start", "index": 0,
                "content_block": {"type": "thinking", "thinking": ""}}, "timestamp": "2026-09-24T10:00:00Z"},
            {"type": "stream_event", "event": {"type": "content_block_delta", "index": 0,
                "delta": {"type": "thinking_delta", "thinking": "Need "}}, "timestamp": "2026-09-24T10:00:01Z"},
            {"type": "stream_event", "event": {"type": "content_block_delta", "index": 0,
                "delta": {"type": "thinking_delta", "thinking": "file"}}},
            {"type": "stream_event", "event": {"type": "content_block_stop", "index": 0},
                "timestamp": "2026-09-24T10:00:03Z"},
            {"type": "stream_event", "event": {"type": "content_block_start", "index": 1,
                "content_block": {"type": "tool_use", "id": "tool1", "name": "Read", "input": {}}}},
            {"type": "stream_event", "event": {"type": "content_block_delta", "index": 1,
                "delta": {"type": "input_json_delta", "partial_json": '{"file_pa'}}},
            {"type": "stream_event", "event": {"type": "content_block_delta", "index": 1,
                "delta": {"type": "input_json_delta", "partial_json": 'th":"a.py"}'}}},
            {"type": "stream_event", "event": {"type": "content_block_stop", "index": 1}},
            {"type": "stream_event", "event": {"type": "content_block_start", "index": 2,
                "content_block": {"type": "text", "text": ""}}},
            {"type": "stream_event", "event": {"type": "content_block_delta", "index": 2,
                "delta": {"type": "text_delta", "text": "Found "}}},
            {"type": "stream_event", "event": {"type": "message_stop"}},
            {"type": "assistant", "message": {"id": "m1", "content": [
                {"type": "thinking", "thinking": "Need file"},
                {"type": "tool_use", "id": "tool1", "name": "Read", "input": {"file_path": "a.py"}},
                {"type": "text", "text": "Found code"}]}},
            {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "tool1",
                "content": "print(1)"}]}},
            {"type": "result", "subtype": "success", "is_error": False,
                "num_turns": 1, "duration_ms": 4000, "result": "Found code"},
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "partial.jsonl"
            path.write_text("\n".join(map(line, items[:8])) + "\n", encoding="utf-8")
            first_lines, offset, _ = console.read_jsonl_lines(path, 0)
            first, state = assemble_agent_lines(first_lines)
            self.assertEqual("".join(e["text"] for e in first if e["type"] == "thinking_delta"), "Need file")
            self.assertEqual(first[-1]["text"], '{"file_pa')
            with path.open("a", encoding="utf-8") as handle:
                handle.write("\n".join(map(line, items[8:])) + "\n")
            second_lines, final_offset, _ = console.read_jsonl_lines(path, offset)
            second, _ = assemble_agent_lines(second_lines, state)
            self.assertEqual(final_offset, path.stat().st_size)
        all_events = first + second
        self.assertEqual(sum(e["type"] == "turn_start" for e in all_events), 1)
        self.assertEqual(sum(e["type"] == "tool_start" for e in all_events), 1)
        self.assertEqual("".join(e["text"] for e in all_events if e["type"] == "thinking_delta"), "Need file")
        self.assertEqual("".join(e["text"] for e in all_events if e["type"] == "text_delta"), "Found code")
        self.assertEqual(json.loads("".join(e["text"] for e in all_events if e["type"] == "tool_input_delta")),
                         {"file_path": "a.py"})
        self.assertEqual(next(e for e in all_events if e["type"] == "thinking_end")["seconds"], 2.0)
        self.assertEqual(next(e for e in all_events if e["type"] == "tool_result")["tool_id"], "tool1")
        self.assertEqual(all_events[-1]["type"], "result")

    def test_nonpartial_fixture_assembles_turns(self):
        path = HERE / "console" / "fixtures" / "claude-code-local-L1-apierror.jsonl"
        lines, offset, more = console.read_jsonl_lines(path, 0)
        self.assertFalse(more)
        self.assertEqual(offset, path.stat().st_size)
        events, _ = assemble_agent_lines(lines)
        self.assertEqual(sum(e["type"] == "retry_count" and e["count"] == 10 for e in events), 1)
        self.assertEqual(sum(e["type"] == "tool_start" for e in events), 0)
        self.assertTrue(next(e for e in events if e["type"] == "result")["is_error"])

    def test_real_partial_fixture_matches_whole_messages(self):
        path = HERE / "console" / "fixtures" / "claude-code-local-partial.jsonl"
        lines, offset, more = console.read_jsonl_lines(path, 0)
        self.assertFalse(more)
        self.assertEqual(offset, path.stat().st_size)
        events, _ = assemble_agent_lines(lines)
        originals = [json.loads(line)["message"] for _, line in lines
                     if json.loads(line).get("type") == "assistant"]
        message_ids = list(dict.fromkeys(message["id"] for message in originals))
        turn_ids = [event["turn_id"] for event in events if event["type"] == "turn_start"]
        self.assertEqual(len(message_ids), len(turn_ids))
        for message_id, turn_id in zip(message_ids, turn_ids):
            blocks = [block for message in originals if message["id"] == message_id
                      for block in message["content"]]
            for kind, field, event_type in (("thinking", "thinking", "thinking_delta"),
                                            ("text", "text", "text_delta")):
                expected = "".join(block.get(field, "") for block in blocks if block["type"] == kind)
                actual = ""
                for event in events:
                    if event["type"] == event_type and event["turn_id"] == turn_id:
                        actual = event["text"] if event.get("replace") else actual + event["text"]
                self.assertEqual(actual, expected, f"{message_id}: {kind}")
            tools = [block for block in blocks if block["type"] == "tool_use"]
            started = [event for event in events if event["type"] == "tool_start" and event["turn_id"] == turn_id]
            self.assertEqual(len(started), len(tools))
            for tool in tools:
                start = next(event for event in started if event["tool_id"] == tool["id"])
                value = ""
                for event in events:
                    if event["type"] == "tool_input_delta" and event["turn_id"] == turn_id and event["block"] == start["block"]:
                        value = event["text"] if event.get("replace") else value + event["text"]
                self.assertEqual(json.loads(value), tool["input"])
        self.assertEqual(sum(event["type"] == "turn_end" for event in events), 5)
        self.assertEqual(next(event for event in events if event["type"] == "result")["turns"], 5)

    def test_request_events_stream_in_order(self):
        lines = [(8, json.dumps({"type": "request_start", "request_id": "r", "user": "prompt",
                                 "time": "2026-09-24T10:00:00Z"})),
                 (17, json.dumps({"type": "reasoning", "request_id": "r", "text": "think"})),
                 (26, json.dumps({"type": "answer", "request_id": "r", "text": "answer",
                                  "time": "2026-09-24T10:00:03Z"})),
                 (35, json.dumps({"type": "request_end", "request_id": "r", "timings": {"wall_seconds": 3}})),
                 (44, json.dumps({"type": "accepted", "request_id": "r", "verdict": "PASSED ACCEPTANCE"}))]
        events, _ = assemble_request_lines(lines)
        self.assertEqual([e["type"] for e in events], ["prompt", "turn_start", "thinking_delta",
                                                        "thinking_end", "text_delta", "turn_end", "result", "acceptance"])
        self.assertEqual(events[-1]["offset"], 44)
        self.assertEqual(next(e for e in events if e["type"] == "thinking_end")["seconds"], 3.0)

    def test_live_cursor_resumes_mid_line_and_mid_block(self):
        first = {"type": "stream_event", "event": {"type": "content_block_start", "index": 0,
                 "content_block": {"type": "thinking", "thinking": ""}}}
        second = {"type": "stream_event", "event": {"type": "content_block_delta", "index": 0,
                  "delta": {"type": "thinking_delta", "thinking": "live"}}}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root / "run.jsonl"
            line1 = json.dumps(first) + "\n"; line2 = json.dumps(second) + "\n"
            path.write_bytes((line1 + line2[:15]).encode("utf-8"))
            state = console.ConsoleState(root, root); cursor = "a" * 32
            one = state.agent_events(path, 0, cursor, "Actual prompt")
            self.assertEqual([e["type"] for e in one["events"]], ["prompt", "turn_start"])
            self.assertEqual(one["offset"], len(line1.encode()))
            self.assertTrue(one["more"])
            with path.open("ab") as handle:
                handle.write(line2[15:].encode("utf-8"))
            two = state.agent_events(path, one["offset"], cursor)
            self.assertEqual([e["type"] for e in two["events"]], ["thinking_delta"])
            self.assertEqual(two["events"][0]["text"], "live")
            self.assertEqual(two["offset"], path.stat().st_size)
            with self.assertRaisesRegex(ValueError, "offset disagree"):
                state.agent_events(path, one["offset"], cursor)

    def test_request_cursor_keeps_thought_timing_across_polls(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); path = root / "requests-20260925.jsonl"
            first = [{"type": "request_start", "request_id": "r", "user": "prompt",
                      "time": "2026-09-24T10:00:00Z"},
                     {"type": "reasoning", "request_id": "r", "text": "working"}]
            path.write_bytes(("\n".join(json.dumps(row) for row in first) + "\n").encode())
            state = console.ConsoleState(root, root); cursor = "b" * 32
            one = state.request_events(path, 0, cursor)
            self.assertEqual([event["type"] for event in one["events"]],
                             ["prompt", "turn_start", "thinking_delta"])
            later = [{"type": "answer", "request_id": "r", "text": "done",
                      "time": "2026-09-24T10:00:07Z"},
                     {"type": "request_end", "request_id": "r", "time": "2026-09-24T10:00:08Z",
                      "timings": {"wall_seconds": 8}}]
            with path.open("ab") as handle:
                handle.write(("\n".join(json.dumps(row) for row in later) + "\n").encode())
            two = state.request_events(path, one["offset"], cursor)
            self.assertEqual([event["type"] for event in two["events"]],
                             ["thinking_end", "text_delta", "turn_end", "result"])
            self.assertEqual(two["events"][0]["seconds"], 7.0)
            self.assertEqual(two["events"][-1]["duration_ms"], 8000)

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
