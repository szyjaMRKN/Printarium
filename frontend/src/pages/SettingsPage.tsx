import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { auditApi, settingsApi } from '../api/resources';
import { usersApi, authApi } from '../api/auth';
import { Alert, Badge, Field, Loading, MoneyInput, Pagination } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { useMeta } from '../hooks/useMeta';
import { useTheme } from '../hooks/useTheme';
import { useToast } from '../hooks/useToast';
import { currentYear, formatDateTime, formatMoney, formatPercent, optionLabel } from '../utils/format';
import type { SettingsValues } from '../types';

type Tab = 'firma' | 'rok' | 'aplikacja' | 'uzytkownicy' | 'dziennik' | 'konto';

export function SettingsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { session } = useAuth();
  const { data: meta } = useMeta();
  const { mode, setMode } = useTheme();
  const [tab, setTab] = useState<Tab>('firma');

  const settings = useQuery({ queryKey: ['settings'], queryFn: settingsApi.get });
  const fiscalYears = useQuery({ queryKey: ['fiscal-years'], queryFn: settingsApi.fiscalYears });
  const [values, setValues] = useState<SettingsValues>({});

  useEffect(() => {
    if (settings.data) setValues(settings.data.values);
  }, [settings.data]);

  const saveSettings = useMutation({
    mutationFn: (payload: SettingsValues) => settingsApi.update(payload),
    onSuccess: () => {
      toast.success('Ustawienia zostały zapisane.');
      void queryClient.invalidateQueries({ queryKey: ['settings'] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      void queryClient.invalidateQueries({ queryKey: ['limits'] });
    },
    onError: (error) => toast.error(error),
  });

  const isAdmin = session?.user.role === 'admin';

  if (settings.isLoading) return <Loading />;

  const setValue = (key: string, value: string | number | boolean) =>
    setValues((current) => ({ ...current, [key]: value }));

  const submitGroup = (keys: string[]) => (event: FormEvent) => {
    event.preventDefault();
    const payload: SettingsValues = {};
    keys.forEach((key) => {
      if (key in values) payload[key] = values[key];
    });
    saveSettings.mutate(payload);
  };

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Ustawienia</h1>
          <p>
            Wszystkie limity i progi są zapisane w bazie — zmieniasz je tutaj, bez zmian w kodzie. Wersja aplikacji:{' '}
            {meta?.app.version ?? '—'}
          </p>
        </div>
      </div>

      {!isAdmin ? <Alert variant="info">Zmiana ustawień wymaga roli administratora.</Alert> : null}

      <div className="tabs">
        {(
          [
            ['firma', 'Dane sprzedawcy i dokumenty'],
            ['rok', 'Rok podatkowy i limity'],
            ['aplikacja', 'Aplikacja'],
            ['uzytkownicy', 'Użytkownicy'],
            ['dziennik', 'Dziennik zmian'],
            ['konto', 'Moje konto'],
          ] as Array<[Tab, string]>
        ).map(([key, label]) => (
          <button key={key} type="button" className={tab === key ? 'tab is-active' : 'tab'} onClick={() => setTab(key)}>
            {label}
          </button>
        ))}
      </div>

      {tab === 'firma' ? (
        <form
          className="card stack"
          onSubmit={submitGroup([
            'company.first_name',
            'company.last_name',
            'company.business_name',
            'company.address',
            'company.postal_code',
            'company.city',
            'company.nip',
            'company.email',
            'company.phone',
            'company.bank_account',
            'invoicing.number_format',
            'invoicing.reset_period',
            'invoicing.default_document_type',
            'invoicing.default_payment_days',
            'invoicing.footer_note',
          ])}
        >
          <h2 className="card__title">Dane sprzedawcy</h2>
          <div className="form-grid">
            {[
              ['company.first_name', 'Imię'],
              ['company.last_name', 'Nazwisko'],
              ['company.business_name', 'Nazwa (opcjonalnie)'],
              ['company.address', 'Adres'],
              ['company.postal_code', 'Kod pocztowy'],
              ['company.city', 'Miejscowość'],
              ['company.nip', 'NIP (opcjonalny)'],
              ['company.email', 'E-mail'],
              ['company.phone', 'Telefon'],
              ['company.bank_account', 'Numer rachunku bankowego'],
            ].map(([key, label]) => (
              <Field key={key} label={label} htmlFor={key}>
                <input
                  id={key}
                  value={String(values[key] ?? '')}
                  disabled={!isAdmin}
                  onChange={(event) => setValue(key, event.target.value)}
                />
              </Field>
            ))}
          </div>

          <h2 className="card__title">Numeracja dokumentów</h2>
          <div className="form-grid">
            <Field
              label="Format numeru"
              htmlFor="invoicing.number_format"
              hint="Znaczniki: {nr}, {mm}, {rrrr}, {rr}"
            >
              <input
                id="invoicing.number_format"
                value={String(values['invoicing.number_format'] ?? '')}
                disabled={!isAdmin}
                onChange={(event) => setValue('invoicing.number_format', event.target.value)}
              />
            </Field>
            <Field label="Reset numeracji" htmlFor="invoicing.reset_period">
              <select
                id="invoicing.reset_period"
                value={String(values['invoicing.reset_period'] ?? 'month')}
                disabled={!isAdmin}
                onChange={(event) => setValue('invoicing.reset_period', event.target.value)}
              >
                <option value="month">co miesiąc</option>
                <option value="year">co rok</option>
              </select>
            </Field>
            <Field label="Domyślny termin płatności (dni)" htmlFor="invoicing.default_payment_days">
              <input
                id="invoicing.default_payment_days"
                type="number"
                min={0}
                max={365}
                value={Number(values['invoicing.default_payment_days'] ?? 7)}
                disabled={!isAdmin}
                onChange={(event) => setValue('invoicing.default_payment_days', Number(event.target.value))}
              />
            </Field>
          </div>
          <Field label="Stopka dokumentu" htmlFor="invoicing.footer_note">
            <textarea
              id="invoicing.footer_note"
              value={String(values['invoicing.footer_note'] ?? '')}
              disabled={!isAdmin}
              onChange={(event) => setValue('invoicing.footer_note', event.target.value)}
            />
          </Field>
          <div className="form-actions">
            <button type="submit" className="btn btn--primary" disabled={!isAdmin || saveSettings.isPending}>
              Zapisz
            </button>
          </div>
        </form>
      ) : null}

      {tab === 'rok' ? <FiscalYearTab isAdmin={isAdmin} years={fiscalYears.data ?? []} /> : null}

      {tab === 'aplikacja' ? (
        <form
          className="card stack"
          onSubmit={submitGroup([
            'fiscal.default_year',
            'fiscal.shipping_counts_as_revenue',
            'fiscal.warning_percent',
            'fiscal.strong_warning_percent',
            'uploads.max_size_mb',
            'backup.auto_enabled',
            'backup.auto_hour',
            'backup.auto_minute',
            'backup.retention',
          ])}
        >
          <h2 className="card__title">Zasady liczenia</h2>
          <div className="form-grid">
            <Field label="Domyślny rok podatkowy" htmlFor="fiscal.default_year" hint="0 = rok bieżący">
              <input
                id="fiscal.default_year"
                type="number"
                value={Number(values['fiscal.default_year'] ?? 0)}
                disabled={!isAdmin}
                onChange={(event) => setValue('fiscal.default_year', Number(event.target.value))}
              />
            </Field>
            <Field label="Próg ostrzeżenia (%)" htmlFor="fiscal.warning_percent">
              <input
                id="fiscal.warning_percent"
                type="number"
                min={1}
                max={100}
                value={Number(values['fiscal.warning_percent'] ?? 75)}
                disabled={!isAdmin}
                onChange={(event) => setValue('fiscal.warning_percent', Number(event.target.value))}
              />
            </Field>
            <Field label="Próg mocnego ostrzeżenia (%)" htmlFor="fiscal.strong_warning_percent">
              <input
                id="fiscal.strong_warning_percent"
                type="number"
                min={1}
                max={100}
                value={Number(values['fiscal.strong_warning_percent'] ?? 90)}
                disabled={!isAdmin}
                onChange={(event) => setValue('fiscal.strong_warning_percent', Number(event.target.value))}
              />
            </Field>
            <Field
              label="Maksymalny rozmiar pliku (MB)"
              htmlFor="uploads.max_size_mb"
              hint="Nie większy niż limit serwera (MAX_UPLOAD_MB)"
            >
              <input
                id="uploads.max_size_mb"
                type="number"
                min={1}
                max={100}
                value={Number(values['uploads.max_size_mb'] ?? 10)}
                disabled={!isAdmin}
                onChange={(event) => setValue('uploads.max_size_mb', Number(event.target.value))}
              />
            </Field>
          </div>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={Boolean(values['fiscal.shipping_counts_as_revenue'])}
              disabled={!isAdmin}
              onChange={(event) => setValue('fiscal.shipping_counts_as_revenue', event.target.checked)}
            />
            Koszt wysyłki pobrany od klienta wlicza się do przychodu należnego
          </label>

          <h2 className="card__title">Kopie zapasowe</h2>
          <div className="form-grid">
            <Field label="Godzina automatycznej kopii" htmlFor="backup.auto_hour">
              <input
                id="backup.auto_hour"
                type="number"
                min={0}
                max={23}
                value={Number(values['backup.auto_hour'] ?? 3)}
                disabled={!isAdmin}
                onChange={(event) => setValue('backup.auto_hour', Number(event.target.value))}
              />
            </Field>
            <Field label="Minuta" htmlFor="backup.auto_minute">
              <input
                id="backup.auto_minute"
                type="number"
                min={0}
                max={59}
                value={Number(values['backup.auto_minute'] ?? 0)}
                disabled={!isAdmin}
                onChange={(event) => setValue('backup.auto_minute', Number(event.target.value))}
              />
            </Field>
            <Field label="Liczba przechowywanych kopii" htmlFor="backup.retention">
              <input
                id="backup.retention"
                type="number"
                min={1}
                max={365}
                value={Number(values['backup.retention'] ?? 30)}
                disabled={!isAdmin}
                onChange={(event) => setValue('backup.retention', Number(event.target.value))}
              />
            </Field>
          </div>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={Boolean(values['backup.auto_enabled'])}
              disabled={!isAdmin}
              onChange={(event) => setValue('backup.auto_enabled', event.target.checked)}
            />
            Twórz kopie automatycznie
          </label>

          <h2 className="card__title">Wygląd</h2>
          <Field label="Motyw" htmlFor="theme_mode">
            <select id="theme_mode" value={mode} onChange={(event) => setMode(event.target.value as typeof mode)}>
              <option value="system">jak w systemie</option>
              <option value="light">jasny</option>
              <option value="dark">ciemny</option>
            </select>
          </Field>

          <div className="form-actions">
            <button type="submit" className="btn btn--primary" disabled={!isAdmin || saveSettings.isPending}>
              Zapisz
            </button>
          </div>
        </form>
      ) : null}

      {tab === 'uzytkownicy' ? <UsersTab isAdmin={isAdmin} /> : null}
      {tab === 'dziennik' ? <AuditTab /> : null}
      {tab === 'konto' ? <AccountTab /> : null}
    </>
  );
}

