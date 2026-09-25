"""Pure, incremental Claude Code transcript assembly for the local console."""

from copy import deepcopy
from datetime import datetime
import json


def initial_agent_state():
    return {"turn": None, "next_turn": 1, "prompt_seen": False, "result_seen": False}


def _seconds_between(first, last):
    if not first or not last:
        return None
    try:
        start = datetime.fromisoformat(first.replace("Z", "+00:00"))
        end = datetime.fromisoformat(last.replace("Z", "+00:00"))
        return round(max(0, (end - start).total_seconds()), 1)
    except (ValueError, TypeError):
        return None


def _content_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(str(block.get("text") or block.get("content") or json.dumps(block, ensure_ascii=False)))
        return "\n".join(parts)
    return json.dumps(content, ensure_ascii=False)


def assemble_agent_lines(lines, previous=None):
    """Return (events, new state) for (ending-byte-offset, JSONL text) pairs.

    Neither the input state nor the lines are modified. Each event carries the byte offset
    of the complete line that produced it, so a caller can resume without replaying text.
    """
    state = deepcopy(previous) if previous is not None else initial_agent_state()
    events = []
    retries = progress = 0
    last_offset = lines[-1][0] if lines else 0

    def emit(kind, offset, **values):
        events.append({"type": kind, "offset": offset, **values})

    def ensure_turn(offset, message_id=None, timestamp=None):
        turn = state["turn"]
        if turn is None or (message_id and turn["message_id"] and message_id != turn["message_id"]) or (turn["closed"] and not message_id):
            turn = {"id": f"turn-{state['next_turn']}", "message_id": message_id,
                    "blocks": {}, "whole_indices": [], "closed": False, "started_at": timestamp}
            state["next_turn"] += 1
            state["turn"] = turn
            emit("turn_start", offset, turn_id=turn["id"])
        elif message_id and not turn["message_id"]:
            turn["message_id"] = message_id
        return turn

    def block_for(turn, index, kind):
        key = str(index)
        if key not in turn["blocks"]:
            turn["blocks"][key] = {"kind": kind, "text": "", "tool_id": None,
                                    "name": None, "thinking_at": None, "thinking_done": False}
        return turn["blocks"][key]

    def append_text(turn, index, kind, value, offset, timestamp, replace=False):
        block = block_for(turn, index, kind)
        if kind == "thinking" and block["thinking_at"] is None:
            block["thinking_at"] = timestamp
        block["text"] = value if replace else block["text"] + value
        event_type = {"thinking": "thinking_delta", "text": "text_delta",
                      "tool_use": "tool_input_delta"}[kind]
        emit(event_type, offset, turn_id=turn["id"], block=index, text=value, replace=replace)

    def reconcile(turn, index, kind, final, offset, timestamp):
        block = block_for(turn, index, kind)
        current = block["text"]
        if kind == "tool_use":
            try:
                if json.loads(current) == final:
                    return
            except (ValueError, TypeError):
                pass
            final = json.dumps(final, ensure_ascii=False)
        if final == current:
            return
        if isinstance(final, str) and final.startswith(current):
            append_text(turn, index, kind, final[len(current):], offset, timestamp)
        else:
            append_text(turn, index, kind, final, offset, timestamp, replace=True)

    def whole_index(turn, block, ordinal):
        """Claude may emit each finished block as its own assistant JSONL row."""
        kind = block.get("type")
        preferred = turn["blocks"].get(str(ordinal))
        if preferred and preferred["kind"] == kind and ordinal not in turn["whole_indices"]:
            return ordinal
        for key, existing in turn["blocks"].items():
            index = int(key)
            if existing["kind"] != kind or index in turn["whole_indices"]:
                continue
            if kind != "tool_use" or not existing["tool_id"] or existing["tool_id"] == block.get("id"):
                return index
        index = ordinal
        while str(index) in turn["blocks"]:
            index += 1
        return index

    def finish_thinking(turn, index, offset, timestamp):
        block = turn["blocks"].get(str(index))
        if block and block["kind"] == "thinking" and not block["thinking_done"]:
            block["thinking_done"] = True
            emit("thinking_end", offset, turn_id=turn["id"], block=index,
                 seconds=_seconds_between(block["thinking_at"], timestamp))

    for offset, line in lines:
        try:
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError("JSONL item is not an object")
        except (json.JSONDecodeError, ValueError) as error:
            emit("malformed", offset, text=line, error=str(error))
            continue
        kind, subtype = item.get("type"), item.get("subtype")
        timestamp = item.get("timestamp")
        if kind == "system":
            if subtype == "init":
                emit("init", offset, model=item.get("model"), cwd=item.get("cwd"),
                     tool_count=len(item.get("tools") or []))
            elif subtype == "api_retry":
                retries += 1
            else:
                progress += 1
            continue
        if kind == "result":
            turn = state["turn"]
            if turn and not turn["closed"]:
                for index in turn["blocks"]:
                    finish_thinking(turn, int(index), offset, timestamp)
                turn["closed"] = True
                emit("turn_end", offset, turn_id=turn["id"])
            state["result_seen"] = True
            emit("result", offset, subtype=subtype, is_error=bool(item.get("is_error")),
                 turns=item.get("num_turns"), duration_ms=item.get("duration_ms"),
                 text=item.get("result") or "")
            continue
        if kind == "stream_event":
            event = item.get("event") or {}
            event_type = event.get("type")
            if event_type == "message_start":
                message = event.get("message") or {}
                if message.get("role", "assistant") == "assistant":
                    ensure_turn(offset, message.get("id") or item.get("message_id"), timestamp)
            elif event_type == "content_block_start":
                turn = ensure_turn(offset, item.get("message_id"), timestamp)
                index = event.get("index", 0)
                content = event.get("content_block") or {}
                block_type = content.get("type")
                block = block_for(turn, index, block_type)
                if block_type == "tool_use":
                    block["tool_id"], block["name"] = content.get("id"), content.get("name")
                    emit("tool_start", offset, turn_id=turn["id"], block=index,
                         tool_id=block["tool_id"], name=block["name"])
                elif block_type in ("thinking", "text"):
                    initial = content.get("thinking" if block_type == "thinking" else "text") or ""
                    if initial:
                        append_text(turn, index, block_type, initial, offset, timestamp)
            elif event_type == "content_block_delta":
                turn = ensure_turn(offset, item.get("message_id"), timestamp)
                index = event.get("index", 0)
                delta = event.get("delta") or {}
                delta_type = delta.get("type")
                if delta_type == "thinking_delta":
                    append_text(turn, index, "thinking", delta.get("thinking") or "", offset, timestamp)
                elif delta_type == "text_delta":
                    append_text(turn, index, "text", delta.get("text") or "", offset, timestamp)
                elif delta_type == "input_json_delta":
                    append_text(turn, index, "tool_use", delta.get("partial_json") or "", offset, timestamp)
            elif event_type == "content_block_stop":
                turn = state["turn"]
                if turn:
                    finish_thinking(turn, event.get("index", 0), offset, timestamp)
            elif event_type == "message_stop":
                turn = state["turn"]
                if turn and not turn["closed"]:
                    for index in turn["blocks"]:
                        finish_thinking(turn, int(index), offset, timestamp)
                    turn["closed"] = True
                    emit("turn_end", offset, turn_id=turn["id"])
            continue
        if kind == "user":
            blocks = (item.get("message") or {}).get("content") or []
            if isinstance(blocks, str):
                blocks = [{"type": "text", "text": blocks}]
            prompt = []
            for block in blocks:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_result":
                    emit("tool_result", offset, tool_id=block.get("tool_use_id"),
                         text=_content_text(block.get("content")),
                         is_error=bool(block.get("is_error")))
                elif block.get("type") == "text":
                    prompt.append(block.get("text") or "")
            if prompt and not state["prompt_seen"]:
                state["prompt_seen"] = True
                emit("prompt", offset, text="\n".join(prompt))
            continue
        if kind == "assistant":
            message = item.get("message") or {}
            message_id = message.get("id")
            turn = ensure_turn(offset, message_id, timestamp)
            blocks = message.get("content") or []
            if isinstance(blocks, str):
                blocks = [{"type": "text", "text": blocks}]
            for ordinal, block in enumerate(blocks):
                if not isinstance(block, dict):
                    continue
                index = whole_index(turn, block, ordinal)
                turn["whole_indices"].append(index)
                block_type = block.get("type")
                if block_type in ("thinking", "text"):
                    final = block.get("thinking" if block_type == "thinking" else "text") or ""
                    reconcile(turn, index, block_type, final, offset, timestamp)
                    if block_type == "thinking":
                        finish_thinking(turn, index, offset, timestamp)
                elif block_type == "tool_use":
                    existing = turn["blocks"].get(str(index))
                    if not existing or not existing["tool_id"]:
                        tool = block_for(turn, index, "tool_use")
                        tool["tool_id"], tool["name"] = block.get("id"), block.get("name")
                        emit("tool_start", offset, turn_id=turn["id"], block=index,
                             tool_id=tool["tool_id"], name=tool["name"])
                    reconcile(turn, index, "tool_use", block.get("input") or {}, offset, timestamp)
            if not turn["closed"]:
                turn["closed"] = True
                emit("turn_end", offset, turn_id=turn["id"])
    if retries:
        emit("retry_count", last_offset, count=retries)
    if progress:
        emit("progress_count", last_offset, count=progress)
    return events, state


