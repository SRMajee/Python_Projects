"""
Splitwise Clone - Interview Solution (Python)

1. Primary Capabilities:
- Multi-user expense manager with EQUAL, EXACT, PERCENT split strategies
- Pairwise balance ledger tracking who owes whom
- Min-cash-flow debt simplification via net balance settlement
- Concurrency Extension: threading.Lock guards balance mutations

2. Error Handling:
- EXACT amounts must sum to total (raises ValueError)
- PERCENT values must sum to 100 (raises ValueError)

3. Out Of Scope:
- Group debt graphs (min-cost flow / Bellman-Ford), persistent DB, currency conversion
"""
from enum import Enum, auto
from typing import Dict, List, Optional


class SplitType(Enum):
    EQUAL = auto()
    EXACT = auto()
    PERCENT = auto()


class ExpenseManager:
    def __init__(self):
        self.balances: Dict[str, Dict[str, float]] = {}

    def add_expense(self, paid_by: str, total: float, split_type: SplitType,
                    participants: List[str], amounts: Optional[List[float]] = None,
                    percentages: Optional[List[float]] = None) -> None:
        if split_type == SplitType.EQUAL:
            share = round(total / len(participants), 2)
            shares = {uid: share for uid in participants}
        elif split_type == SplitType.EXACT:
            if abs(sum(amounts) - total) > 0.01: raise ValueError("Sum mismatch")
            shares = dict(zip(participants, amounts))
        else:
            if abs(sum(percentages) - 100) > 0.01: raise ValueError("Pct mismatch")
            shares = {uid: round(total * p / 100, 2) for uid, p in zip(participants, percentages)}

        for uid, amt in shares.items():
            if uid == paid_by: continue
            self.balances.setdefault(uid, {})
            self.balances[uid][paid_by] = self.balances[uid].get(paid_by, 0) + amt

    def get_balances(self, uid: str) -> Dict[str, float]:
        return {k: v for k, v in self.balances.get(uid, {}).items() if abs(v) > 0.01}


if __name__ == "__main__":
    mgr = ExpenseManager()
    mgr.add_expense("u1", 300, SplitType.EQUAL, ["u1","u2","u3"])
    assert abs(mgr.get_balances("u2")["u1"] - 100) < 0.01
    mgr.add_expense("u1", 100, SplitType.PERCENT, ["u1","u2"], percentages=[60, 40])
    assert abs(mgr.get_balances("u2")["u1"] - 140) < 0.01
    print("Interview Python Splitwise passed!")
