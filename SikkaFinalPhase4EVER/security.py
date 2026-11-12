"""Record encryption for personal data in the Sikka database.

National ID, email and phone are encrypted with AES-256-GCM before they
are saved, so a copy of sikka.db does not show any personal data.
A keyed hash (HMAC-SHA256) of the National ID is stored next to it, so the
system can still check for duplicates without decrypting every row.
"""
import base64, hashlib, hmac, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PREFIX = "enc:"                                   # marks an encrypted value
# personal fields that are encrypted in each table
# (users.email stays readable because it is used to check new sign-ups)
PROTECTED = {"passengers": ("national_id", "email", "phone"),
             "users":      ("national_id", "phone")}


def _load_key(name):
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is not set. Run: python security.py --new-keys")
    key = base64.urlsafe_b64decode(value)
    if len(key) != 32:
        raise RuntimeError(f"{name} must be a 32-byte key")
    return key


def encrypt(plain):
    if not plain or str(plain).startswith(PREFIX):
        return plain                              # empty, or already encrypted
    nonce = os.urandom(12)                        # new random nonce every time
    data = AESGCM(_load_key("SIKKA_DATA_KEY")).encrypt(nonce, str(plain).encode(), None)
    return PREFIX + base64.urlsafe_b64encode(nonce + data).decode()


def decrypt(value):
    if not value or not str(value).startswith(PREFIX):
        return value                              # old plain value
    raw = base64.urlsafe_b64decode(value[len(PREFIX):])
    # raises InvalidTag if the value was changed in the database
    return AESGCM(_load_key("SIKKA_DATA_KEY")).decrypt(raw[:12], raw[12:], None).decode()


def blind_index(national_id):
    """Same input always gives the same hash, but it cannot be reversed."""
    if not national_id:
        return None
    key = _load_key("SIKKA_INDEX_KEY")
    return hmac.new(key, national_id.strip().encode(), hashlib.sha256).hexdigest()


def reveal(rows):
    """Decrypts the personal fields of database rows before showing them."""
    out = []
    for r in rows:
        d = dict(r)
        for f in ("national_id", "email", "phone"):
            if f in d:
                d[f] = decrypt(d[f])
        out.append(d)
    return out


def encrypt_existing_rows(conn):
    """One-time migration: encrypts the plain values that are already saved."""
    for table, fields in PROTECTED.items():
        cols = ", ".join(fields)
        for r in conn.execute(f"SELECT id, {cols} FROM {table}").fetchall():
            new = {f: encrypt(r[f]) for f in fields}
            if all(new[f] == r[f] for f in fields):
                continue                          # nothing left to encrypt
            sets = ", ".join(f"{f}=?" for f in fields)
            conn.execute(f"UPDATE {table} SET {sets}, nid_hash=? WHERE id=?",
                         (*new.values(), blind_index(decrypt(r["national_id"])), r["id"]))
    conn.commit()


if __name__ == "__main__":
    import sys
    if "--new-keys" in sys.argv:
        for name in ("SIKKA_DATA_KEY", "SIKKA_INDEX_KEY"):
            print(f"{name}={base64.urlsafe_b64encode(os.urandom(32)).decode()}")
