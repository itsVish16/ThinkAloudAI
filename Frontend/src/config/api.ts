// Centralized API configuration with production fallback
export const getApiBaseUrl = (): string => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined' && window.location.hostname.includes('thinkaloudai.tech')) {
    return 'https://api.thinkaloudai.tech';
  }
  return '';
};

export const API_BASE_URL = getApiBaseUrl();
