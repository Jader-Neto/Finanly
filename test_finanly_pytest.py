import json
from pathlib import Path

import finanly_pro


def test_register_and_login(tmp_path):
    data_file = tmp_path / "data.json"
    finanly_pro.DATA_FILE = str(data_file)
    # inicializa arquivo vazio
    finanly_pro.DATA_FILE = str(data_file)
    ms = finanly_pro.FinanlySystem()

    u = ms.register_user("PyUser", "py@example.com", "pwd")
    assert u.user_id == 1
    assert ms.login("py@example.com", "pwd")


def test_group_and_expense(tmp_path):
    data_file = tmp_path / "data2.json"
    finanly_pro.DATA_FILE = str(data_file)
    ms = finanly_pro.FinanlySystem()
    u1 = ms.register_user("A", "a@example.com", "p")
    u2 = ms.register_user("B", "b@example.com", "p")
    ms.login(u1.email, "p")
    grp = ms.create_group("G", [u2.user_id])
    exp = ms.create_equal_expense(grp.group_id, "X", u1.user_id, 90.0, participants=grp.membros)
    assert exp.total == 90.0
    balances = ms.calculate_group_balances(grp.group_id)
    assert isinstance(balances, dict)


def test_payment_and_exports(tmp_path):
    data_file = tmp_path / "data3.json"
    finanly_pro.DATA_FILE = str(data_file)
    ms = finanly_pro.FinanlySystem()
    u1 = ms.register_user("C", "c@example.com", "p")
    u2 = ms.register_user("D", "d@example.com", "p")
    ms.login(u1.email, "p")
    grp = ms.create_group("G2", [u2.user_id])
    p = ms.register_payment(grp.group_id, from_user=u2.user_id, to_user=u1.user_id, valor=10.0)
    assert p.valor == 10.0
    txt = ms.export_group_summary_txt(grp.group_id)
    csv = ms.export_group_expenses_csv(grp.group_id)
    assert Path(txt).exists()
    assert Path(csv).exists()
