import { useEffect, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useTheme } from '../hooks/useTheme';
import { useMeta } from '../hooks/useMeta';

const NAV_ITEMS = [
  { to: '/', label: 'Pulpit', icon: '▦', end: true },
  { to: '/sprzedaz', label: 'Sprzedaż', icon: '🧾' },
  { to: '/ewidencja', label: 'Ewidencja sprzedaży', icon: '📒' },
  { to: '/limity', label: 'Limity działalności', icon: '📊' },
  { to: '/koszty', label: 'Koszty', icon: '💳' },
  { to: '/produkty', label: 'Produkty', icon: '📦' },
  { to: '/dokumenty', label: 'Dokumenty', icon: '📄' },
  { to: '/raporty', label: 'Raporty', icon: '📈' },
  { to: '/pit', label: 'PIT', icon: '🏛' },
  { to: '/backup', label: 'Backup', icon: '💾' },
  { to: '/ustawienia', label: 'Ustawienia', icon: '⚙️' },
];

export function Layout() {
  const { session, logout } = useAuth();
  const { resolved, toggle } = useTheme();
  const { data: meta } = useMeta();
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMenuOpen(false);
  }, [location.pathname]);

  const currentTitle = NAV_ITEMS.find((item) =>
    item.end ? location.pathname === item.to : location.pathname.startsWith(item.to),
  )?.label;

  return (
    <div className="app-shell">
      {menuOpen ? <div className="backdrop" onClick={() => setMenuOpen(false)} /> : null}
      <aside className={menuOpen ? 'sidebar is-open' : 'sidebar'}>
        <div className="sidebar__brand">
          <img src="/icons/icon.svg" alt="" aria-hidden="true" />
          <span>Ewidencja</span>
        </div>
        <nav className="sidebar__nav" aria-label="Menu główne">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'sidebar__link is-active' : 'sidebar__link')}
            >
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__footer">
          Działalność nierejestrowana
          <br />
          wersja {meta?.app.version ?? '—'}
        </div>
      </aside>

      <div className="main">
        <header className="topbar">
          <button
            type="button"
            className="hamburger"
            onClick={() => setMenuOpen((open) => !open)}
            aria-label="Menu"
            aria-expanded={menuOpen}
          >
            ☰
          </button>
          <h1 className="topbar__title">{currentTitle ?? 'Ewidencja'}</h1>
          <button
            type="button"
            className="btn btn--sm"
            onClick={toggle}
            aria-label={resolved === 'dark' ? 'Włącz jasny motyw' : 'Włącz ciemny motyw'}
          >
            {resolved === 'dark' ? '☀️' : '🌙'}
          </button>
          <span className="topbar__user">{session?.user.login}</span>
          <button type="button" className="btn btn--sm" onClick={() => void logout()}>
            Wyloguj
          </button>
        </header>
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
