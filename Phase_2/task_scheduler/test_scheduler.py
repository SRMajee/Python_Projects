"""Comprehensive unit test suite for DAG Task Scheduler."""

import time
import unittest
from scheduler import (
    ConcurrentStrategy,
    CycleDetectedError,
    ExecutionStrategy,
    HistoryObserver,
    MetricsObserver,
    SequentialStrategy,
    Task,
    TaskEvent,
    TaskEventType,
    TaskObserver,
    TaskScheduler,
    TaskStatus,
)


class TestDAGValidationAndTopologicalOrder(unittest.TestCase):
    """Tests for DAG dependency resolution, cycle detection, and topological sorting."""

    def test_linear_topological_order(self) -> None:
        scheduler = TaskScheduler()
        execution_log = []

        scheduler.add_task(Task("step_1", lambda: execution_log.append("step_1")))
        scheduler.add_task(Task("step_2", lambda: execution_log.append("step_2"), dependencies={"step_1"}))
        scheduler.add_task(Task("step_3", lambda: execution_log.append("step_3"), dependencies={"step_2"}))

        order = scheduler.validate_dag()
        self.assertEqual(order, ["step_1", "step_2", "step_3"])

        scheduler.run()
        self.assertEqual(execution_log, ["step_1", "step_2", "step_3"])

    def test_diamond_dependency_graph(self) -> None:
        scheduler = TaskScheduler()
        execution_log = []

        # Graph: A -> B, A -> C, (B, C) -> D
        scheduler.add_task(Task("A", lambda: execution_log.append("A")))
        scheduler.add_task(Task("B", lambda: execution_log.append("B"), dependencies={"A"}))
        scheduler.add_task(Task("C", lambda: execution_log.append("C"), dependencies={"A"}))
        scheduler.add_task(Task("D", lambda: execution_log.append("D"), dependencies={"B", "C"}))

        scheduler.run()
        self.assertEqual(execution_log[0], "A")
        self.assertEqual(set(execution_log[1:3]), {"B", "C"})
        self.assertEqual(execution_log[3], "D")

    def test_cycle_detection_direct(self) -> None:
        scheduler = TaskScheduler()
        scheduler.add_task(Task("A", lambda: None, dependencies={"B"}))
        scheduler.add_task(Task("B", lambda: None, dependencies={"A"}))

        with self.assertRaises(CycleDetectedError):
            scheduler.run()

    def test_cycle_detection_indirect(self) -> None:
        scheduler = TaskScheduler()
        scheduler.add_task(Task("A", lambda: None, dependencies={"C"}))
        scheduler.add_task(Task("B", lambda: None, dependencies={"A"}))
        scheduler.add_task(Task("C", lambda: None, dependencies={"B"}))

        with self.assertRaises(CycleDetectedError):
            scheduler.validate_dag()

    def test_missing_dependency_raises_key_error(self) -> None:
        scheduler = TaskScheduler()
        scheduler.add_task(Task("A", lambda: None, dependencies={"ghost_task"}))

        with self.assertRaises(KeyError):
            scheduler.run()

    def test_duplicate_task_registration_raises_error(self) -> None:
        scheduler = TaskScheduler()
        scheduler.add_task(Task("A", lambda: 1))
        with self.assertRaises(ValueError):
            scheduler.add_task(Task("A", lambda: 2))


class TestPriorityScheduling(unittest.TestCase):
    """Tests priority resolution when multiple tasks are ready concurrently."""

    def test_higher_priority_executes_first(self) -> None:
        scheduler = TaskScheduler()
        execution_order = []

        scheduler.add_task(Task("root", lambda: execution_order.append("root")))
        scheduler.add_task(Task("low_prio", lambda: execution_order.append("low"), dependencies={"root"}, priority=1))
        scheduler.add_task(Task("high_prio", lambda: execution_order.append("high"), dependencies={"root"}, priority=10))
        scheduler.add_task(Task("mid_prio", lambda: execution_order.append("mid"), dependencies={"root"}, priority=5))

        scheduler.run()
        self.assertEqual(execution_order, ["root", "high", "mid", "low"])


class TestStrategyPattern(unittest.TestCase):
    """Tests execution strategies (Sequential, Concurrent, and custom strategies)."""

    def test_sequential_strategy_results(self) -> None:
        scheduler = TaskScheduler(strategy=SequentialStrategy())
        scheduler.add_task(Task("t1", lambda: 10))
        scheduler.add_task(Task("t2", lambda: 20, dependencies={"t1"}))

        results = scheduler.run()
        self.assertEqual(results, {"t1": 10, "t2": 20})

    def test_concurrent_strategy_parallel_speedup(self) -> None:
        scheduler = TaskScheduler(strategy=ConcurrentStrategy(max_workers=2))

        def slow_action() -> str:
            time.sleep(0.05)
            return "done"

        scheduler.add_task(Task("slow_1", slow_action))
        scheduler.add_task(Task("slow_2", slow_action))

        start = time.time()
        results = scheduler.run()
        duration = time.time() - start

        self.assertEqual(results, {"slow_1": "done", "slow_2": "done"})
        # 2 x 0.05s tasks running concurrently should finish in well under 0.10s
        self.assertLess(duration, 0.09)

    def test_custom_strategy_injection(self) -> None:
        class ReversePriorityStrategy(ExecutionStrategy):
            def execute(self, sched: TaskScheduler) -> dict:
                while True:
                    ready = sched.get_ready_tasks()
                    if not ready:
                        break
                    # Reverse priority: lowest priority first
                    ready.sort(key=lambda t: (t.priority, t.task_id))
                    for t in ready:
                        sched.run_task(t)
                return {t.task_id: t.result for t in sched.tasks.values()}

        order = []
        scheduler = TaskScheduler(strategy=ReversePriorityStrategy())
        scheduler.add_task(Task("t_high", lambda: order.append("high"), priority=100))
        scheduler.add_task(Task("t_low", lambda: order.append("low"), priority=1))

        scheduler.run()
        self.assertEqual(order, ["low", "high"])


