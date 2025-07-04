import { useState, useCallback, useRef, useEffect } from 'react';

interface LoadingState {
  isLoading: boolean;
  error: string | null;
  startLoading: () => void;
  stopLoading: () => void;
  setError: (error: string | null) => void;
  resetError: () => void;
  executeAsync: <T>(asyncFn: () => Promise<T>) => Promise<T | undefined>;
}

export const useLoadingState = (initialLoading = false): LoadingState => {
  const [isLoading, setIsLoading] = useState(initialLoading);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const startLoading = useCallback(() => {
    if (mountedRef.current) {
      setIsLoading(true);
      setError(null);
    }
  }, []);

  const stopLoading = useCallback(() => {
    if (mountedRef.current) {
      setIsLoading(false);
    }
  }, []);

  const resetError = useCallback(() => {
    if (mountedRef.current) {
      setError(null);
    }
  }, []);

  const executeAsync = useCallback(async <T,>(asyncFn: () => Promise<T>): Promise<T | undefined> => {
    startLoading();
    try {
      const result = await asyncFn();
      if (mountedRef.current) {
        stopLoading();
      }
      return result;
    } catch (err: any) {
      if (mountedRef.current) {
        const errorMessage = err.response?.data?.error || 
                           err.response?.data?.message || 
                           err.message || 
                           'An unexpected error occurred';
        setError(errorMessage);
        stopLoading();
      }
      return undefined;
    }
  }, [startLoading, stopLoading]);

  return {
    isLoading,
    error,
    startLoading,
    stopLoading,
    setError,
    resetError,
    executeAsync,
  };
};

// Hook for delayed loading states (prevents flash of loading for fast operations)
export const useDelayedLoading = (delay = 200) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showLoading, setShowLoading] = useState(false);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (isLoading) {
      timeoutRef.current = setTimeout(() => {
        setShowLoading(true);
      }, delay);
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      setShowLoading(false);
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [isLoading, delay]);

  return {
    isLoading,
    showLoading,
    setIsLoading,
  };
};