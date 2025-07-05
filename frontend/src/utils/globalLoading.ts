import { useState, useEffect } from 'react';

// Global loading state management
let globalSetLoading: ((loading: boolean, message?: string) => void) | null = null;

export const useGlobalLoading = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('Loading...');

  useEffect(() => {
    globalSetLoading = (loading: boolean, msg?: string) => {
      setIsLoading(loading);
      if (msg) setMessage(msg);
    };

    return () => {
      globalSetLoading = null;
    };
  }, []);

  return { isLoading, message };
};

// Utility functions to control global loading
export const showGlobalLoading = (message?: string) => {
  if (globalSetLoading) {
    globalSetLoading(true, message);
  }
};

export const hideGlobalLoading = () => {
  if (globalSetLoading) {
    globalSetLoading(false);
  }
};