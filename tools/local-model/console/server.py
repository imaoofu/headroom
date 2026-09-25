"""Loopback-only local model console. No GPU settings or measurement commands."""

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import ask_local
import run_queue
from streaming import iter_sse_events
from assembly import assemble_agent_lines, assemble_request_lines, initial_agent_state

DEFAULT_RUNS = HERE.parent / "runs"
DEFAULT_SANDBOX = Path(r"C:\Users\Raymond\Documents\local-agent-sandbox")
MODEL_URL = ask_local.BACKENDS["llamacpp"]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def append_chat(runs_root, entry):
    directory = runs_root / "console"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"chat-{datetime.now(timezone.utc):%Y%m%d}.jsonl"
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def allowed_file(roots, root_name, relative):
    if root_name not in roots or not relative or Path(relative).is_absolute():
        raise ValueError("Unlisted root or invalid path")
    root = roots[root_name].resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError as error:
        raise ValueError("Path escapes its allowed root") from error
    if not target.is_file():
        raise FileNotFoundError(target)
    return target


def list_transcripts(roots):
    found = []
    for name, root in roots.items():
        if root.exists():
            for path in root.rglob("*.jsonl"):
                if path.is_file():
                    found.append({"root": name, "path": path.relative_to(root).as_posix(),  # "/" on Windows too; the page matches on it
                                  "bytes": path.stat().st_size, "mtime": path.stat().st_mtime})
    return sorted(found, key=lambda row: (row["root"], row["path"]))


def parse_transcript_line(line):
    try:
        item = json.loads(line)
    except json.JSONDecodeError as error:
        return {"kind": "malformed", "text": line, "error": str(error)}
    kind, subtype = item.get("type"), item.get("subtype")
    if kind == "system" and subtype == "init":
        return {"kind": "init", "model": item.get("model"),
                "tool_count": len(item.get("tools") or []), "cwd": item.get("cwd")}
    if kind == "system" and subtype == "api_retry":
        return {"kind": "api_retry"}
    if kind == "system":
        # Claude Code streams a thinking_tokens progress event per chunk; the first live
        # transcript (2026-09-24) held 10,047 of them around 42 real events. Count, do not list.
        return {"kind": "progress", "subtype": subtype}
    if kind == "result":
        return {"kind": "result", "subtype": subtype, "is_error": bool(item.get("is_error")),
                "turns": item.get("num_turns"), "duration_ms": item.get("duration_ms"),
                "text": item.get("result") or ""}
    blocks = (item.get("message") or {}).get("content") or []
    if isinstance(blocks, str):
        blocks = [{"type": "text", "text": blocks}]
    output = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type in ("thinking", "text"):
            output.append({"kind": block_type, "text": block.get("thinking") if block_type == "thinking" else block.get("text", "")})
        elif block_type == "tool_use":
            output.append({"kind": "tool_use", "name": block.get("name"),
                           "input": block.get("input")})
        elif block_type == "tool_result":
            content = block.get("content")
            output.append({"kind": "tool_result", "tool_use_id": block.get("tool_use_id"),
                           "text": content if isinstance(content, str) else json.dumps(content, ensure_ascii=False),
                           "is_error": block.get("is_error", False)})
    return output or {"kind": "other", "type": kind, "subtype": subtype}


def tail_jsonl(path, offset, limit=1024 * 1024, parser=None):
    size = path.stat().st_size
    if offset < 0 or offset > size:
        offset = 0
    with path.open("rb") as handle:
        handle.seek(offset)
        data = handle.read(limit)
    last_line = data.rfind(b"\n")
    if last_line < 0:
        return {"offset": offset, "events": [], "more": size > offset}
    complete = data[:last_line + 1]
    events = []
    for raw in complete.splitlines():
        line = raw.decode("utf-8", errors="replace")
        events.append(parser(line) if parser else parse_jsonl_line(line))
    return {"offset": offset + len(complete), "events": events,
            "more": size > offset + len(complete)}


