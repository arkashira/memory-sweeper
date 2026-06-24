# memory-sweeper

`memory-sweeper` is a tiny static analysis tool that scans a piece of Python source code
and reports possible resource leaks (e.g., files opened without being closed).  
For each detected leak it provides:

* **Severity** – `high` for unclosed files, `medium` for other resources (e.g., sockets).  
* **Message** – a short description of the problem.  
* **Suggestion** – a concrete code snippet or refactor step to fix the issue.

The implementation lives in `src/memory_sweeper.py` and is completely based on the
standard library (`ast`, `dataclasses`, …).  

Run the test suite with:
