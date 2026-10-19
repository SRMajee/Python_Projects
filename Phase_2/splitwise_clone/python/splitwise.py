"""
Splitwise Clone - Complete Solution (Python)
Supports EQUAL, EXACT, PERCENT splits with pairwise balance tracking.
Concurrency: threading.Lock guards all balance mutations.
"""
import threading
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional


class SplitType(Enum):
    EQUAL = auto()
    EXACT = auto()
    PERCENT = auto()


@dataclass
class User:
    user_id: str
    name: str


@dataclass
class Split:
    user_id: str
    amount: float = 0.0


class ExpenseManager:
    def __init__(self) -> None:
        self.users: Dict[str, User] = {}
        self.balances: Dict[str, Dict[str, float]] = {}
        self._lock = threading.Lock()

    def add_user(self, user: User) -> None:
        self.users[user.user_id] = user
        self.balances.setdefault(user.user_id, {})

    def add_expense(
        self,
        paid_by: str,
        total: float,
        split_type: SplitType,
        participants: List[str],
        amounts: Optional[List[float]] = None,
        percentages: Optional[List[float]] = None,
    ) -> None:
        splits = self._compute_splits(total, split_type, participants, amounts, percentages)
        with self._lock:
            for uid, share in splits.items():
                if uid == paid_by:
                    continue
                self.balances.setdefault(uid, {})
                self.balances.setdefault(paid_by, {})
                self.balances[uid][paid_by] = self.balances[uid].get(paid_by, 0.0) + share
                self.balances[paid_by][uid] = self.balances[paid_by].get(uid, 0.0) - share

    def _compute_splits(
        self, total: float, split_type: SplitType,
        participants: List[str],
        amounts: Optional[List[float]],
        percentages: Optional[List[float]],
    ) -> Dict[str, float]:
        if split_type == SplitType.EQUAL:
            share = round(total / len(participants), 2)
            return {uid: share for uid in participants}
        elif split_type == SplitType.EXACT:
            if not amounts or abs(sum(amounts) - total) > 0.01:
                raise ValueError("Exact amounts must sum to total")
            return dict(zip(participants, amounts))
        elif split_type == SplitType.PERCENT:
            if not percentages or abs(sum(percentages) - 100.0) > 0.01:
                raise ValueError("Percentages must sum to 100")
            return {uid: round(total * pct / 100.0, 2) for uid, pct in zip(participants, percentages)}
        raise ValueError(f"Unknown split type: {split_type}")

    def get_balances(self, user_id: str) -> Dict[str, float]:
        return {k: v for k, v in self.balances.get(user_id, {}).items() if abs(v) > 0.01}

    def simplify_debts(self) -> List[tuple]:
        """Min-cash-flow debt simplification using net balances."""
        net: Dict[str, float] = {}
        for uid in self.users:
            total = sum(self.balances.get(uid, {}).values())
            if abs(total) > 0.01:
                net[uid] = total
        creditors = sorted([(v, k) for k, v in net.items() if v < 0])
        debtors = sorted([(v, k) for k, v in net.items() if v > 0], reverse=True)
        result = []
        i = j = 0
        while i < len(debtors) and j < len(creditors):
            debt_amt, debtor = debtors[i]
            cred_amt, creditor = creditors[j]
            settle = min(debt_amt, -cred_amt)
            result.append((debtor, creditor, round(settle, 2)))
            debtors[i] = (debt_amt - settle, debtor)
            creditors[j] = (cred_amt + settle, creditor)
            if debtors[i][0] < 0.01:
                i += 1
            if creditors[j][0] > -0.01:
                j += 1
        return result


if __name__ == "__main__":
    mgr = ExpenseManager()
    for uid, name in [("u1","Alice"),("u2","Bob"),("u3","Charlie")]:
        mgr.add_user(User(uid, name))

    mgr.add_expense("u1", 300.0, SplitType.EQUAL, ["u1","u2","u3"])
    assert abs(mgr.get_balances("u2")["u1"] - 100.0) < 0.01

    mgr.add_expense("u2", 90.0, SplitType.EXACT, ["u1","u2","u3"], amounts=[30.0, 30.0, 30.0])
    mgr.add_expense("u3", 100.0, SplitType.PERCENT, ["u1","u2","u3"], percentages=[50.0, 25.0, 25.0])

    debts = mgr.simplify_debts()
    assert len(debts) > 0
    print("Complete Python Splitwise passed!")
