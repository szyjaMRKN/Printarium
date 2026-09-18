/**
 * Klient HTTP.
 * Sesja trzymana jest w ciasteczku HttpOnly — w localStorage nie ma żadnych tokenów.
 * Token CSRF czytamy z ciasteczka i wysyłamy nagłówkiem przy każdej modyfikacji.
 */

export const CSRF_COOKIE = 'ewid_csrf';
export const CSRF_HEADER = 'X-CSRF-Token';
export const UNAUTHORIZED_EVENT = 'ewidencja:unauthorized';

export class ApiError extends Error {
  status: number;
  code: string;
  fieldErrors: Array<{ field: string; message: string }>;

  constructor(
    message: string,
    status: number,
    code = 'blad',
    fieldErrors: Array<{ field: string; message: string }> = [],
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }
}

export function readCookie(name: string): string {
  const match = document.cookie.split('; ').find((row) => row.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : '';
}

/**
 * Przedrostek adresów — aplikacja może być zainstalowana w podkatalogu domeny
 * (np. mojadomena.pl/ewidencja). Vite podstawia tu wartość `base` z builda.
 */
export const BASE_PATH = (import.meta.env.BASE_URL || '/').replace(/\/+$/, '');

function buildUrl(path: string, params?: Record<string, unknown>): string {
  const url = BASE_PATH + (path.startsWith('/') ? path : `/${path}`);
  if (!params) return url;
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    search.append(key, String(value));
  });
  const query = search.toString();
  return query ? `${url}?${query}` : url;
}

async function toError(response: Response): Promise<ApiError> {
  let detail = `Błąd ${response.status}`;
  let code = 'blad';
  let fieldErrors: Array<{ field: string; message: string }> = [];
  try {
    const body = await response.json();
    detail = body.detail ?? detail;
    code = body.code ?? code;
    fieldErrors = body.errors ?? [];
  } catch {
    /* odpowiedź bez JSON-a — zostaje komunikat domyślny */
  }
  return new ApiError(detail, response.status, code, fieldErrors);
}

async function request<T>(
  method: string,
  path: string,
  options: { body?: unknown; params?: Record<string, unknown>; formData?: FormData } = {},
): Promise<T> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (options.body !== undefined) headers['Content-Type'] = 'application/json';
  if (method !== 'GET' && method !== 'HEAD') headers[CSRF_HEADER] = readCookie(CSRF_COOKIE);

  const response = await fetch(buildUrl(path, options.params), {
    method,
    headers,
    credentials: 'include',
    body: options.formData ?? (options.body !== undefined ? JSON.stringify(options.body) : undefined),
  });

  if (response.status === 401 && !path.includes('/auth/login')) {
    window.dispatchEvent(new CustomEvent(UNAUTHORIZED_EVENT));
  }
  if (!response.ok) throw await toError(response);
  if (response.status === 204) return undefined as T;

  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) return (await response.text()) as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, params?: Record<string, unknown>) => request<T>('GET', path, { params }),
  post: <T>(path: string, body?: unknown, params?: Record<string, unknown>) =>
    request<T>('POST', path, { body: body ?? {}, params }),
  put: <T>(path: string, body: unknown) => request<T>('PUT', path, { body }),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, { body }),
  delete: <T>(path: string, params?: Record<string, unknown>) => request<T>('DELETE', path, { params }),
  upload: <T>(path: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<T>('POST', path, { formData });
  },
};

/** Pobiera plik z API (eksport, PDF, kopia zapasowa) i zapisuje go na dysku. */
export async function downloadFile(
  path: string,
  params?: Record<string, unknown>,
  fallbackName = 'plik',
): Promise<void> {
  const response = await fetch(buildUrl(path, params), { credentials: 'include' });
  if (!response.ok) throw await toError(response);

  const disposition = response.headers.get('content-disposition') ?? '';
  const match = /filename="?([^";]+)"?/.exec(disposition);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = match?.[1] ?? fallbackName;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

/** Otwiera plik w nowej karcie (podgląd PDF). */
export async function openFile(path: string): Promise<void> {
  const response = await fetch(buildUrl(path), { credentials: 'include' });
  if (!response.ok) throw await toError(response);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, '_blank', 'noopener');
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