function FiscalYearTab({ isAdmin, years }: { isAdmin: boolean; years: Array<import('../types').FiscalYear> }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [year, setYear] = useState(currentYear());
  const current = years.find((item) => item.year === year);
  const [draft, setDraft] = useState<Partial<import('../types').FiscalYear>>({});

  useEffect(() => {
    setDraft(current ?? {});
  }, [current]);

  const mutation = useMutation({
    mutationFn: (payload: Partial<import('../types').FiscalYear>) => settingsApi.updateFiscalYear(year, payload),
    onSuccess: () => {
      toast.success('Zapisano parametry roku podatkowego.');
      void queryClient.invalidateQueries({ queryKey: ['fiscal-years'] });
      void queryClient.invalidateQueries({ queryKey: ['limits'] });
      void queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
    onError: (error) => toast.error(error),
  });

  const computedLimit =
    ((draft.minimum_wage_gr ?? 0) * (draft.limit_multiplier_permille ?? 0)) / 1000;

  return (
    <form
      className="card stack"
      onSubmit={(event) => {
        event.preventDefault();
        mutation.mutate({
          minimum_wage_gr: draft.minimum_wage_gr,
          limit_multiplier_permille: draft.limit_multiplier_permille,
          quarterly_limit_override_gr: draft.quarterly_limit_override_gr || undefined,
          ksef_monthly_threshold_gr: draft.ksef_monthly_threshold_gr,
          cash_register_yearly_threshold_gr: draft.cash_register_yearly_threshold_gr,
          note: draft.note ?? null,
        });
      }}
    >
      <Alert variant="info">
        Limit kwartalny = minimalne wynagrodzenie × mnożnik. Dla 2026 r. domyślnie 4 806,00 zł × 225% = 10 813,50 zł.
        Możesz też wpisać limit ręcznie — wtedy ma pierwszeństwo.
      </Alert>

      <div className="form-grid">
        <Field label="Rok podatkowy" htmlFor="fy_year">
          <input
            id="fy_year"
            type="number"
            min={2000}
            max={2100}
            value={year}
            onChange={(event) => setYear(Number(event.target.value) || currentYear())}
          />
        </Field>
        <Field label="Minimalne wynagrodzenie" htmlFor="fy_wage">
          <MoneyInput
            id="fy_wage"
            valueGr={draft.minimum_wage_gr ?? 0}
            onChangeGr={(value) => setDraft((state) => ({ ...state, minimum_wage_gr: value }))}
          />
        </Field>
        <Field label="Mnożnik limitu (%)" htmlFor="fy_multiplier" hint="225% = 2250 promili">
          <input
            id="fy_multiplier"
            type="number"
            step={0.1}
            value={(draft.limit_multiplier_permille ?? 0) / 10}
            onChange={(event) =>
              setDraft((state) => ({ ...state, limit_multiplier_permille: Math.round(Number(event.target.value) * 10) }))
            }
          />
        </Field>
        <Field label="Wyliczony limit kwartalny" htmlFor="fy_computed">
          <input id="fy_computed" readOnly className="num" value={formatMoney(computedLimit)} />
        </Field>
        <Field label="Limit kwartalny — wartość ręczna" htmlFor="fy_override" hint="0 = wyłączone">
          <MoneyInput
            id="fy_override"
            valueGr={draft.quarterly_limit_override_gr ?? 0}
            onChangeGr={(value) => setDraft((state) => ({ ...state, quarterly_limit_override_gr: value }))}
          />
        </Field>
        <Field label="Próg KSeF (miesięcznie)" htmlFor="fy_ksef">
          <MoneyInput
            id="fy_ksef"
            valueGr={draft.ksef_monthly_threshold_gr ?? 0}
            onChangeGr={(value) => setDraft((state) => ({ ...state, ksef_monthly_threshold_gr: value }))}
          />
        </Field>
        <Field label="Próg kasy fiskalnej (rocznie)" htmlFor="fy_cash">
          <MoneyInput
            id="fy_cash"
            valueGr={draft.cash_register_yearly_threshold_gr ?? 0}
            onChangeGr={(value) => setDraft((state) => ({ ...state, cash_register_yearly_threshold_gr: value }))}
          />
        </Field>
      </div>

      <Field label="Notatka" htmlFor="fy_note">
        <textarea
          id="fy_note"
          value={draft.note ?? ''}
          onChange={(event) => setDraft((state) => ({ ...state, note: event.target.value }))}
        />
      </Field>

      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={!isAdmin || mutation.isPending}>
          Zapisz parametry roku
        </button>
      </div>

      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th>Rok</th>
              <th className="num">Minimalne wynagrodzenie</th>
              <th className="num">Mnożnik</th>
              <th className="num">Limit kwartalny</th>
              <th className="num">Próg KSeF</th>
              <th className="num">Próg kasy fiskalnej</th>
            </tr>
          </thead>
          <tbody>
            {years.map((item) => (
              <tr key={item.year}>
                <td data-label="Rok">{item.year}</td>
                <td data-label="Minimalne wynagrodzenie" className="num">{formatMoney(item.minimum_wage_gr)}</td>
                <td data-label="Mnożnik" className="num">{formatPercent(item.limit_multiplier_permille / 10, 1)}</td>
                <td data-label="Limit kwartalny" className="num">{formatMoney(item.quarterly_limit_gr)}</td>
                <td data-label="Próg KSeF" className="num">{formatMoney(item.ksef_monthly_threshold_gr)}</td>
                <td data-label="Próg kasy" className="num">{formatMoney(item.cash_register_yearly_threshold_gr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </form>
  );
}

function UsersTab({ isAdmin }: { isAdmin: boolean }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data: meta } = useMeta();
  const users = useQuery({ queryKey: ['users'], queryFn: usersApi.list, enabled: isAdmin });
  const [form, setForm] = useState({ login: '', password: '', email: '', role: 'ksiegowy' });

  const createMutation = useMutation({
    mutationFn: () =>
      usersApi.create({ login: form.login, password: form.password, email: form.email || null, role: form.role }),
    onSuccess: () => {
      toast.success('Dodano użytkownika.');
      setForm({ login: '', password: '', email: '', role: 'ksiegowy' });
      void queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error) => toast.error(error),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) => usersApi.update(id, { is_active }),
    onSuccess: () => {
      toast.success('Zapisano zmianę.');
      void queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error) => toast.error(error),
  });

  if (!isAdmin) return <Alert variant="info">Zarządzanie użytkownikami wymaga roli administratora.</Alert>;

  return (
    <div className="stack">
      <form
        className="card stack"
        onSubmit={(event) => {
          event.preventDefault();
          createMutation.mutate();
        }}
      >
        <h2 className="card__title">Nowy użytkownik</h2>
        <div className="form-grid">
          <Field label="Login" htmlFor="u_login">
            <input id="u_login" required minLength={3} value={form.login} onChange={(event) => setForm({ ...form, login: event.target.value })} />
          </Field>
          <Field label="Hasło" htmlFor="u_password" hint="Min. 10 znaków, małe i wielkie litery oraz cyfra">
            <input
              id="u_password"
              type="password"
              required
              minLength={10}
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
            />
          </Field>
          <Field label="E-mail" htmlFor="u_email">
            <input id="u_email" type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          </Field>
          <Field label="Rola" htmlFor="u_role">
            <select id="u_role" value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
              {meta?.user_role.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </Field>
        </div>
        <div className="form-actions">
          <button type="submit" className="btn btn--primary" disabled={createMutation.isPending}>
            Dodaj użytkownika
          </button>
        </div>
      </form>

      <section className="card card--flush">
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Login</th>
                <th>E-mail</th>
                <th>Rola</th>
                <th>Status</th>
                <th>Ostatnie logowanie</th>
                <th aria-label="Akcje" />
              </tr>
            </thead>
            <tbody>
              {users.data?.map((user) => (
                <tr key={user.id}>
                  <td data-label="Login">{user.login}</td>
                  <td data-label="E-mail">{user.email ?? '—'}</td>
                  <td data-label="Rola">{optionLabel(meta?.user_role, user.role)}</td>
                  <td data-label="Status">
                    <Badge variant={user.is_active ? 'badge--success' : 'badge--danger'}>
                      {user.is_active ? 'aktywny' : 'nieaktywny'}
                    </Badge>
                  </td>
                  <td data-label="Ostatnie logowanie">{formatDateTime(user.last_login_at)}</td>
                  <td data-label="">
                    <button
                      type="button"
                      className="btn btn--sm"
                      onClick={() => toggleMutation.mutate({ id: user.id, is_active: !user.is_active })}
                    >
                      {user.is_active ? 'Wyłącz' : 'Włącz'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

function AuditTab() {
  const [page, setPage] = useState(1);
  const logs = useQuery({
    queryKey: ['audit', page],
    queryFn: () => auditApi.list({ page, per_page: 50 }),
  });

  return (
    <section className="card card--flush">
      {logs.isLoading ? (
        <Loading />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Czas</th>
                <th>Użytkownik</th>
                <th>Operacja</th>
                <th>Obiekt</th>
                <th>Opis</th>
              </tr>
            </thead>
            <tbody>
              {logs.data?.items.map((entry) => (
                <tr key={entry.id}>
                  <td data-label="Czas">{formatDateTime(entry.created_at)}</td>
                  <td data-label="Użytkownik">{entry.user_login ?? '—'}</td>
                  <td data-label="Operacja">{entry.action.replaceAll('_', ' ')}</td>
                  <td data-label="Obiekt">
                    {entry.entity_type ? `${entry.entity_type}${entry.entity_id ? ` #${entry.entity_id}` : ''}` : '—'}
                  </td>
                  <td data-label="Opis">{entry.description ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {logs.data ? (
        <Pagination page={logs.data.meta.page} pages={logs.data.meta.pages} total={logs.data.meta.total} onChange={setPage} />
      ) : null}
    </section>
  );
}

function AccountTab() {
  const toast = useToast();
  const { session } = useAuth();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [repeat, setRepeat] = useState('');

  const mutation = useMutation({
    mutationFn: () => authApi.changePassword(current, next),
    onSuccess: () => {
      toast.success('Hasło zostało zmienione. Pozostałe sesje zostały wylogowane.');
      setCurrent('');
      setNext('');
      setRepeat('');
    },
    onError: (error) => toast.error(error),
  });

  return (
    <form
      className="card stack"
      onSubmit={(event) => {
        event.preventDefault();
        if (next !== repeat) {
          toast.push('Nowe hasła nie są identyczne.', 'error');
          return;
        }
        mutation.mutate();
      }}
    >
      <h2 className="card__title">Moje konto</h2>
      <p className="small muted">
        Zalogowany jako <strong>{session?.user.login}</strong> ({session?.user.role}).
      </p>
      <div className="form-grid">
        <Field label="Aktualne hasło" htmlFor="pw_current">
          <input id="pw_current" type="password" required value={current} onChange={(event) => setCurrent(event.target.value)} />
        </Field>
        <Field label="Nowe hasło" htmlFor="pw_new" hint="Min. 10 znaków, małe i wielkie litery oraz cyfra">
          <input id="pw_new" type="password" required minLength={10} value={next} onChange={(event) => setNext(event.target.value)} />
        </Field>
        <Field label="Powtórz nowe hasło" htmlFor="pw_repeat">
          <input id="pw_repeat" type="password" required minLength={10} value={repeat} onChange={(event) => setRepeat(event.target.value)} />
        </Field>
      </div>
      <div className="form-actions">
        <button type="submit" className="btn btn--primary" disabled={mutation.isPending}>
          Zmień hasło
        </button>
      </div>
    </form>
  );
}