def assemble_request_lines(lines, previous=None):
    """Map ask_local's append-only log to the same conversation event vocabulary."""
    state = deepcopy(previous) if previous is not None else {"started": {}, "thinking_done": []}
    events = []
    for offset, line in lines:
        try:
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError("JSONL item is not an object")
        except (json.JSONDecodeError, ValueError) as error:
            events.append({"type": "malformed", "offset": offset, "text": line, "error": str(error)})
            continue
        kind, ident = item.get("type"), item.get("request_id")
        if not ident:
            continue
        base = {"request_id": ident, "offset": offset}
        if kind == "request_start":
            state["started"][ident] = item.get("time")
            events.append({"type": "prompt", **base, "time": item.get("time"),
                           "text": item.get("user") or "", "system": item.get("system") or "",
                           "job": item.get("job"), "attempt": item.get("attempt"),
                           "queue_name": item.get("queue_name"), "spec_path": item.get("spec_path")})
            events.append({"type": "turn_start", **base, "turn_id": ident})
        elif kind in ("reasoning", "answer"):
            if kind == "answer" and ident not in state["thinking_done"]:
                state["thinking_done"].append(ident)
                events.append({"type": "thinking_end", **base, "turn_id": ident, "block": 0,
                               "seconds": _seconds_between(state["started"].get(ident), item.get("time"))})
            events.append({"type": "thinking_delta" if kind == "reasoning" else "text_delta",
                           **base, "turn_id": ident, "block": 0 if kind == "reasoning" else 1,
                           "text": item.get("text") or ""})
        elif kind == "request_end":
            if ident not in state["thinking_done"]:
                events.append({"type": "thinking_end", **base, "turn_id": ident, "block": 0,
                               "seconds": _seconds_between(state["started"].get(ident), item.get("time"))})
            events.append({"type": "turn_end", **base, "turn_id": ident})
            events.append({"type": "result", **base, "is_error": bool(item.get("error")),
                           "text": item.get("error") or "", "done_reason": item.get("done_reason"),
                           "timings": item.get("timings") or {}, "output_path": item.get("output_path"),
                           "duration_ms": round(((item.get("timings") or {}).get("wall_seconds") or 0) * 1000)})
            state["started"].pop(ident, None)
            if ident in state["thinking_done"]:
                state["thinking_done"].remove(ident)
        elif kind == "accepted":
            events.append({"type": "acceptance", **base, "verdict": item.get("verdict"),
                           "report": item.get("accept_report")})
    return events, state
