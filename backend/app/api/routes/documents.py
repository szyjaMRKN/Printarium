"""Dokumenty sprzedaży (rachunki, faktury bez VAT) + PDF."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, db_session, get_current_context, require_write
from app.repositories.base import paginate
from app.schemas.common import MessageResponse, PageMeta, PageResponse
from app.schemas.document import DocumentCreate, DocumentOut, DocumentUpdate
from app.services import documents_service, pdf_service

router = APIRouter(prefix="/documents", tags=["dokumenty"])


@router.get("", response_model=PageResponse[DocumentOut])
def list_documents(
    year: int | None = Query(default=None, ge=2000, le=2100),
    document_type: str | None = Query(default=None, max_length=32),
    ksef_status: str | None = Query(default=None, max_length=32),
    search: str | None = Query(default=None, max_length=200),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=25, ge=1, le=200),
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> PageResponse[DocumentOut]:
    stmt = documents_service.query(
        year=year, document_type=document_type, ksef_status=ksef_status, search=search
    )
    result = paginate(session, stmt, page, per_page)
    return PageResponse[DocumentOut](
        items=[DocumentOut.model_validate(item) for item in result.items],
        meta=PageMeta(total=result.total, page=result.page, per_page=result.per_page, pages=result.pages),
    )


@router.post("", response_model=DocumentOut, status_code=201)
def create_document(
    payload: DocumentCreate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> DocumentOut:
    document = documents_service.create_document(session, payload, context.user, ip=context.ip)
    session.commit()
    return DocumentOut.model_validate(document)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> DocumentOut:
    return DocumentOut.model_validate(documents_service.get_document(session, document_id))


@router.patch("/{document_id}", response_model=DocumentOut)
def update_document(
    document_id: int,
    payload: DocumentUpdate,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> DocumentOut:
    document = documents_service.update_document(session, document_id, payload, context.user, ip=context.ip)
    session.commit()
    return DocumentOut.model_validate(document)


@router.delete("/{document_id}", response_model=MessageResponse)
def delete_document(
    document_id: int,
    context: CurrentUser = Depends(require_write),
    session: Session = Depends(db_session),
) -> MessageResponse:
    documents_service.soft_delete_document(session, document_id, context.user, ip=context.ip)
    session.commit()
    return MessageResponse(message="Dokument został oznaczony jako usunięty.")


@router.get("/{document_id}/pdf")
def document_pdf(
    document_id: int,
    _: CurrentUser = Depends(get_current_context),
    session: Session = Depends(db_session),
) -> Response:
    document = documents_service.get_document(session, document_id)
    content = pdf_service.build_document_pdf(document)
    filename = f"{document.document_type}_{document.number.replace('/', '-')}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
