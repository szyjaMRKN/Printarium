"""Wspólne narzędzia repozytoriów (paginacja, sortowanie)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int

    @property
    def pages(self) -> int:
        if self.per_page <= 0:
            return 0
        return (self.total + self.per_page - 1) // self.per_page


def count_rows(session: Session, stmt: Select[Any]) -> int:
    subquery = stmt.order_by(None).subquery()
    return int(session.execute(select(func.count()).select_from(subquery)).scalar_one())


def paginate(session: Session, stmt: Select[Any], page: int, per_page: int) -> Page[Any]:
    page = max(page, 1)
    per_page = min(max(per_page, 1), 200)
    total = count_rows(session, stmt)
    rows = session.execute(stmt.limit(per_page).offset((page - 1) * per_page)).scalars().unique().all()
    return Page(items=list(rows), total=total, page=page, per_page=per_page)