def read_jsonl_lines(path, offset, limit=1024 * 1024):
    """Read complete UTF-8 JSONL lines and their ending byte offsets."""
    size = path.stat().st_size
    if offset < 0 or offset > size:
        raise ValueError("Offset is outside the file")
    with path.open("rb") as handle:
        handle.seek(offset)
        data = handle.read(limit)
        # A large assistant message can exceed one chunk. Do not strand it forever.
        while data and b"\n" not in data and len(data) < 32 * 1024 * 1024:
            more = handle.read(min(limit, 32 * 1024 * 1024 - len(data)))
            if not more:
                break
            data += more
    if data and b"\n" not in data and len(data) >= 32 * 1024 * 1024:
        raise ValueError("A JSONL line exceeds the 32 MiB viewer limit")
    last = data.rfind(b"\n")
    if last < 0:
        return [], offset, size > offset
    lines = []
    end = offset
    for raw in data[:last + 1].splitlines(keepends=True):
        end += len(raw)
        lines.append((end, raw.rstrip(b"\r\n").decode("utf-8", errors="replace")))
    return lines, end, size > end


def request_files(runs_root):
    directory = runs_root / "console"
    if not directory.exists():
        return []
    return [{"path": path.relative_to(runs_root).as_posix(), "bytes": path.stat().st_size,
             "mtime": path.stat().st_mtime}
            for path in sorted(directory.glob("requests-*.jsonl")) if path.is_file()]


def parse_jsonl_line(line):
    try:
        return json.loads(line)
    except json.JSONDecodeError as error:
        return {"type": "malformed", "text": line, "error": str(error)}


def queue_rows(runs_root):
    rows = []
    for path in runs_root.glob("*/summary.json"):
        try:
            for row in json.loads(path.read_text(encoding="utf-8")):
                status = run_queue.verdict(row)
                def relative(value):
                    if not value:
                        return None
                    target = (run_queue.ROOT / value).resolve()
                    try:
                        return target.relative_to(runs_root.resolve()).as_posix()
                    except ValueError:
                        return None
                rows.append({"queue": path.parent.name, "job": row.get("job"),
                             "attempt": row.get("attempt"), "verdict": status,
                             "seconds": row.get("seconds"), "answer": relative(row.get("output")),
                             "report": relative(row.get("accept_report"))})
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return rows


def any_llama_process():
    """A loading server can exist before /health starts answering."""
    probe = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name = 'llama-server.exe'\" | Select-Object -ExpandProperty ProcessId"],
        capture_output=True, text=True, timeout=10, check=True)
    return bool(probe.stdout.strip())


