"""WebSecKit — scrypt password hashing."""

from __future__ import annotations

import binascii
import hashlib
import hmac
import os

SCRYPT_N = 16384
SCRYPT_R = 8
SCRYPT_P = 1
KEYLEN = 32
SALTLEN = 16


def hash_password(password: str) -> str:
    salt = os.urandom(SALTLEN)
    derived = hashlib.scrypt(password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=KEYLEN)
    return "scrypt${}${}${}${}${}".format(
        SCRYPT_N,
        SCRYPT_R,
        SCRYPT_P,
        binascii.b2a_base64(salt, newline=False).decode(),
        binascii.b2a_base64(derived, newline=False).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 6 or parts[0] != "scrypt":
        dummy_verify(password)
        return False
    n, r, p = int(parts[1]), int(parts[2]), int(parts[3])
    salt = binascii.a2b_base64(parts[4])
    expected = binascii.a2b_base64(parts[5])
    derived = hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=len(expected))
    return hmac.compare_digest(derived, expected)


def dummy_verify(password: str) -> None:
    hashlib.scrypt(password.encode(), salt=b"\x01" * SALTLEN, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=KEYLEN)
