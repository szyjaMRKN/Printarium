import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { backupsApi } from '../api/resources';
import { downloadFile } from '../api/client';
import { Alert, EmptyState, Field, Loading, Modal } from '../components/ui';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { formatBytes, formatDateTime } from '../utils/format';

const CONFIRMATION = 'PRZYWRACAM';

export function BackupPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const { refresh } = useAuth();
  const [restoring, setRestoring] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState('');
  const [acknowledged, setAcknowledged] = useState(false);

  const backups = useQuery({ queryKey: ['backups'], queryFn: backupsApi.list });

  const createMutation = useMutation({
    mutationFn: () => backupsApi.create('ręczna'),
    onSuccess: (backup) => {
      toast.success(`Utworzono kopię ${backup.filename}.`);
      void queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
    onError: (error) => toast.error(error),
  });

  const deleteMutation = useMutation({
    mutationFn: (filename: string) => backupsApi.remove(filename),
    onSuccess: () => {
      toast.success('Kopia została usunięta.');
      void queryClient.invalidateQueries({ queryKey: ['backups'] });
    },
    onError: (error) => toast.error(error),
  });

  const restoreMutation = useMutation({
    mutationFn: (filename: string) => backupsApi.restore(filename, CONFIRMATION),
    onSuccess: (result) => {
      toast.success(`${result.message} Kopia bezpieczeństwa: ${result.safety_backup}.`);
      setRestoring(null);
      setConfirmation('');
      setAcknowledged(false);
      queryClient.clear();
      void refresh();
    },
    onError: (error) => toast.error(error),
  });

  return (
    <>
      <div className="page__header">
        <div>
          <h1>Backup</h1>
          <p>
            Kopie wykonywane są mechanizmem SQLite Backup API — bezpiecznie, także gdy ktoś właśnie zapisuje dane.
          </p>
        </div>
        <div className="btn-row">
          <button
            type="button"
            className="btn"
            onClick={() => void downloadFile('/api/backups/export-json', undefined, 'eksport-danych.json').catch((e) => toast.error(e))}
          >
            Eksport danych (JSON)
          </button>
          <button type="button" className="btn btn--primary" onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
            {createMutation.isPending ? 'Tworzenie…' : 'Utwórz kopię zapasową'}
          </button>
        </div>
      </div>

      <Alert variant="warning" title="Przywracanie nadpisuje bieżące dane">
        Przed przywróceniem aplikacja sprawdza integralność pliku i automatycznie wykonuje kopię aktualnej bazy.
        Po przywróceniu trzeba zalogować się ponownie.
      </Alert>

      <section className="card card--flush">
        {backups.isLoading ? (
          <Loading />
        ) : backups.data && backups.data.length === 0 ? (
          <EmptyState label="Brak kopii zapasowych. Utwórz pierwszą kopię." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Plik</th>
                  <th>Utworzono</th>
                  <th className="num">Rozmiar</th>
                  <th>Rodzaj</th>
                  <th aria-label="Akcje" />
                </tr>
              </thead>
              <tbody>
                {backups.data?.map((backup) => (
                  <tr key={backup.filename}>
                    <td data-label="Plik" className="small">{backup.filename}</td>
                    <td data-label="Utworzono">{formatDateTime(backup.created_at)}</td>
                    <td data-label="Rozmiar" className="num">{formatBytes(backup.size_bytes)}</td>
                    <td data-label="Rodzaj">{backup.is_automatic ? 'automatyczna' : 'ręczna'}</td>
                    <td data-label="">
                      <div className="btn-row">
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() =>
                            void downloadFile(`/api/backups/${backup.filename}/download`, undefined, backup.filename).catch((e) =>
                              toast.error(e),
                            )
                          }
                        >
                          Pobierz
                        </button>
                        <button type="button" className="btn btn--sm" onClick={() => setRestoring(backup.filename)}>
                          Przywróć
                        </button>
                        <button
                          type="button"
                          className="btn btn--sm"
                          onClick={() => {
                            if (window.confirm(`Usunąć kopię ${backup.filename}?`)) deleteMutation.mutate(backup.filename);
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
      </section>

      {restoring ? (
        <Modal title="Przywracanie kopii zapasowej" onClose={() => setRestoring(null)}>
          <div className="stack">
            <Alert variant="danger" title="Operacja nieodwracalna">
              Baza zostanie zastąpiona zawartością pliku <strong>{restoring}</strong>. Aktualne dane zostaną wcześniej
              zapisane w kopii bezpieczeństwa.
            </Alert>
            <label className="checkbox">
              <input type="checkbox" checked={acknowledged} onChange={(event) => setAcknowledged(event.target.checked)} />
              Rozumiem, że bieżące dane zostaną nadpisane.
            </label>
            <Field label={`Wpisz ${CONFIRMATION}, aby potwierdzić`} htmlFor="confirm_restore">
              <input id="confirm_restore" value={confirmation} onChange={(event) => setConfirmation(event.target.value)} />
            </Field>
            <div className="form-actions">
              <button type="button" className="btn" onClick={() => setRestoring(null)}>
                Anuluj
              </button>
              <button
                type="button"
                className="btn btn--danger"
                disabled={!acknowledged || confirmation.trim().toUpperCase() !== CONFIRMATION || restoreMutation.isPending}
                onClick={() => restoreMutation.mutate(restoring)}
              >
                {restoreMutation.isPending ? 'Przywracanie…' : 'Przywróć bazę'}
              </button>
            </div>
          </div>
        </Modal>
      ) : null}
    </>
  );
}
