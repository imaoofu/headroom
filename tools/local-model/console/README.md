# Local Model Console

Double-click `OPEN-CONSOLE.bat`. It starts a Python standard-library server bound to
`127.0.0.1:8098` and opens Edge in app mode, or the default browser if Edge is unavailable.
Alternatively run `python tools/local-model/console/server.py` and open
`http://127.0.0.1:8098`. The launcher starts only the console; use **Start model** in the
page if needed. The model uses the exact `ask_local.SERVER_COMMAND` and backend URL.

The console shows chat, Claude requests, agent transcripts, queue results, model health,
GPU memory and utilization. Chat and model start refuse while a measurement is running.
The page pauses viewer polling during a measurement and all polling while hidden. It
never changes GPU settings. **Stop model** terminates only a model process started by
this console instance. A model started by `run_queue.py` or elsewhere remains running.

Chat history is appended to `runs/console/chat-YYYYMMDD.jsonl`. `ask_local.py` writes
full requests, streamed reasoning and answers, and final results to
`runs/console/requests-YYYYMMDD.jsonl`. These files contain complete prompts and context;
`runs/` is ignored by Git. The console serves read-only files from its two configured
roots and writes only under `runs/console/`.

The default roots are `tools/local-model/runs/` and
`C:\Users\Raymond\Documents\local-agent-sandbox`. To change them, start manually:

```text
python tools/local-model/console/server.py --runs-root C:\path\to\runs --sandbox-root C:\path\to\sandbox
```

The server does not start automatically on reboot. To stop it, close its Python process;
the launcher uses a hidden window. Run `python tools/local-model/test_console.py` for
mock-only checks. No live model or sweep is used by the tests.
