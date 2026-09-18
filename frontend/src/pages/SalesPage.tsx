import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { salesApi } from '../api/sales';
import type { SaleQuery } from '../api/sales';
import { Alert, Badge, EmptyState, Loading, Modal, Pagination } from '../components/ui';
import { Field } from '../components/ui';
import { SaleForm } from '../features/SaleForm';
import { SaleDetails } from '../features/SaleDetails';
import { useMeta } from '../hooks/useMeta';
import { useToast } from '../hooks/useToast';
import { STATUS_BADGE, formatDate, formatMoney, optionLabel } from '../utils/format';
import type { Sale, SaleInput, SaleListItem } from '../types';

const EMPTY_FILTERS: SaleQuery = { page: 1, per_page: 25, sort_by: 'sale_date', sort_dir: 'desc' };

export function SalesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data: meta } = useMeta();
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState<SaleQuery>(EMPTY_FILTERS);
  const [formOpen, setFormOpen] = useState(searchParams.get('nowa') === '1');
  const [editing, setEditing] = useState<Sale | null>(null);
  const [detailsId, setDetailsId] = useState<number | null>(null);

  const list = useQuery({
    queryKey: ['sales', filters],
    queryFn: () => salesApi.list(filters),
  });

  const details = useQuery({
    queryKey: ['sale', detailsId],
    queryFn: () => salesApi.get(detailsId as number),
    enabled: detailsId !== null,
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ['sales'] });
    void queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    void queryClient.invalidateQueries({ queryKey: ['limits'] });
    void queryClient.invalidateQueries({ queryKey: ['registry'] });
    if (detailsId) void queryClient.invalidateQueries({ queryKey: ['sale', detailsId] });
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditing(null);
    if (searchParams.get('nowa')) {
      searchParams.delete('nowa');
      setSearchParams(searchParams, { replace: true });
    }
  };

  const createMutation = useMutation({
    mutationFn: (payload: SaleInput) => salesApi.create(payload),
    onSuccess: (sale) => {
      toast.success(`Dodano sprzedaż ${sale.document_number ?? ''}.`);
      invalidate();
      closeForm();
    },
    onError: (error) => toast.error(error),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: SaleInput }) => salesApi.update(id, payload),
    onSuccess: () => {
      toast.success('Zapisano zmiany w sprzedaży.');
      invalidate();
      closeForm();
    },
    onError: (error) => toast.error(error),
  });

  const deleteMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => salesApi.remove(id, reason),
    onSuccess: (response) => {
      toast.success(response.message);
      invalidate();
    },
    onError: (error) => toast.error(error),
  });

  const paymentMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Parameters<typeof salesApi.addPayment>[1] }) =>
      salesApi.addPayment(id, payload),
    onSuccess: () => {
      toast.success('Zapisano płatność.');
      invalidate();
    },
    onError: (error) => toast.error(error),
  });

  const deletePaymentMutation = useMutation({
    mutationFn: (paymentId: number) => salesApi.deletePayment(paymentId),
    onSuccess: () => {
      toast.success('Usunięto płatność.');
      invalidate();
    },
    onError: (error) => toast.error(error),
  });

  const correctionMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Parameters<typeof salesApi.addCorrection>[1] }) =>
      salesApi.addCorrection(id, payload),
    onSuccess: () => {
      toast.success('Zapisano korektę.');
      invalidate();
    },
    onError: (error) => toast.error(error),
  });

  const setFilter = (patch: Partial<SaleQuery>) => setFilters((current) => ({ ...current, ...patch, page: 1 }));

  const sortBy = (column: string) => {
    setFilters((current) => ({
      ...current,
      sort_by: column,
      sort_dir: current.sort_by === column && current.sort_dir === 'asc' ? 'desc' : 'asc',
    }));
  };

  const openEdit = async (sale: SaleListItem) => {
    try {
      const full = await salesApi.get(sale.id);
      setEditing(full);
      setFormOpen(true);
    } catch (error) {
      toast.error(error);
    }
  };

  const handleDelete = (sale: SaleListItem) => {
    const reason = window.prompt(
      `Usunięcie sprzedaży ${sale.document_number ?? sale.id} jest miękkie — dane zostają w historii.\nPodaj powód:`,
      '',
    );
    if (reason === null) return;
    deleteMutation.mutate({ id: sale.id, reason });
  };

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Sprzedaż</h1>
          <p>Rejestrowanie sprzedaży, płatności i korekt. Kwoty są zapisywane w groszach.</p>
        </div>
        <button type="button" className="btn btn--primary" onClick={() => setFormOpen(true)}>
          + Dodaj sprzedaż
        </button>
      </div>

      <section className="card">
        <div className="filters">
          <Field label="Data od" htmlFor="f_from">
            <input id="f_from" type="date" value={filters.date_from ?? ''} onChange={(e) => setFilter({ date_from: e.target.value || undefined })} />
          </Field>
          <Field label="Data do" htmlFor="f_to">
            <input id="f_to" type="date" value={filters.date_to ?? ''} onChange={(e) => setFilter({ date_to: e.target.value || undefined })} />
          </Field>
          <Field label="Rok" htmlFor="f_year">
            <input id="f_year" type="number" min={2000} max={2100} value={filters.year ?? ''} onChange={(e) => setFilter({ year: e.target.value ? Number(e.target.value) : undefined })} />
          </Field>
          <Field label="Kwartał" htmlFor="f_quarter">
            <select id="f_quarter" value={filters.quarter ?? ''} onChange={(e) => setFilter({ quarter: e.target.value ? Number(e.target.value) : undefined })}>
              <option value="">wszystkie</option>
              <option value="1">I</option>
              <option value="2">II</option>
              <option value="3">III</option>
              <option value="4">IV</option>
            </select>
          </Field>
          <Field label="Miesiąc" htmlFor="f_month">
            <select id="f_month" value={filters.month ?? ''} onChange={(e) => setFilter({ month: e.target.value ? Number(e.target.value) : undefined })}>
              <option value="">wszystkie</option>
              {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                <option key={month} value={month}>
                  {String(month).padStart(2, '0')}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Kanał" htmlFor="f_channel">
            <select id="f_channel" value={filters.sales_channel ?? ''} onChange={(e) => setFilter({ sales_channel: e.target.value || undefined })}>
              <option value="">wszystkie</option>
              {meta?.sales_channel.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Metoda płatności" htmlFor="f_method">
            <select id="f_method" value={filters.payment_method ?? ''} onChange={(e) => setFilter({ payment_method: e.target.value || undefined })}>
              <option value="">wszystkie</option>
              {meta?.payment_method.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Status płatności" htmlFor="f_status">
            <select id="f_status" value={filters.payment_status ?? ''} onChange={(e) => setFilter({ payment_status: e.target.value || undefined })}>
              <option value="">wszystkie</option>
              {meta?.payment_status.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Typ klienta" htmlFor="f_customer">
            <select id="f_customer" value={filters.customer_type ?? ''} onChange={(e) => setFilter({ customer_type: e.target.value || undefined })}>
              <option value="">wszyscy</option>
              {meta?.customer_type.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Produkt" htmlFor="f_product">
            <input id="f_product" value={filters.product ?? ''} onChange={(e) => setFilter({ product: e.target.value || undefined })} placeholder="nazwa produktu" />
          </Field>
          <Field label="Szukaj" htmlFor="f_search">
            <input id="f_search" value={filters.search ?? ''} onChange={(e) => setFilter({ search: e.target.value || undefined })} placeholder="numer, klient, opis" />
          </Field>
          <div className="field">
            <span className="field__label">&nbsp;</span>
            <button type="button" className="btn" onClick={() => setFilters(EMPTY_FILTERS)}>
              Wyczyść filtry
            </button>
          </div>
        </div>
      </section>

      <section className="card card--flush">
        {list.isLoading ? (
          <Loading />
        ) : list.error ? (
          <Alert variant="danger">Nie udało się pobrać listy sprzedaży.</Alert>
        ) : list.data && list.data.items.length === 0 ? (
          <EmptyState label="Brak sprzedaży spełniającej wybrane kryteria." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th className="sortable" onClick={() => sortBy('sale_date')}>Data</th>
                  <th className="sortable" onClick={() => sortBy('document_number')}>Numer</th>
                  <th>Opis</th>
                  <th>Klient</th>
                  <th className="num sortable" onClick={() => sortBy('total_gr')}>Wartość</th>
                  <th className="num sortable" onClick={() => sortBy('accrued_revenue_gr')}>Przychód należny</th>
                  <th className="num">Otrzymano</th>
                  <th>Status</th>
                  <th aria-label="Akcje" />
                </tr>
              </thead>
              <tbody>
                {list.data?.items.map((sale) => (
                  <tr key={sale.id}>
                    <td data-label="Data">{formatDate(sale.sale_date)}</td>
                    <td data-label="Numer">{sale.document_number ?? '—'}</td>
                    <td data-label="Opis">{sale.description ?? '—'}</td>
                    <td data-label="Klient">
                      {sale.customer_name ?? '—'}
                      <br />
                      <span className="small muted">{optionLabel(meta?.customer_type, sale.customer_type)}</span>
                    </td>
                    <td data-label="Wartość" className="num">{formatMoney(sale.total_gr)}</td>
                    <td data-label="Przychód należny" className="num">{formatMoney(sale.accrued_revenue_gr)}</td>
                    <td data-label="Otrzymano" className="num">{formatMoney(sale.paid_amount_gr)}</td>
                    <td data-label="Status">
                      <Badge variant={STATUS_BADGE[sale.payment_status]}>
                        {optionLabel(meta?.payment_status, sale.payment_status)}
                      </Badge>
                    </td>
                    <td data-label="">
                      <div className="btn-row">
                        <button type="button" className="btn btn--sm" onClick={() => setDetailsId(sale.id)}>
                          Szczegóły
                        </button>
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() => void openEdit(sale)}
                          disabled={sale.is_cancelled}
                        >
                          Edytuj
                        </button>
                        <button type="button" className="btn btn--sm" onClick={() => handleDelete(sale)}>
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
        {list.data ? (
          <Pagination
            page={list.data.meta.page}
            pages={list.data.meta.pages}
            total={list.data.meta.total}
            onChange={(page) => setFilters((current) => ({ ...current, page }))}
          />
        ) : null}
      </section>

      {formOpen ? (
        <Modal title={editing ? `Edycja sprzedaży ${editing.document_number ?? ''}` : 'Nowa sprzedaż'} onClose={closeForm} wide>
          <SaleForm
            sale={editing}
            submitting={createMutation.isPending || updateMutation.isPending}
            onCancel={closeForm}
            onSubmit={(payload) =>
              editing ? updateMutation.mutate({ id: editing.id, payload }) : createMutation.mutate(payload)
            }
          />
        </Modal>
      ) : null}

      {detailsId !== null ? (
        <Modal
          title={`Sprzedaż ${details.data?.document_number ?? ''}`}
          onClose={() => setDetailsId(null)}
          wide
        >
          {details.isLoading || !details.data ? (
            <Loading />
          ) : (
            <SaleDetails
              sale={details.data}
              busy={paymentMutation.isPending || correctionMutation.isPending || deletePaymentMutation.isPending}
              onAddPayment={(payload) => paymentMutation.mutate({ id: details.data!.id, payload })}
              onDeletePayment={(paymentId) => deletePaymentMutation.mutate(paymentId)}
              onAddCorrection={(payload) => correctionMutation.mutate({ id: details.data!.id, payload })}
            />
          )}
        </Modal>
      ) : null}
    </>
  );
}
