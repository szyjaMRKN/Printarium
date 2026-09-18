import { Navigate, Route, Routes } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Loading } from './components/ui';
import { useAuth } from './hooks/useAuth';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { SalesPage } from './pages/SalesPage';
import { RegistryPage } from './pages/RegistryPage';
import { LimitsPage } from './pages/LimitsPage';
import { CostsPage } from './pages/CostsPage';
import { ProductsPage } from './pages/ProductsPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { ReportsPage } from './pages/ReportsPage';
import { PitPage } from './pages/PitPage';
import { BackupPage } from './pages/BackupPage';
import { SettingsPage } from './pages/SettingsPage';

export default function App() {
  const { session, loading } = useAuth();

  if (loading) {
    return <Loading label="Sprawdzanie sesji…" />;
  }

  if (!session) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<Navigate to="/" replace />} />
      <Route element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="sprzedaz" element={<SalesPage />} />
        <Route path="ewidencja" element={<RegistryPage />} />
        <Route path="limity" element={<LimitsPage />} />
        <Route path="koszty" element={<CostsPage />} />
        <Route path="produkty" element={<ProductsPage />} />
        <Route path="dokumenty" element={<DocumentsPage />} />
        <Route path="raporty" element={<ReportsPage />} />
        <Route path="pit" element={<PitPage />} />
        <Route path="backup" element={<BackupPage />} />
        <Route path="ustawienia" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
