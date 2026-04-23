import { useState, useEffect, useCallback } from 'react';

export function useFetch(fetchFn, options = {}) {
  const { immediate = true, deps = [] } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);

    try {
      const result = await fetchFn(...args);
      setData(result);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  const refetch = useCallback(() => execute(), [execute]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute, ...deps]);

  return { data, loading, error, execute, refetch };
}