class ConsoleState:
    def __init__(self, runs_root=DEFAULT_RUNS, sandbox_root=DEFAULT_SANDBOX):
        self.roots = {"runs": Path(runs_root), "sandbox": Path(sandbox_root)}
        self.started = None
        self.log_handle = None
        self.lock = threading.Lock()
        self.cursor_lock = threading.Lock()
        self.agent_cursors = {}
        self.request_cursors = {}

    def agent_events(self, path, offset, cursor, prompt=None):
        if not re.fullmatch(r"[a-f0-9]{32}", cursor):
            raise ValueError("Invalid viewer cursor")
        key = (cursor, str(path.resolve()))
        with self.cursor_lock:
            current = self.agent_cursors.get(key)
            if offset == 0 or current is None:
                if offset != 0:
                    raise ValueError("Viewer cursor expired; restart at offset 0")
                current = {"offset": 0, "assembly": initial_agent_state()}
            elif offset != current["offset"]:
                raise ValueError("Viewer cursor and byte offset disagree")
            lines, new_offset, more = read_jsonl_lines(path, offset)
            events, assembled = assemble_agent_lines(lines, current["assembly"])
            if offset == 0 and prompt:
                events.insert(0, {"type": "prompt", "offset": 0, "text": prompt})
            self.agent_cursors[key] = {"offset": new_offset, "assembly": assembled}
            if len(self.agent_cursors) > 32:
                for oldest in self.agent_cursors:
                    if oldest != key:
                        del self.agent_cursors[oldest]
                        break
            return {"offset": new_offset, "events": events, "more": more,
                    "result_seen": assembled["result_seen"], "mtime": path.stat().st_mtime}

    def request_events(self, path, offset, cursor):
        if not re.fullmatch(r"[a-f0-9]{32}", cursor):
            raise ValueError("Invalid viewer cursor")
        key = (cursor, str(path.resolve()))
        with self.cursor_lock:
            current = self.request_cursors.get(key)
            if offset == 0 or current is None:
                if offset != 0:
                    raise ValueError("Viewer cursor expired; restart at offset 0")
                current = {"offset": 0, "assembly": None}
            elif offset != current["offset"]:
                raise ValueError("Viewer cursor and byte offset disagree")
            lines, new_offset, more = read_jsonl_lines(path, offset)
            events, assembled = assemble_request_lines(lines, current["assembly"])
            self.request_cursors[key] = {"offset": new_offset, "assembly": assembled}
            if len(self.request_cursors) > 32:
                for oldest in self.request_cursors:
                    if oldest != key:
                        del self.request_cursors[oldest]
                        break
            return {"offset": new_offset, "events": events, "more": more,
                    "mtime": path.stat().st_mtime}

    def start_model(self):
        if run_queue.measurement_running():
            raise RuntimeError("Measurement running; model start refused")
        with self.lock:
            if self.started and self.started.poll() is None:
                raise RuntimeError("Console-started model already running")
            if run_queue.measurement_running():
                raise RuntimeError("Measurement running; model start refused")
            try:
                other = run_queue.server_up() or any_llama_process()
            except (OSError, subprocess.SubprocessError) as error:
                raise RuntimeError(f"Cannot verify model process state: {error}") from error
            if other:
                raise RuntimeError("Model server already running outside this console")
            directory = self.roots["runs"] / "console"
            directory.mkdir(parents=True, exist_ok=True)
            self.log_handle = (directory / "llama-server.log").open("a", encoding="utf-8")
            self.started = subprocess.Popen(ask_local.SERVER_COMMAND,
                                            stdout=self.log_handle, stderr=subprocess.STDOUT,
                                            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
            return self.started.pid

    def stop_model(self):
        with self.lock:
            if not self.started or self.started.poll() is not None:
                raise RuntimeError("No console-started model is running")
            pid = self.started.pid
            self.started.terminate()
            self.started = None
            if self.log_handle:
                self.log_handle.close()
                self.log_handle = None
            return pid


def status(state):
    busy = bool(run_queue.measurement_running())
    try:
        with urllib.request.urlopen(MODEL_URL + "/health", timeout=1) as response:
            healthy = response.status == 200
    except (OSError, TimeoutError):
        healthy = False
    try:
        probe = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu",
                                "--format=csv,noheader,nounits"], capture_output=True,
                               text=True, timeout=2, check=True)
        used, total, util = [int(x.strip()) for x in probe.stdout.splitlines()[0].split(",")]
        gpu = {"used_mb": used, "total_mb": total, "util_percent": util}
    except (OSError, ValueError, IndexError, subprocess.SubprocessError):
        gpu = None
    owned = state.started is not None and state.started.poll() is None
    return {"measurement": busy, "model_healthy": healthy, "gpu": gpu,
            "console_started_model": owned}


def chat_stream(state, payload, emit):
    entry = {"time": utc_now(), "request_id": uuid.uuid4().hex,
             "system": str(payload.get("system") or ""), "prompt": str(payload.get("prompt") or ""),
             "temperature": payload.get("temperature", 0.7), "reasoning": "", "answer": "",
             "timings": {}, "usage": {}, "done_reason": None, "error": None}
    try:
        if run_queue.measurement_running():
            raise RuntimeError("Measurement running; chat refused")
        if not entry["prompt"].strip():
            raise ValueError("Prompt is empty")
        temperature = float(entry["temperature"])
        if not 0 <= temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2")
        messages = []
        if entry["system"]:
            messages.append({"role": "system", "content": entry["system"]})
        messages.append({"role": "user", "content": entry["prompt"]})
        body = {"messages": messages, "temperature": temperature, "stream": True,
                "stream_options": {"include_usage": True}}
        request = urllib.request.Request(MODEL_URL + "/v1/chat/completions",
                                         data=json.dumps(body).encode("utf-8"),
                                         headers={"Content-Type": "application/json"})
        done = False
        with urllib.request.urlopen(request, timeout=1800) as response:
            for event in iter_sse_events(response):
                kind = event["type"]
                if kind in ("reasoning", "answer"):
                    entry[kind] += event["text"]
                elif kind == "stats":
                    entry["timings"].update(event["timings"])
                    entry["usage"].update(event["usage"])
                elif kind == "finish":
                    entry["done_reason"] = event["reason"]
                elif kind == "done":
                    done = True
                emit(event)
        if not done or entry["done_reason"] is None:
            raise RuntimeError("Stream ended before completion")
    except Exception as error:
        entry["error"] = str(error)
        emit({"type": "error", "text": str(error)})
    finally:
        append_chat(state.roots["runs"], entry)
        emit({"type": "complete", "entry": entry})
    return entry


