"""Create or reset an admin user."""

from __future__ import annotations

import argparse
from getpass import getpass

from app.core.database import SessionLocal
from app.core.providers import AppError
from app.services.admin_auth_service import AdminAuthService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create or reset a BuyWise admin user.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--reset-password", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    password = args.password or getpass("Admin password: ")
    db = SessionLocal()
    try:
        user = AdminAuthService(db).create_admin_user(
            username=args.username,
            email=args.email,
            password=password,
            reset_password=args.reset_password,
        )
    except AppError as exc:
        db.rollback()
        print(f"Error: {exc.message}")
        return 1
    finally:
        db.close()

    print(f"Admin user ready: username={user.username} role={user.role}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
