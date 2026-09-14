"""WebSecKit — account enumeration protection."""

GENERIC_AUTH_MESSAGE = "Invalid credentials."
GENERIC_RESET_MESSAGE = "If an account exists for this email, a reset link has been sent."


def generic_auth_error() -> dict[str, str | int]:
    return {"status": 401, "error": GENERIC_AUTH_MESSAGE}


def generic_reset_accepted() -> dict[str, str | int]:
    return {"status": 200, "message": GENERIC_RESET_MESSAGE}
