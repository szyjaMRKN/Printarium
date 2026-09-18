import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../api/resources';
import type { DocumentInput } from '../api/resources';
import { salesApi } from '../api/sales';
import { openFile } from '../api/client';
import { Alert, Badge, EmptyState, Field, Loading, Modal, MoneyInput, Pagination } from '../components/ui';
import { useMeta } from '../hooks/useMeta';
import { useToast } from '../hooks/useToast';
import { currentYear, formatDate, formatMoney, optionLabel, todayIso } from '../utils/format';
import type { SalesDocument } from '../types';

function emptyDocument(): DocumentInput {
  return {
    document_type: 'rachunek',
    sale_id: null,
    issue_date: todayIso(),
    sale_date: null,
    due_date: null,
    buyer_name: '',
    buyer_nip: null,
    buyer_address: null,
    buyer_email: null,
    customer_type: 'b2c',
    items: [],
    payment_method: 'przelew',
    paid_note: null,
    notes: null,
    ksef_status: 'nie_dotyczy',
    ksef_number: null,
  };
}

export function DocumentsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data: meta } = useMeta();
  const [filters, setFilters] = useState<Record<string, unknown>>({ year: currentYear(), page: 1, per_page: 25 });
  const [formOpen, setFormOpen] = useState(false);
  const [form, setForm] = useState<DocumentInput>(emptyDocument());
  const [ksefEditing, setKsefEditing] = useState<SalesDocument | null>(null);

  const documents = useQuery({ queryKey: ['documents', filters], queryFn: () => documentsApi.list(filters) });
  const sales = useQuery({
    queryKey: ['sales', 'for-documents'],
    queryFn: () => salesApi.list({ per_page: 50, sort_by: 'sale_date', sort_dir: 'desc' }),
    enabled: formOpen,
  });

  const createMutation = useMutation({
    mutationFn: (payload: DocumentInput) => documentsApi.create(payload),
    onSuccess: (document) => {
      toast.success(`Wystawiono dokument ${document.number}.`);
      void queryClient.invalidateQueries({ queryKey: ['documents'] });
      void queryClient.invalidateQueries({ queryKey: ['limits'] });
      setFormOpen(false);
      setForm(emptyDocument());
    },
    onError: (error) => toast.error(error),
  });

  const ksefMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: { ksef_status: string; ksef_number: string | null } }) =>
      documentsApi.update(id, payload),
    onSuccess: () => {
      toast.success('Zapisano oznaczenie KSeF.');
      void queryClient.invalidateQueries({ queryKey: ['documents'] });
      setKsefEditing(null);
    },
    onError: (error) => toast.error(error),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => documentsApi.remove(id),
    onSuccess: () => {
      toast.success('Dokument został usunięty.');
      void queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
    onError: (error) => toast.error(error),
  });

  const addItem = () =>
    setForm((current) => ({
      ...current,
      items: [...current.items, { name: '', quantity: 1, unit_price_gr: 0, unit: 'szt.' }],
    }));

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!form.buyer_name.trim()) {
      toast.push('Podaj nabywcę.', 'error');
      return;
    }
    if (!form.sale_id && form.items.length === 0) {
      toast.push('Wybierz sprzedaż albo dodaj pozycje dokumentu.', 'error');
      return;
    }
    createMutation.mutate(form);
  };

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Dokumenty</h1>
          <p>
            Rachunki i faktury bez VAT. Dane sprzedawcy pochodzą z ustawień, numeracja jest konfigurowalna, PDF
            generuje serwer.
          </p>
        </div>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => {
            setForm(emptyDocument());
            setFormOpen(true);
          }}
        >
          + Wystaw dokument
        </button>
      </div>

      <section className="card">
        <div className="filters">
          <Field label="Rok" htmlFor="d_year">
            <input
              id="d_year"
              type="number"
              value={(filters.year as number) ?? ''}
              onChange={(event) =>
                setFilters((current) => ({ ...current, year: event.target.value ? Number(event.target.value) : undefined, page: 1 }))
              }
            />
          </Field>
          <Field label="Rodzaj" htmlFor="d_type">
            <select
              id="d_type"
              value={(filters.document_type as string) ?? ''}
              onChange={(event) => setFilters((current) => ({ ...current, document_type: event.target.value || undefined, page: 1 }))}
            >
              <option value="">wszystkie</option>
              {meta?.document_type.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="KSeF" htmlFor="d_ksef">
            <select
              id="d_ksef"
              value={(filters.ksef_status as string) ?? ''}
              onChange={(event) => setFilters((current) => ({ ...current, ksef_status: event.target.value || undefined, page: 1 }))}
            >
              <option value="">wszystkie</option>
              {meta?.ksef_status.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Szukaj" htmlFor="d_search">
            <input
              id="d_search"
              value={(filters.search as string) ?? ''}
              onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value || undefined, page: 1 }))}
              placeholder="numer, nabywca, NIP"
            />
          </Field>
        </div>
      </section>

      <section className="card card--flush">
        {documents.isLoading ? (
          <Loading />
        ) : documents.data && documents.data.items.length === 0 ? (
          <EmptyState label="Brak dokumentów w wybranym okresie." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Numer</th>
                  <th>Rodzaj</th>
                  <th>Data wystawienia</th>
                  <th>Nabywca</th>
                  <th className="num">Kwota</th>
                  <th>KSeF</th>
                  <th aria-label="Akcje" />
                </tr>
              </thead>
              <tbody>
                {documents.data?.items.map((document) => (
                  <tr key={document.id}>
                    <td data-label="Numer">{document.number}</td>
                    <td data-label="Rodzaj">{optionLabel(meta?.document_type, document.document_type)}</td>
                    <td data-label="Data wystawienia">{formatDate(document.issue_date)}</td>
                    <td data-label="Nabywca">
                      {document.buyer_name}
                      {document.buyer_nip ? <span className="small muted"> · NIP {document.buyer_nip}</span> : null}
                    </td>
                    <td data-label="Kwota" className="num">{formatMoney(document.total_gr)}</td>
                    <td data-label="KSeF">
                      <Badge variant={document.ksef_status === 'przeslany' ? 'badge--success' : undefined}>
                        {optionLabel(meta?.ksef_status, document.ksef_status)}
                      </Badge>
                      {document.ksef_number ? <div className="small muted">{document.ksef_number}</div> : null}
                    </td>
                    <td data-label="">
                      <div className="btn-row">
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() => void openFile(`/api/documents/${document.id}/pdf`).catch((error) => toast.error(error))}
                        >
                          PDF
                        </button>
                        <button type="button" className="btn btn--sm" onClick={() => setKsefEditing(document)}>
                          KSeF
                        </button>
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() => {
                            if (window.confirm(`Usunąć dokument ${document.number}?`)) deleteMutation.mutate(document.id);
                          }}
                        >
                          Usuń
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {documents.data ? (
          <Pagination
            page={documents.data.meta.page}
            pages={documents.data.meta.pages}
            total={documents.data.meta.total}
            onChange={(page) => setFilters((current) => ({ ...current, page }))}
          />
        ) : null}
      </section>

      {formOpen ? (
        <Modal title="Nowy dokument sprzedaży" onClose={() => setFormOpen(false)} wide>
          <form className="stack" onSubmit={submit}>
            <Alert variant="info">
              Wybranie sprzedaży przepisuje jej pozycje do dokumentu. Bez wyboru sprzedaży wpisz pozycje ręcznie.
            </Alert>
            <div className="form-grid">
              <Field label="Rodzaj dokumentu" htmlFor="do_type">
                <select
                  id="do_type"
                  value={form.document_type}
                  onChange={(event) => setForm({ ...form, document_type: event.target.value })}
                >
                  {meta?.document_type.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Data wystawienia" htmlFor="do_issue">
                <input
                  id="do_issue"
                  type="date"
                  required
                  value={form.issue_date}
                  onChange={(event) => setForm({ ...form, issue_date: event.target.value })}
                />
              </Field>
              <Field label="Termin płatności" htmlFor="do_due" hint="Puste = według ustawień">
                <input
                  id="do_due"
                  type="date"
                  value={form.due_date ?? ''}
                  onChange={(event) => setForm({ ...form, due_date: event.target.value || null })}
                />
              </Field>
              <Field label="Powiązana sprzedaż" htmlFor="do_sale">
                <select
                  id="do_sale"
                  value={form.sale_id ?? ''}
                  onChange={(event) => {
                    const saleId = event.target.value ? Number(event.target.value) : null;
                    const sale = sales.data?.items.find((item) => item.id === saleId);
                    setForm({
                      ...form,
                      sale_id: saleId,
                      buyer_name: sale?.customer_name ?? form.buyer_name,
                      customer_type: sale?.customer_type ?? form.customer_type,
                      sale_date: sale?.sale_date ?? null,
                      items: saleId ? [] : form.items,
                    });
                  }}
                >
                  <option value="">— dokument bez powiązania —</option>
                  {sales.data?.items.map((sale) => (
                    <option key={sale.id} value={sale.id}>
                      {sale.document_number} · {formatDate(sale.sale_date)} · {formatMoney(sale.total_gr)}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Nabywca" htmlFor="do_buyer">
                <input
                  id="do_buyer"
                  required
                  value={form.buyer_name}
                  onChange={(event) => setForm({ ...form, buyer_name: event.target.value })}
                />
              </Field>
              <Field label="NIP nabywcy" htmlFor="do_nip">
                <input
                  id="do_nip"
                  value={form.buyer_nip ?? ''}
                  onChange={(event) => setForm({ ...form, buyer_nip: event.target.value || null })}
                />
              </Field>
              <Field label="Typ klienta" htmlFor="do_customer_type">
                <select
                  id="do_customer_type"
                  value={form.customer_type}
                  onChange={(event) => setForm({ ...form, customer_type: event.target.value })}
                >
                  {meta?.customer_type.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Metoda płatności" htmlFor="do_method">
                <select
                  id="do_method"
                  value={form.payment_method ?? ''}
                  onChange={(event) => setForm({ ...form, payment_method: event.target.value || null })}
                >
                  {meta?.payment_method.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              {form.customer_type === 'b2b' ? (
                <Field label="Status KSeF" htmlFor="do_ksef">
                  <select
                    id="do_ksef"
                    value={form.ksef_status}
                    onChange={(event) => setForm({ ...form, ksef_status: event.target.value })}
                  >
                    {meta?.ksef_status.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </Field>
              ) : null}
            </div>

            <Field label="Adres nabywcy" htmlFor="do_address">
              <textarea
                id="do_address"
                value={form.buyer_address ?? ''}
                onChange={(event) => setForm({ ...form, buyer_address: event.target.value || null })}
              />
            </Field>

            {!form.sale_id ? (
              <div className="card card--flush">
                <div className="table-wrap">
                  <table className="data">
                    <thead>
                      <tr>
                        <th>Nazwa</th>
                        <th className="num">Ilość</th>
                        <th>J.m.</th>
                        <th className="num">Cena (zł)</th>
                        <th aria-label="Akcje" />
                      </tr>
                    </thead>
                    <tbody>
                      {form.items.map((item, index) => (
                        <tr key={index}>
                          <td data-label="Nazwa">
                            <input
                              value={item.name}
                              aria-label={`Nazwa pozycji ${index + 1}`}
                              onChange={(event) =>
                                setForm({
                                  ...form,
                                  items: form.items.map((row, position) =>
                                    position === index ? { ...row, name: event.target.value } : row,
                                  ),
                                })
                              }
                            />
                          </td>
                          <td data-label="Ilość" className="num">
                            <input
                              type="number"
                              min={1}
                              value={item.quantity}
                              aria-label={`Ilość pozycji ${index + 1}`}
                              onChange={(event) =>
                                setForm({
                                  ...form,
                                  items: form.items.map((row, position) =>
                                    position === index ? { ...row, quantity: Number(event.target.value) || 1 } : row,
                                  ),
                                })
                              }
                            />
                          </td>
                          <td data-label="J.m.">
                            <input
                              value={item.unit}
                              aria-label={`Jednostka pozycji ${index + 1}`}
                              onChange={(event) =>
                                setForm({
                                  ...form,
                                  items: form.items.map((row, position) =>
                                    position === index ? { ...row, unit: event.target.value } : row,
                                  ),
                                })
                              }
                            />
                          </td>
                          <td data-label="Cena" className="num">
                            <MoneyInput
                              valueGr={item.unit_price_gr}
                              onChangeGr={(value) =>
                                setForm({
                                  ...form,
                                  items: form.items.map((row, position) =>
                                    position === index ? { ...row, unit_price_gr: value } : row,
                                  ),
                                })
                              }
                            />
                          </td>
                          <td data-label="">
                            <button
                              type="button"
                              className="btn btn--sm"
                              onClick={() => setForm({ ...form, items: form.items.filter((_, position) => position !== index) })}
                            >
                              Usuń
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="pagination">
                  <button type="button" className="btn btn--sm" onClick={addItem}>
                    + Dodaj pozycję
                  </button>
                  <span>
                    Razem:{' '}
                    <strong>
                      {formatMoney(form.items.reduce((sum, item) => sum + item.quantity * item.unit_price_gr, 0))}
                    </strong>
                  </span>
                </div>
              </div>
            ) : null}

            <Field label="Uwagi na dokumencie" htmlFor="do_notes">
              <textarea
                id="do_notes"
                value={form.notes ?? ''}
                onChange={(event) => setForm({ ...form, notes: event.target.value || null })}
              />
            </Field>

            <div className="form-actions">
              <button type="button" className="btn" onClick={() => setFormOpen(false)}>
                Anuluj
              </button>
              <button type="submit" className="btn btn--primary" disabled={createMutation.isPending}>
                Wystaw dokument
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {ksefEditing ? (
        <Modal title={`KSeF — dokument ${ksefEditing.number}`} onClose={() => setKsefEditing(null)}>
          <form
            className="stack"
            onSubmit={(event) => {
              event.preventDefault();
              const formData = new FormData(event.target as HTMLFormElement);
              ksefMutation.mutate({
                id: ksefEditing.id,
                payload: {
                  ksef_status: String(formData.get('ksef_status')),
                  ksef_number: String(formData.get('ksef_number') || '') || null,
                },
              });
            }}
          >
            <Alert variant="info">
              Aplikacja nie wysyła dokumentów do KSeF. Oznaczenie służy do własnej ewidencji i pomocniczego licznika
              miesięcznego.
            </Alert>
            <Field label="Status" htmlFor="ks_status">
              <select id="ks_status" name="ksef_status" defaultValue={ksefEditing.ksef_status}>
                {meta?.ksef_status.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Numer KSeF" htmlFor="ks_number">
              <input id="ks_number" name="ksef_number" defaultValue={ksefEditing.ksef_number ?? ''} />
            </Field>
            <div className="form-actions">
              <button type="button" className="btn" onClick={() => setKsefEditing(null)}>
                Anuluj
              </button>
              <button type="submit" className="btn btn--primary" disabled={ksefMutation.isPending}>
                Zapisz
              </button>
            </div>
          </form>
        </Modal>
      ) : null}
    </>
  );
}