class TestObserverPattern(unittest.TestCase):
    """Tests notification dispatch to HistoryObserver, MetricsObserver, and custom observers."""

    def test_history_observer_records_lifecycle(self) -> None:
        scheduler = TaskScheduler()
        history = HistoryObserver()
        scheduler.add_observer(history)

        scheduler.add_task(Task("task_a", lambda: "val_a"))
        scheduler.run()

        event_types = [e.event_type for e in history.events]
        self.assertIn(TaskEventType.WORKFLOW_STARTED, event_types)
        self.assertIn(TaskEventType.TASK_STARTED, event_types)
        self.assertIn(TaskEventType.TASK_COMPLETED, event_types)
        self.assertIn(TaskEventType.WORKFLOW_COMPLETED, event_types)

    def test_metrics_observer_counts_and_timings(self) -> None:
        scheduler = TaskScheduler()
        metrics = MetricsObserver()
        scheduler.add_observer(metrics)

        def fail_action() -> None:
            raise RuntimeError("Intentional failure")

        scheduler.add_task(Task("success_1", lambda: 1))
        scheduler.add_task(Task("fail_1", fail_action))
        scheduler.add_task(Task("skipped_1", lambda: 3, dependencies={"fail_1"}))

        scheduler.run()
        self.assertEqual(metrics.counts[TaskStatus.COMPLETED], 1)
        self.assertEqual(metrics.counts[TaskStatus.FAILED], 1)
        self.assertEqual(metrics.counts[TaskStatus.SKIPPED], 1)
        self.assertGreaterEqual(metrics.total_duration, 0.0)

    def test_remove_observer(self) -> None:
        scheduler = TaskScheduler()
        history = HistoryObserver()
        scheduler.add_observer(history)
        scheduler.remove_observer(history)

        scheduler.add_task(Task("t1", lambda: "ok"))
        scheduler.run()
        self.assertEqual(len(history.events), 0)


class TestFailureCascadeAndRetries(unittest.TestCase):
    """Tests failure propagation, downstream skipping, and retry resilience."""

    def test_failure_cascades_skip_downstream(self) -> None:
        scheduler = TaskScheduler()

        def raise_err() -> None:
            raise RuntimeError("Task failure")

        scheduler.add_task(Task("failing_task", raise_err))
        scheduler.add_task(Task("dependent_child", lambda: "never", dependencies={"failing_task"}))
        scheduler.add_task(Task("dependent_grandchild", lambda: "never", dependencies={"dependent_child"}))
        scheduler.add_task(Task("independent_task", lambda: "success"))

        results = scheduler.run()

        self.assertEqual(scheduler.tasks["failing_task"].status, TaskStatus.FAILED)
        self.assertEqual(scheduler.tasks["dependent_child"].status, TaskStatus.SKIPPED)
        self.assertEqual(scheduler.tasks["dependent_grandchild"].status, TaskStatus.SKIPPED)
        self.assertEqual(scheduler.tasks["independent_task"].status, TaskStatus.COMPLETED)
        self.assertEqual(results["independent_task"], "success")

    def test_retry_eventual_success(self) -> None:
        scheduler = TaskScheduler()
        attempts = 0

        def flaky_action() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Transient error")
            return "recovered"

        task = Task("flaky", flaky_action, max_retries=3)
        scheduler.add_task(task)
        scheduler.run()

        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.result, "recovered")
        self.assertEqual(task.retry_count, 2)

    def test_retry_exhaustion_marks_failed(self) -> None:
        scheduler = TaskScheduler()
        def fail_forever() -> None:
            raise RuntimeError("Persistent failure")

        task = Task("always_fails", fail_forever, max_retries=2)
        scheduler.add_task(task)
        scheduler.run()

        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(task.retry_count, 2)
        self.assertIsInstance(task.error, RuntimeError)


class TestCronLikePeriodicExecution(unittest.TestCase):
    """Tests cron-like periodic evaluation and interval triggering."""

    def test_tick_triggers_due_tasks(self) -> None:
        scheduler = TaskScheduler()
        run_count = 0

        scheduler.add_task(Task("heartbeat", lambda: run_count + 1, interval=10.0))

        # Initial tick at t=100 (never run before -> due)
        triggered = scheduler.tick(current_time=100.0)
        self.assertEqual(triggered, ["heartbeat"])
        self.assertEqual(scheduler.tasks["heartbeat"].status, TaskStatus.COMPLETED)

        # Tick at t=105 (only 5s elapsed < 10s interval -> not due)
        triggered_early = scheduler.tick(current_time=105.0)
        self.assertEqual(triggered_early, [])

        # Tick at t=111 (>10s elapsed -> due again)
        triggered_again = scheduler.tick(current_time=111.0)
        self.assertEqual(triggered_again, ["heartbeat"])


if __name__ == "__main__":
    unittest.main()
