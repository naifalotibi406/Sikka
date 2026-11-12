import base64, os, shutil, sqlite3
import pytest
from cryptography.exceptions import InvalidTag

os.environ["SIKKA_DATA_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode()
os.environ["SIKKA_INDEX_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode()
import security, main


@pytest.fixture
def app(tmp_path):
    db = tmp_path / "sikka.db"
    shutil.copy("sikka.db", db)          # copy of the old database (plain data)
    main.DB = str(db)
    main.init_db()                       # runs the encryption migration
    main.app.config["TESTING"] = True
    return main.app.test_client(), str(db)


def test_1_encrypt_and_decrypt():
    enc = security.encrypt("1023456781")
    assert enc.startswith("enc:") and "1023456781" not in enc
    assert security.decrypt(enc) == "1023456781"


def test_2_same_value_gives_different_ciphertext():
    first = security.encrypt("0512345601")
    second = security.encrypt("0512345601")
    assert first != second


def test_3_changed_value_is_rejected():
    enc = security.encrypt("1023456781")
    changed = enc[:-6] + ("AAAAAA" if enc[-6:] != "AAAAAA" else "BBBBBB")
    with pytest.raises(InvalidTag):
        security.decrypt(changed)


def test_4_wrong_key_cannot_read():
    enc = security.encrypt("1023456781")
    old = os.environ["SIKKA_DATA_KEY"]
    os.environ["SIKKA_DATA_KEY"] = base64.urlsafe_b64encode(os.urandom(32)).decode()
    with pytest.raises(InvalidTag):
        security.decrypt(enc)
    os.environ["SIKKA_DATA_KEY"] = old


def test_5_database_file_has_no_plain_ids(app):
    _, db = app
    sql = "SELECT national_id, email, phone FROM passengers"
    rows = sqlite3.connect(db).execute(sql).fetchall()
    assert len(rows) == 20
    assert all(v.startswith("enc:") for r in rows for v in r)


def test_6_app_still_shows_real_data(app):
    client, _ = app
    client.post("/login", data={"username": "addmin", "password": "admin123"})
    page = client.get("/passengers").get_data(as_text=True)
    assert "1023456781" in page and "enc:" not in page


def test_7_duplicate_national_id_is_blocked(app):
    client, _ = app
    client.post("/login", data={"username": "addmin", "password": "admin123"})
    form = {"name": "Test", "national_id": "1023456781"}
    reply = client.post("/passengers/add", data=form, follow_redirects=True)
    page = reply.get_data(as_text=True)
    assert "National ID already exists" in page
