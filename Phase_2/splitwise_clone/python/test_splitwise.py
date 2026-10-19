from splitwise import ExpenseManager, User, SplitType


def test_equal_split():
    mgr = ExpenseManager()
    mgr.add_user(User("u1", "Alice"))
    mgr.add_user(User("u2", "Bob"))
    mgr.add_expense("u1", 200.0, SplitType.EQUAL, ["u1", "u2"])
    bal = mgr.get_balances("u2")
    assert abs(bal["u1"] - 100.0) < 0.01


def test_exact_split():
    mgr = ExpenseManager()
    mgr.add_user(User("u1", "A"))
    mgr.add_user(User("u2", "B"))
    mgr.add_user(User("u3", "C"))
    mgr.add_expense("u1", 100.0, SplitType.EXACT, ["u1","u2","u3"], amounts=[10.0, 40.0, 50.0])
    assert abs(mgr.get_balances("u2")["u1"] - 40.0) < 0.01
    assert abs(mgr.get_balances("u3")["u1"] - 50.0) < 0.01


def test_percent_split():
    mgr = ExpenseManager()
    mgr.add_user(User("u1", "A"))
    mgr.add_user(User("u2", "B"))
    mgr.add_expense("u1", 200.0, SplitType.PERCENT, ["u1","u2"], percentages=[60.0, 40.0])
    assert abs(mgr.get_balances("u2")["u1"] - 80.0) < 0.01


def test_simplify_debts():
    mgr = ExpenseManager()
    for uid, name in [("u1","A"),("u2","B"),("u3","C")]:
        mgr.add_user(User(uid, name))
    mgr.add_expense("u1", 300.0, SplitType.EQUAL, ["u1","u2","u3"])
    debts = mgr.simplify_debts()
    assert len(debts) > 0
    total_settled = sum(d[2] for d in debts)
    assert abs(total_settled - 200.0) < 0.01


if __name__ == "__main__":
    test_equal_split()
    test_exact_split()
    test_percent_split()
    test_simplify_debts()
    print("All Splitwise tests passed!")
