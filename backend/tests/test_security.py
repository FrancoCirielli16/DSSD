from app.core.security import hash_password, verify_password


def test_hash_y_verificacion():
    h = hash_password("demo1234")
    assert h != "demo1234"
    assert verify_password("demo1234", h)
    assert not verify_password("otra", h)


def test_cada_hash_usa_su_propia_sal():
    assert hash_password("x") != hash_password("x")


def test_hash_corrupto_no_verifica_ni_explota():
    assert not verify_password("x", "no-es-un-hash")
    assert not verify_password("x", "")
