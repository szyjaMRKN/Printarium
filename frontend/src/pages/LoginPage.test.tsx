import { describe, expect, it, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LoginPage } from './LoginPage';
import { renderWithProviders } from '../test/utils';
import { authApi } from '../api/auth';
import { ApiError } from '../api/client';

vi.mock('../api/auth', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    me: vi.fn().mockRejectedValue(new Error('brak sesji')),
    changePassword: vi.fn(),
  },
  usersApi: { list: vi.fn(), create: vi.fn(), update: vi.fn() },
}));

describe('Ekran logowania', () => {
  beforeEach(() => {
    vi.mocked(authApi.me).mockRejectedValue(new ApiError('brak sesji', 401));
  });

  it('wysyła login i hasło do API', async () => {
    vi.mocked(authApi.login).mockResolvedValue({
      user: {
        id: 1,
        login: 'admin',
        email: null,
        role: 'admin',
        is_active: true,
        created_at: '2026-01-01T00:00:00Z',
        last_login_at: null,
        must_change_password: false,
      },
      csrf_token: 'token',
      expires_at: '2026-01-02T00:00:00Z',
    });

    renderWithProviders(<LoginPage />);
    await userEvent.type(screen.getByLabelText('Login'), 'admin');
    await userEvent.type(screen.getByLabelText('Hasło'), 'SuperTajne123');
    await userEvent.click(screen.getByRole('button', { name: /zaloguj/i }));

    await waitFor(() => expect(authApi.login).toHaveBeenCalledWith('admin', 'SuperTajne123'));
  });

  it('pokazuje komunikat o błędnym haśle', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new ApiError('Nieprawidłowy login lub hasło.', 401));

    renderWithProviders(<LoginPage />);
    await userEvent.type(screen.getByLabelText('Login'), 'admin');
    await userEvent.type(screen.getByLabelText('Hasło'), 'zle');
    await userEvent.click(screen.getByRole('button', { name: /zaloguj/i }));

    expect(await screen.findByText('Nieprawidłowy login lub hasło.')).toBeInTheDocument();
  });
});
