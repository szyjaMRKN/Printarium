import { useState } from 'react';
import type { FormEvent } from 'react';
import { useAuth } from '../hooks/useAuth';
import { toErrorMessage } from '../hooks/useToast';
import { Alert, Field } from '../components/ui';

export function LoginPage() {
  const { login } = useAuth();
  const [userLogin, setUserLogin] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(userLogin, password);
    } catch (loginError) {
      setError(toErrorMessage(loginError, 'Nie udało się zalogować.'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login">
      <form className="login__card" onSubmit={handleSubmit}>
        <div className="login__brand">
          <img src="/icons/icon.svg" alt="" width={36} height={36} />
          Ewidencja działalności nierejestrowanej
        </div>
        <p className="muted small">
          Dostęp do danych wymaga zalogowania. Sesja jest przechowywana w bezpiecznym ciasteczku.
        </p>

        {error ? <Alert variant="danger">{error}</Alert> : null}

        <Field label="Login" htmlFor="login">
          <input
            id="login"
            name="login"
            autoComplete="username"
            required
            value={userLogin}
            onChange={(event) => setUserLogin(event.target.value)}
          />
        </Field>

        <Field label="Hasło" htmlFor="password">
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </Field>

        <button type="submit" className="btn btn--primary btn--block" disabled={busy}>
          {busy ? 'Logowanie…' : 'Zaloguj się'}
        </button>
      </form>
    </div>
  );
}
