import axios, { AxiosResponse } from 'axios';
import { VWE_MapViewerData, VWE_MapViewerRequest, VWE_MapViewerResponse, ApiError } from '@/types/vwe_mapviewer';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export class VWE_MapViewerApi {
  static async getHealth(): Promise<VWE_MapViewerData> {
    try {
      const response = await apiClient.get('/api/health');
      return response.data;
    } catch (error) {
      throw new Error('Failed to fetch health status');
    }
  }

  static async create(request: VWE_MapViewerRequest): Promise<VWE_MapViewerData> {
    try {
      const response = await apiClient.post<VWE_MapViewerResponse>('/api/vwe_mapviewer/', request);
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to create vwe_mapviewer');
      }
      throw new Error('Failed to create vwe_mapviewer');
    }
  }

  static async getById(id: string): Promise<VWE_MapViewerData> {
    try {
      const response = await apiClient.get<VWE_MapViewerResponse>(`/api/vwe_mapviewer/${id}`);
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to fetch vwe_mapviewer');
      }
      throw new Error('Failed to fetch vwe_mapviewer');
    }
  }

  static async update(id: string, request: Partial<VWE_MapViewerRequest>): Promise<VWE_MapViewerData> {
    try {
      const response = await apiClient.put<VWE_MapViewerResponse>(`/api/vwe_mapviewer/${id}`, request);
      return response.data.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to update vwe_mapviewer');
      }
      throw new Error('Failed to update vwe_mapviewer');
    }
  }

  static async delete(id: string): Promise<void> {
    try {
      await apiClient.delete(`/api/vwe_mapviewer/${id}`);
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to delete vwe_mapviewer');
      }
      throw new Error('Failed to delete vwe_mapviewer');
    }
  }

  static async list(params?: { page?: number; limit?: number }): Promise<VWE_MapViewerData[]> {
    try {
      const response = await apiClient.get<VWE_MapViewerData[]>('/api/vwe_mapviewer/', {
        params,
      });
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error) && error.response) {
        const apiError: ApiError = error.response.data;
        throw new Error(apiError.message || 'Failed to list vwe_mapviewers');
      }
      throw new Error('Failed to list vwe_mapviewers');
    }
  }
}

// Utility functions
export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatStatus(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}
