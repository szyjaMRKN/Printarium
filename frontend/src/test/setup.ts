import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

// jsdom nie implementuje matchMedia ani ResizeObserver (wymagane przez motyw i wykresy).
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addEventListener: () => {},
    removeEventListener: () => {},
    addListener: () => {},
    removeListener: () => {},
    dispatchEvent: () => false,
  }),
});

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = globalThis.ResizeObserver ?? (ResizeObserverStub as never);

// Testy nigdy nie odpytują prawdziwego API — domyślnie zwracamy 401,
// a konkretne przypadki podmieniają moduły z katalogu src/api.
globalThis.fetch = vi.fn(
  async () =>
    new Response(JSON.stringify({ detail: 'Brak sesji', code: 'brak_autoryzacji' }), {
      status: 401,
      headers: { 'content-type': 'application/json' },
    }),
) as unknown as typeof fetch;