def handler_factory(state):
    class Handler(BaseHTTPRequestHandler):
        def send_json(self, value, code=200):
            data = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def query(self):
            return urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)

        def do_GET(self):
            path = urllib.parse.urlsplit(self.path).path
            try:
                if path == "/":
                    data = (HERE / "index.html").read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src data:; base-uri 'none'; form-action 'none'")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                    return
                if path == "/api/status":
                    return self.send_json(status(state))
                if path == "/api/transcripts":
                    return self.send_json(list_transcripts(state.roots))
                if path == "/api/request-files":
                    return self.send_json(request_files(state.roots["runs"]))
                if path == "/api/request-events":
                    query = self.query()
                    rel = query.get("path", [""])[0]
                    if not re.fullmatch(r"console/requests-[0-9]{8}\.jsonl", rel):
                        raise ValueError("Invalid request log path")
                    offset = int(query.get("offset", ["0"])[0])
                    cursor = query.get("cursor", [""])[0]
                    file = allowed_file(state.roots, "runs", rel)
                    return self.send_json(state.request_events(file, offset, cursor))
                if path == "/api/agent-events":
                    query = self.query()
                    root_name = query.get("root", [""])[0]
                    relative = query.get("path", [""])[0]
                    file = allowed_file(state.roots, root_name, relative)
                    offset = int(query.get("offset", ["0"])[0])
                    cursor = query.get("cursor", [""])[0]
                    prompt = None
                    if offset == 0:
                        try:
                            sidecar = allowed_file(state.roots, root_name, relative + ".prompt.txt")
                            if sidecar.stat().st_size > 1024 * 1024:
                                raise ValueError("Prompt sidecar exceeds 1 MiB")
                            prompt = sidecar.read_text(encoding="utf-8-sig")
                        except FileNotFoundError:
                            pass
                    return self.send_json(state.agent_events(file, offset, cursor, prompt))
                if path == "/api/queues":
                    return self.send_json(queue_rows(state.roots["runs"]))
                if path == "/api/tail":
                    query = self.query()
                    root = query.get("root", [""])[0]
                    rel = query.get("path", [""])[0]
                    offset = int(query.get("offset", ["0"])[0])
                    file = allowed_file(state.roots, root, rel)
                    parser = parse_transcript_line if root == "sandbox" or not rel.startswith("console/") else None
                    return self.send_json(tail_jsonl(file, offset, parser=parser))
                if path == "/api/file":
                    query = self.query()
                    file = allowed_file(state.roots, query.get("root", [""])[0],
                                        query.get("path", [""])[0])
                    data = file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain; charset=utf-8")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Content-Disposition", "inline")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                self.send_json({"error": "Not found"}, 404)
            except (ValueError, FileNotFoundError) as error:
                self.send_json({"error": str(error)}, 400)

        def do_POST(self):
            # A separate local web page must not be able to trigger model operations.
            origin = self.headers.get("Origin")
            host = self.headers.get("Host", "")
            if host != "127.0.0.1:8098" or (origin and origin != "http://127.0.0.1:8098"):
                return self.send_json({"error": "Invalid origin"}, 403)
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1024 * 1024:
                return self.send_json({"error": "Request too large"}, 413)
            try:
                payload = json.loads(self.rfile.read(length) or b"{}")
                path = urllib.parse.urlsplit(self.path).path
                if path == "/api/model/start":
                    return self.send_json({"pid": state.start_model()})
                if path == "/api/model/stop":
                    return self.send_json({"pid": state.stop_model()})
                if path == "/api/chat":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    def emit(event):
                        try:
                            self.wfile.write((json.dumps(event, ensure_ascii=False) + "\n").encode("utf-8"))
                            self.wfile.flush()
                        except (BrokenPipeError, ConnectionResetError):
                            pass
                    chat_stream(state, payload, emit)
                    return
                self.send_json({"error": "Not found"}, 404)
            except (ValueError, RuntimeError) as error:
                self.send_json({"error": str(error)}, 400)

    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS)
    parser.add_argument("--sandbox-root", type=Path, default=DEFAULT_SANDBOX)
    args = parser.parse_args()
    state = ConsoleState(args.runs_root, args.sandbox_root)
    server = ThreadingHTTPServer(("127.0.0.1", 8098), handler_factory(state))
    print("Local Model Console: http://127.0.0.1:8098", flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
