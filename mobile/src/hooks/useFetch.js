import { useCallback, useEffect, useState } from 'react';

import { api, apiErrorMessage } from '../api/client';

/** GET `path` with loading/error/refetch. `params` is an axios params object. */
export default function useFetch(path, params, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(
    async (silent = false) => {
      if (!silent) setLoading(true);
      setError('');
      try {
        const res = await api.get(path, { params });
        setData(res.data);
      } catch (e) {
        setError(apiErrorMessage(e));
      } finally {
        setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [path, JSON.stringify(params), ...deps],
  );

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, refetch: load, setData };
}
