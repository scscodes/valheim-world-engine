import { useState, useEffect, useCallback } from 'react';
import { VWE_MapViewerData, VWE_MapViewerRequest, ApiError } from '@/types/vwe_mapviewer';
import { vwe_mapviewerApi } from '@/utils/vwe_mapviewer';

interface UseVWE_MapViewerReturn {
  data: VWE_MapViewerData | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  create: (request: VWE_MapViewerRequest) => Promise<VWE_MapViewerData | null>;
  update: (id: string, request: Partial<VWE_MapViewerRequest>) => Promise<VWE_MapViewerData | null>;
  remove: (id: string) => Promise<boolean>;
}

export function useVWE_MapViewer(initialData?: VWE_MapViewerData): UseVWE_MapViewerReturn {
  const [data, setData] = useState<VWE_MapViewerData | null>(initialData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await vwe_mapviewerApi.getHealth();
      setData(result as any); // Type assertion for demo
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unknown error occurred';
      setError(errorMessage);
      console.error('Error fetching vwe_mapviewer data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const create = useCallback(async (request: VWE_MapViewerRequest): Promise<VWE_MapViewerData | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await vwe_mapviewerApi.create(request);
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create vwe_mapviewer';
      setError(errorMessage);
      console.error('Error creating vwe_mapviewer:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const update = useCallback(async (id: string, request: Partial<VWE_MapViewerRequest>): Promise<VWE_MapViewerData | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await vwe_mapviewerApi.update(id, request);
      setData(result);
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update vwe_mapviewer';
      setError(errorMessage);
      console.error('Error updating vwe_mapviewer:', err);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const remove = useCallback(async (id: string): Promise<boolean> => {
    setLoading(true);
    setError(null);
    
    try {
      await vwe_mapviewerApi.delete(id);
      setData(null);
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete vwe_mapviewer';
      setError(errorMessage);
      console.error('Error deleting vwe_mapviewer:', err);
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  const refetch = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  useEffect(() => {
    if (!initialData) {
      fetchData();
    }
  }, [fetchData, initialData]);

  return {
    data,
    loading,
    error,
    refetch,
    create,
    update,
    remove,
  };
}
