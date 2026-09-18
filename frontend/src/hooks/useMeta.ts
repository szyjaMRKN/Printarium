import { useQuery } from '@tanstack/react-query';
import { metaApi } from '../api/resources';
import type { MetaOptions } from '../types';

/** Słowniki (statusy, metody płatności, kanały) pobierane raz na sesję. */
export function useMeta() {
  return useQuery<MetaOptions>({
    queryKey: ['meta'],
    queryFn: metaApi.options,
    staleTime: 60 * 60 * 1000,
  });
}
