import { useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { productsApi } from '../api/resources';
import type { ProductInput } from '../api/resources';
import { EmptyState, Field, Loading, Modal, MoneyInput, Pagination } from '../components/ui';
import { useToast } from '../hooks/useToast';
import { formatMoney } from '../utils/format';
import type { Product } from '../types';

function emptyProduct(): ProductInput {
  return {
    name: '',
    sku: null,
    model: null,
    category: null,
    price_gr: 0,
    production_cost_gr: 0,
    is_active: true,
    description: null,
  };
}

export function ProductsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Product | null>(null);
  const [form, setForm] = useState<ProductInput>(emptyProduct());

  const products = useQuery({
    queryKey: ['products', { search, page }],
    queryFn: () => productsApi.list({ search: search || undefined, page, per_page: 25 }),
  });

  const saveMutation = useMutation({
    mutationFn: (payload: ProductInput) =>
      editing ? productsApi.update(editing.id, payload) : productsApi.create(payload),
    onSuccess: () => {
      toast.success(editing ? 'Zapisano zmiany produktu.' : 'Dodano produkt.');
      void queryClient.invalidateQueries({ queryKey: ['products'] });
      setFormOpen(false);
      setEditing(null);
      setForm(emptyProduct());
    },
    onError: (error) => toast.error(error),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => productsApi.remove(id),
    onSuccess: () => {
      toast.success('Produkt został usunięty.');
      void queryClient.invalidateQueries({ queryKey: ['products'] });
    },
    onError: (error) => toast.error(error),
  });

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!form.name.trim()) {
      toast.push('Podaj nazwę produktu.', 'error');
      return;
    }
    saveMutation.mutate(form);
  };

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Produkty</h1>
          <p>Baza produktów używana przy dodawaniu sprzedaży i w raportach.</p>
        </div>
        <button
          type="button"
          className="btn btn--primary"
          onClick={() => {
            setEditing(null);
            setForm(emptyProduct());
            setFormOpen(true);
          }}
        >
          + Dodaj produkt
        </button>
      </div>

      <section className="card">
        <div className="filters">
          <Field label="Szukaj" htmlFor="p_search">
            <input
              id="p_search"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setPage(1);
              }}
              placeholder="nazwa, SKU, model"
            />
          </Field>
        </div>
      </section>

      <section className="card card--flush">
        {products.isLoading ? (
          <Loading />
        ) : products.data && products.data.items.length === 0 ? (
          <EmptyState label="Brak produktów. Dodaj pierwszy produkt, aby przyspieszyć wpisywanie sprzedaży." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Nazwa</th>
                  <th>SKU</th>
                  <th>Model</th>
                  <th>Kategoria</th>
                  <th className="num">Cena</th>
                  <th className="num">Koszt produkcji</th>
                  <th className="num">Marża</th>
                  <th>Status</th>
                  <th aria-label="Akcje" />
                </tr>
              </thead>
              <tbody>
                {products.data?.items.map((product) => (
                  <tr key={product.id}>
                    <td data-label="Nazwa">{product.name}</td>
                    <td data-label="SKU">{product.sku ?? '—'}</td>
                    <td data-label="Model">{product.model ?? '—'}</td>
                    <td data-label="Kategoria">{product.category ?? '—'}</td>
                    <td data-label="Cena" className="num">{formatMoney(product.price_gr)}</td>
                    <td data-label="Koszt produkcji" className="num">{formatMoney(product.production_cost_gr)}</td>
                    <td data-label="Marża" className="num">
                      {formatMoney(product.price_gr - product.production_cost_gr)}
                    </td>
                    <td data-label="Status">{product.is_active ? 'aktywny' : 'nieaktywny'}</td>
                    <td data-label="">
                      <div className="btn-row">
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() => {
                            setEditing(product);
                            setForm({
                              name: product.name,
                              sku: product.sku,
                              model: product.model,
                              category: product.category,
                              price_gr: product.price_gr,
                              production_cost_gr: product.production_cost_gr,
                              is_active: product.is_active,
                              description: product.description,
                            });
                            setFormOpen(true);
                          }}
                        >
                          Edytuj
                        </button>
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() => {
                            if (window.confirm(`Usunąć produkt „${product.name}”?`)) deleteMutation.mutate(product.id);
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
        {products.data ? (
          <Pagination
            page={products.data.meta.page}
            pages={products.data.meta.pages}
            total={products.data.meta.total}
            onChange={setPage}
          />
        ) : null}
      </section>

      {formOpen ? (
        <Modal title={editing ? 'Edycja produktu' : 'Nowy produkt'} onClose={() => setFormOpen(false)}>
          <form className="stack" onSubmit={submit}>
            <div className="form-grid">
              <Field label="Nazwa" htmlFor="pr_name">
                <input
                  id="pr_name"
                  required
                  value={form.name}
                  onChange={(event) => setForm({ ...form, name: event.target.value })}
                />
              </Field>
              <Field label="SKU" htmlFor="pr_sku">
                <input id="pr_sku" value={form.sku ?? ''} onChange={(event) => setForm({ ...form, sku: event.target.value })} />
              </Field>
              <Field label="Model" htmlFor="pr_model">
                <input id="pr_model" value={form.model ?? ''} onChange={(event) => setForm({ ...form, model: event.target.value })} />
              </Field>
              <Field label="Kategoria" htmlFor="pr_category">
                <input
                  id="pr_category"
                  value={form.category ?? ''}
                  onChange={(event) => setForm({ ...form, category: event.target.value })}
                />
              </Field>
              <Field label="Cena (zł)" htmlFor="pr_price">
                <MoneyInput id="pr_price" valueGr={form.price_gr} onChangeGr={(value) => setForm({ ...form, price_gr: value })} />
              </Field>
              <Field label="Koszt produkcji (zł)" htmlFor="pr_cost">
                <MoneyInput
                  id="pr_cost"
                  valueGr={form.production_cost_gr}
                  onChangeGr={(value) => setForm({ ...form, production_cost_gr: value })}
                />
              </Field>
            </div>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={form.is_active}
                onChange={(event) => setForm({ ...form, is_active: event.target.checked })}
              />
              Produkt aktywny (widoczny przy dodawaniu sprzedaży)
            </label>
            <Field label="Opis" htmlFor="pr_description">
              <textarea
                id="pr_description"
                value={form.description ?? ''}
                onChange={(event) => setForm({ ...form, description: event.target.value })}
              />
            </Field>
            <div className="form-actions">
              <button type="button" className="btn" onClick={() => setFormOpen(false)}>
                Anuluj
              </button>
              <button type="submit" className="btn btn--primary" disabled={saveMutation.isPending}>
                Zapisz produkt
              </button>
            </div>
          </form>
        </Modal>
      ) : null}
    </>
  );
}
