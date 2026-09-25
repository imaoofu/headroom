"""Parse llama.cpp's OpenAI-compatible SSE without a network dependency."""

import json


def iter_sse_events(lines):
    """Yield normalized events from byte or text SSE lines."""
    for raw in lines:
        line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        line = line.strip()
        if not line or line.startswith(":") or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if data == "[DONE]":
            yield {"type": "done"}
            return
        try:
            chunk = json.loads(data)
        except json.JSONDecodeError as error:
            raise ValueError(f"Malformed SSE data: {error}") from error
        if chunk.get("error"):
            raise RuntimeError(f"llama-server stream error: {chunk['error']}")
        for choice in chunk.get("choices", []):
            delta = choice.get("delta") or {}
            if delta.get("reasoning_content"):
                yield {"type": "reasoning", "text": delta["reasoning_content"]}
            if delta.get("content"):
                yield {"type": "answer", "text": delta["content"]}
            if delta.get("tool_calls"):
                yield {"type": "tool_calls", "value": delta["tool_calls"]}
            if choice.get("finish_reason") is not None:
                yield {"type": "finish", "reason": choice["finish_reason"]}
        if chunk.get("usage") or chunk.get("timings"):
            yield {"type": "stats", "usage": chunk.get("usage") or {},
                   "timings": chunk.get("timings") or {}}
