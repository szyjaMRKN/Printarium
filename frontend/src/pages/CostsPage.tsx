import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { costsApi } from '../api/resources';
import type { CostInput } from '../api/resources';
import { downloadFile } from '../api/client';
import { Alert, EmptyState, Field, Loading, Modal, MoneyInput, Pagination } from '../components/ui';
import { useMeta } from '../hooks/useMeta';
import { useToast } from '../hooks/useToast';
import { currentYear, formatDate, formatMoney, optionLabel, todayIso } from '../utils/format';
import type { Cost } from '../types';

function emptyCost(): CostInput {
  return {
    cost_date: todayIso(),
    name: '',
    category_id: null,
    vendor: null,
    invoice_number: null,
    amount_gr: 0,
    payment_method: 'przelew',
    description: null,
    attachment_id: null,
  };
}

export function CostsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data: meta } = useMeta();
  const [filters, setFilters] = useState<Record<string, unknown>>({ year: currentYear(), page: 1, per_page: 25 });
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Cost | null>(null);
  const [form, setForm] = useState<CostInput>(emptyCost());
  const [attachmentName, setAttachmentName] = useState<string | null>(null);
  const [categoriesOpen, setCategoriesOpen] = useState(false);
  const [newCategory, setNewCategory] = useState('');

  const categories = useQuery({ queryKey: ['cost-categories'], queryFn: costsApi.categories });
  const costs = useQuery({ queryKey: ['costs', filters], queryFn: () => costsApi.list(filters) });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['costs'] });
    void queryClient.invalidateQueries({ queryKey: ['dashboard'] });
  };

  const saveMutation = useMutation({
    mutationFn: (payload: CostInput) =>
      editing ? costsApi.update(editing.id, payload) : costsApi.create(payload),
    onSuccess: () => {
      toast.success(editing ? 'Zapisano zmiany kosztu.' : 'Dodano koszt.');
      invalidate();
      setFormOpen(false);
      setEditing(null);
      setForm(emptyCost());
      setAttachmentName(null);
    },
    onError: (error) => toast.error(error),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => costsApi.remove(id),
    onSuccess: () => {
      toast.success('Koszt został usunięty.');
      invalidate();
    },
    onError: (error) => toast.error(error),
  });

  const categoryMutation = useMutation({
    mutationFn: (name: string) => costsApi.createCategory(name),
    onSuccess: () => {
      toast.success('Dodano kategorię.');
      setNewCategory('');
      void queryClient.invalidateQueries({ queryKey: ['cost-categories'] });
    },
    onError: (error) => toast.error(error),
  });

  const categoryToggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      costsApi.updateCategory(id, { is_active }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ['cost-categories'] }),
    onError: (error) => toast.error(error),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => costsApi.uploadAttachment(file),
    onSuccess: (attachment) => {
      setForm((current) => ({ ...current, attachment_id: attachment.id }));
      setAttachmentName(attachment.original_name);
      toast.success('Załącznik został wgrany.');
    },
    onError: (error) => toast.error(error),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyCost());
    setAttachmentName(null);
    setFormOpen(true);
  };

  const openEdit = (cost: Cost) => {
    setEditing(cost);
    setForm({
      cost_date: cost.cost_date,
      name: cost.name,
      category_id: cost.category_id,
      vendor: cost.vendor,
      invoice_number: cost.invoice_number,
      amount_gr: cost.amount_gr,
      payment_method: cost.payment_method,
      description: cost.description,
      attachment_id: cost.attachment_id,
    });
    setAttachmentName(cost.attachment_name);
    setFormOpen(true);
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!form.name.trim()) {
      toast.push('Podaj nazwę kosztu.', 'error');
      return;
    }
    if (form.amount_gr <= 0) {
      toast.push('Kwota kosztu musi być większa od zera.', 'error');
      return;
    }
    saveMutation.mutate(form);
  };

  const total = costs.data?.items.reduce((sum, cost) => sum + cost.amount_gr, 0) ?? 0;

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Koszty</h1>
          <p>Koszty działalności wraz z dokumentami. Pliki trafiają poza katalog publiczny serwera.</p>
        </div>
        <div className="btn-row">
          <button type="button" className="btn" onClick={() => setCategoriesOpen(true)}>
            Kategorie
          </button>
          <button
            type="button"
            className="btn"
            onClick={() =>
              void downloadFile('/api/reports/koszty/export', { format: 'xlsx', year: filters.year }).catch((error) =>
                toast.error(error),
              )
            }
          >
            Eksport XLSX
          </button>
          <button type="button" className="btn btn--primary" onClick={openCreate}>
            + Dodaj koszt
          </button>
        </div>
      </div>

      <section className="card">
        <div className="filters">
          <Field label="Rok" htmlFor="c_year">
            <input
              id="c_year"
              type="number"
              value={(filters.year as number) ?? ''}
              onChange={(event) =>
                setFilters((current) => ({ ...current, year: event.target.value ? Number(event.target.value) : undefined, page: 1 }))
              }
            />
          </Field>
          <Field label="Miesiąc" htmlFor="c_month">
            <select
              id="c_month"
              value={(filters.month as number) ?? ''}
              onChange={(event) =>
                setFilters((current) => ({ ...current, month: event.target.value ? Number(event.target.value) : undefined, page: 1 }))
              }
            >
              <option value="">wszystkie</option>
              {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                <option key={month} value={month}>
                  {String(month).padStart(2, '0')}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Kategoria" htmlFor="c_category">
            <select
              id="c_category"
              value={(filters.category_id as number) ?? ''}
              onChange={(event) =>
                setFilters((current) => ({
                  ...current,
                  category_id: event.target.value ? Number(event.target.value) : undefined,
                  page: 1,
                }))
              }
            >
              <option value="">wszystkie</option>
              {categories.data?.map((category) => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Szukaj" htmlFor="c_search">
            <input
              id="c_search"
              value={(filters.search as string) ?? ''}
              onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value || undefined, page: 1 }))}
              placeholder="nazwa, sprzedawca, numer"
            />
          </Field>
        </div>
      </section>

      <section className="card card--flush">
        {costs.isLoading ? (
          <Loading />
        ) : costs.data && costs.data.items.length === 0 ? (
          <EmptyState label="Brak kosztów w wybranym okresie." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Data</th>
                  <th>Nazwa</th>
                  <th>Kategoria</th>
                  <th>Sprzedawca</th>
                  <th>Dokument</th>
                  <th className="num">Kwota</th>
                  <th>Metoda</th>
                  <th aria-label="Akcje" />
                </tr>
              </thead>
              <tbody>
                {costs.data?.items.map((cost) => (
                  <tr key={cost.id}>
                    <td data-label="Data">{formatDate(cost.cost_date)}</td>
                    <td data-label="Nazwa">{cost.name}</td>
                    <td data-label="Kategoria">{cost.category_name ?? '—'}</td>
                    <td data-label="Sprzedawca">{cost.vendor ?? '—'}</td>
                    <td data-label="Dokument">
                      {cost.invoice_number ?? '—'}
                      {cost.attachment_id ? (
                        <>
                          {' '}
                          <button
                            type="button"
                            className="btn btn--sm"
                            onClick={() =>
                              void downloadFile(`/api/attachments/${cost.attachment_id}`, undefined, cost.attachment_name ?? 'zalacznik').catch(
                                (error) => toast.error(error),
                              )
                            }
                          >
                            Pobierz
                          </button>
                        </>
                      ) : null}
                    </td>
                    <td data-label="Kwota" className="num">{formatMoney(cost.amount_gr)}</td>
                    <td data-label="Metoda">{optionLabel(meta?.payment_method, cost.payment_method)}</td>
                    <td data-label="">
                      <div className="btn-row">
                        <button type="button" className="btn btn--sm" onClick={() => openEdit(cost)}>
                          Edytuj
                        </button>
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() => {
                            if (window.confirm(`Usunąć koszt „${cost.name}”? Rekord pozostanie w historii.`)) {
                              deleteMutation.mutate(cost.id);
                            }
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
        {costs.data ? (
          <>
            <div className="pagination">
              <span>
                Suma na tej stronie: <strong>{formatMoney(total)}</strong>
              </span>
            </div>
            <Pagination
              page={costs.data.meta.page}
              pages={costs.data.meta.pages}
              total={costs.data.meta.total}
              onChange={(page) => setFilters((current) => ({ ...current, page }))}
            />
          </>
        ) : null}
      </section>

      {formOpen ? (
        <Modal title={editing ? 'Edycja kosztu' : 'Nowy koszt'} onClose={() => setFormOpen(false)}>
          <form className="stack" onSubmit={submit}>
            <div className="form-grid">
              <Field label="Data" htmlFor="k_date">
                <input
                  id="k_date"
                  type="date"
                  required
                  value={form.cost_date}
                  onChange={(event) => setForm({ ...form, cost_date: event.target.value })}
                />
              </Field>
              <Field label="Nazwa / rodzaj kosztu" htmlFor="k_name">
                <input
                  id="k_name"
                  required
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                />
              </Field>
              <Field label="Kategoria" htmlFor="k_category">
                <select
                  id="k_category"
                  value={form.category_id ?? ''}
                  onChange={(event) =>
                    setForm({ ...form, category_id: event.target.value ? Number(event.target.value) : null })
                  }
                >
                  <option value="">— brak —</option>
                  {categories.data
                    ?.filter((category) => category.is_active || category.id === form.category_id)
                    .map((category) => (
                      <option key={category.id} value={category.id}>
                        {category.name}
                      </option>
                    ))}
                </select>
              </Field>
              <Field label="Kwota (zł)" htmlFor="k_amount">
                <MoneyInput
                  id="k_amount"
                  valueGr={form.amount_gr}
                  onChangeGr={(value) => setForm({ ...form, amount_gr: value })}
                />
              </Field>
              <Field label="Sprzedawca" htmlFor="k_vendor">
                <input
                  id="k_vendor"
                  value={form.vendor ?? ''}
                  onChange={(event) => setForm({ ...form, vendor: event.target.value })}
                />
              </Field>
              <Field label="Numer faktury / paragonu" htmlFor="k_invoice">
                <input
                  id="k_invoice"
                  value={form.invoice_number ?? ''}
                  onChange={(event) => setForm({ ...form, invoice_number: event.target.value })}
                />
              </Field>
              <Field label="Metoda płatności" htmlFor="k_method">
                <select
                  id="k_method"
                  value={form.payment_method ?? ''}
                  onChange={(event) => setForm({ ...form, payment_method: event.target.value || null })}
                >
                  <option value="">—</option>
                  {meta?.payment_method.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field
                label="Dokument (PDF, JPG, PNG, WEBP)"
                htmlFor="k_file"
                hint={attachmentName ? `Wgrano: ${attachmentName}` : 'Plik zapisujemy pod losową nazwą'}
              >
                <input
                  id="k_file"
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.webp"
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) uploadMutation.mutate(file);
                  }}
                />
              </Field>
            </div>
            <Field label="Opis" htmlFor="k_description">
              <textarea
                id="k_description"
                value={form.description ?? ''}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </Field>
            <div className="form-actions">
              <button type="button" className="btn" onClick={() => setFormOpen(false)}>
                Anuluj
              </button>
              <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
                {saveMutation.isPending ? 'Zapisywanie…' : 'Zapisz koszt'}
              </button>
            </div>
          </form>
        </Modal>
      ) : null}

      {categoriesOpen ? (
        <Modal title="Kategorie kosztów" onClose={() => setCategoriesOpen(false)}>
          <div className="stack">
            <Alert variant="info">Kategorie są edytowalne. Używanej kategorii nie można usunąć — można ją wyłączyć.</Alert>
            <form
              className="row"
              onSubmit={(event) => {
                event.preventDefault();
                if (newCategory.trim()) categoryMutation.mutate(newCategory.trim());
              }}
            >
              <input
                value={newCategory}
                onChange={(event) => setNewCategory(event.target.value)}
                placeholder="Nazwa nowej kategorii"
                aria-label="Nazwa nowej kategorii"
              />
              <button type="submit" className="btn btn--primary" disabled={categoryMutation.isPending}>
                Dodaj
              </button>
            </form>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th>Nazwa</th>
                    <th>Status</th>
                    <th aria-label="Akcje" />
                  </tr>
                </thead>
                <tbody>
                  {categories.data?.map((category) => (
                    <tr key={category.id}>
                      <td data-label="Nazwa">{category.name}</td>
                      <td data-label="Status">{category.is_active ? 'aktywna' : 'wyłączona'}</td>
                      <td data-label="">
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() =>
                            categoryToggleMutation.mutate({ id: category.id, is_active: !category.is_active })
                          }
                        >
                          {category.is_active ? 'Wyłącz' : 'Włącz'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </Modal>
      ) : null}
    </>
  );
}
