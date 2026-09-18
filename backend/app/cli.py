"""Narzędzia wiersza poleceń: administrator, migracje, backup.

Użycie:
    python -m app.cli create-admin --login admin
    python -m app.cli reset-password --login admin
    python -m app.cli migrate
    python -m app.cli backup
    python -m app.cli list-users
"""

from __future__ import annotations

import argparse
import getpass
import sys

from app.core.config import get_settings
from app.core.errors import AppError
from app.db.seed import seed_reference_data
from app.db.session import session_scope
from app.models.enums import UserRole
from app.services import auth_service, backup_service


def _prompt_password(confirm: bool = True) -> str:
    password = getpass.getpass("Hasło: ")
    if confirm and password != getpass.getpass("Powtórz hasło: "):
        print("Hasła nie są identyczne.", file=sys.stderr)
        raise SystemExit(1)
    return password


def cmd_create_admin(args: argparse.Namespace) -> None:
    password = args.password or _prompt_password()
    with session_scope() as session:
        seed_reference_data(session)
        user = auth_service.create_user(
            session,
            login=args.login,
            password=password,
            email=args.email,
            role=UserRole.ADMIN.value,
        )
        print(f"Utworzono administratora: {user.login}")


def cmd_reset_password(args: argparse.Namespace) -> None:
    password = args.password or _prompt_password()
    with session_scope() as session:
        user = auth_service.get_user_by_login(session, args.login)
        if user is None:
            print("Nie znaleziono użytkownika.", file=sys.stderr)
            raise SystemExit(1)
        auth_service.set_password(session, user, password)
        auth_service.revoke_all_sessions(session, user.id)
        print(f"Hasło użytkownika {user.login} zostało zmienione.")


def cmd_list_users(_: argparse.Namespace) -> None:
    from sqlalchemy import select

    from app.models.user import User

    with session_scope() as session:
        users = session.execute(select(User).order_by(User.login)).scalars().all()
        if not users:
            print("Brak użytkowników.")
            return
        for user in users:
            status = "aktywny" if user.is_active else "nieaktywny"
            print(f"{user.id:>3}  {user.login:<20} {user.role:<12} {status}")


def cmd_migrate(_: argparse.Namespace) -> None:
    get_settings().ensure_directories()
    backup_service.run_migrations()
    with session_scope() as session:
        seed_reference_data(session)
    print("Migracje wykonane.")


def cmd_backup(_: argparse.Namespace) -> None:
    with session_scope() as session:
        backup = backup_service.create_backup(session, note="cli")
        print(f"Utworzono kopię zapasową: {backup.filename}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Narzędzia administracyjne ewidencji")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_admin = subparsers.add_parser("create-admin", help="Tworzy konto administratora")
    create_admin.add_argument("--login", required=True)
    create_admin.add_argument("--email", default=None)
    create_admin.add_argument("--password", default=None, help="Pominięcie spowoduje zapytanie interaktywne")
    create_admin.set_defaults(func=cmd_create_admin)

    reset_password = subparsers.add_parser("reset-password", help="Ustawia nowe hasło użytkownika")
    reset_password.add_argument("--login", required=True)
    reset_password.add_argument("--password", default=None)
    reset_password.set_defaults(func=cmd_reset_password)

    list_users = subparsers.add_parser("list-users", help="Wypisuje użytkowników")
    list_users.set_defaults(func=cmd_list_users)

    migrate = subparsers.add_parser("migrate", help="Uruchamia migracje Alembic")
    migrate.set_defaults(func=cmd_migrate)

    backup = subparsers.add_parser("backup", help="Tworzy kopię zapasową bazy")
    backup.set_defaults(func=cmd_backup)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    get_settings().ensure_directories()
    try:
        args.func(args)
    except AppError as exc:
        print(f"Błąd: {exc.message}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
