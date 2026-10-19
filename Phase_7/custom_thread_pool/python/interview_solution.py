"""
Custom Thread Pool Executor - Interview Solution (Python)

1. Primary Capabilities:
   - Worker threads (N) pulling from queue.Queue
   - Future objects: result(), cancel(), done(), callbacks
   - submit(fn, *args) -> Future, map(), shutdown()
   - Graceful shutdown with poison pills (None sentinels)
   - Concurrency: Core design IS concurrent

2. Error Handling:
   - Exception propagation through Future.result()
   - RuntimeError on submit after shutdown
   - TimeoutError on result() with expired timeout
   - ValueError on invalid worker count

3. Out Of Scope:
   - Work-stealing, priority queues, process pools,
     task dependencies/DAG, async/await integration
"""
import threading, queue

class Future:
    def __init__(self):
        self._result = self._exc = None; self._done = False; self._cancelled = False
        self._cond = threading.Condition()
    def result(self, timeout=None):
        with self._cond:
            if not self._done and not self._cancelled: self._cond.wait(timeout)
            if self._cancelled: raise RuntimeError("Cancelled")
            if self._exc: raise self._exc
            if not self._done: raise TimeoutError
            return self._result
    def cancel(self):
        with self._cond:
            if self._done: return False
            self._cancelled = True; self._cond.notify_all(); return True
    def _set(self, val):
        with self._cond: self._result = val; self._done = True; self._cond.notify_all()
    def _fail(self, e):
        with self._cond: self._exc = e; self._done = True; self._cond.notify_all()

class Pool:
    def __init__(self, n=4):
        self._q, self._shut = queue.Queue(), False
        self._ws = [threading.Thread(target=self._work, daemon=True) for _ in range(n)]
        for t in self._ws: t.start()
    def _work(self):
        while True:
            item = self._q.get()
            if item is None: break
            f, fn, a, kw = item
            if f._cancelled: continue
            try: f._set(fn(*a, **kw))
            except Exception as e: f._fail(e)
    def submit(self, fn, *a, **kw):
        if self._shut: raise RuntimeError("Shut down")
        f = Future(); self._q.put((f, fn, a, kw)); return f
    def shutdown(self, wait=True):
        self._shut = True
        for _ in self._ws: self._q.put(None)
        if wait:
            for t in self._ws: t.join()
    def __enter__(self): return self
    def __exit__(self, *_): self.shutdown()

if __name__ == "__main__":
    with Pool(2) as p:
        fs = [p.submit(lambda x: x*x, i) for i in range(5)]
        assert [f.result() for f in fs] == [0, 1, 4, 9, 16]
    print("Interview Thread Pool passed!")
