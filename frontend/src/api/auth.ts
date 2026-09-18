import { api } from './client';
import type { SessionInfo, User } from '../types';

export const authApi = {
  login: (login: string, password: string) =>
    api.post<SessionInfo>('/api/auth/login', { login, password }),
  logout: () => api.post<{ message: string }>('/api/auth/logout'),
  me: () => api.get<SessionInfo>('/api/auth/me'),
  changePassword: (current_password: string, new_password: string) =>
    api.post<{ message: string }>('/api/auth/password', { current_password, new_password }),
};

export const usersApi = {
  list: () => api.get<User[]>('/api/users'),
  create: (payload: { login: string; password: string; email?: string | null; role: string }) =>
    api.post<User>('/api/users', payload),
  update: (
    id: number,
    payload: { email?: string | null; role?: string; is_active?: boolean; new_password?: string },
  ) => api.patch<User>(`/api/users/${id}`, payload),
};
