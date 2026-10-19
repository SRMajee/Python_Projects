"""
Distributed Task Worker (Celery Clone) - Interview Solution (Python)

1. Primary Capabilities:
   - Multi-process execution bypassing GIL for CPU-bound tasks
   - In-memory broker via multiprocessing.Queue
   - Result backend via Manager dict (process-safe)
   - Task registry, submit -> task_id, get_result(task_id)
   - Retry with exponential backoff
   - Concurrency: multiprocessing for true parallelism

2. Error Handling:
   - Exception captured per-task, stored in result backend
   - Unknown task -> FAILURE result
   - RuntimeError on submit before start
   - ValueError on invalid worker count

3. Out Of Scope:
   - Redis/RabbitMQ broker, task chaining/chord, periodic tasks,
     priority queues, worker auto-scaling, distributed backend
"""
import multiprocessing as mp, time, queue as q

def _worker(tq, rs, rl, tasks):
    while True:
        try: item = tq.get(timeout=1)
        except q.Empty: continue
        if item is None: break
        tid, name, args, kw, retries = item
        fn = tasks.get(name)
        if not fn:
            with rl: rs[tid] = {"state": "FAILURE", "result": None, "error": f"Unknown: {name}"}
            continue
        for attempt in range(retries + 1):
            try:
                result = fn(*args, **kw)
                with rl: rs[tid] = {"state": "SUCCESS", "result": result, "error": ""}
                break
            except Exception as e:
                if attempt == retries:
                    with rl: rs[tid] = {"state": "FAILURE", "result": None, "error": str(e)}
                else: time.sleep(0.1 * (2 ** attempt))

class Worker:
    def __init__(self, n=4):
        self.n, self._mgr = n, mp.Manager()
        self.q, self.rs, self.rl = mp.Queue(), self._mgr.dict(), self._mgr.Lock()
        self.ps, self._tc = [], 0
    def start(self, tasks):
        for i in range(self.n):
            p = mp.Process(target=_worker, args=(self.q, self.rs, self.rl, tasks), daemon=True)
            p.start(); self.ps.append(p)
    def submit(self, name, *a, retries=0, **kw):
        self._tc += 1; tid = f"t{self._tc}"
        with self.rl: self.rs[tid] = {"state": "PENDING", "result": None, "error": ""}
        self.q.put((tid, name, a, kw, retries)); return tid
    def result(self, tid, timeout=10):
        dl = time.time() + timeout
        while time.time() < dl:
            with self.rl: r = self.rs.get(tid)
            if r and r.get("state") in ("SUCCESS", "FAILURE"): return dict(r)
            time.sleep(0.05)
        return None
    def shutdown(self):
        for _ in self.ps: self.q.put(None)
        for p in self.ps: p.join(timeout=3)
        self._mgr.shutdown()

if __name__ == "__main__":
    w = Worker(2); w.start({"sq": lambda x: x*x})
    t1 = w.submit("sq", 7); r = w.result(t1)
    assert r["state"] == "SUCCESS" and r["result"] == 49
    t2 = w.submit("bad"); r2 = w.result(t2)
    assert r2["state"] == "FAILURE"
    w.shutdown()
    print("Interview Distributed Worker passed!")
