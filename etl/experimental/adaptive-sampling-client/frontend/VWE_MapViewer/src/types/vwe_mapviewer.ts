export interface VWE_MapViewerData {
  id: string;
  name: string;
  description?: string;
  status: VWE_MapViewerStatus;
  metadata?: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export enum VWE_MapViewerStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export interface VWE_MapViewerRequest {
  name: string;
  description?: string;
  metadata?: Record<string, any>;
}

export interface VWE_MapViewerResponse {
  data: VWE_MapViewerData;
  message: string;
  success: boolean;
}

export interface VWE_MapViewerListResponse {
  data: VWE_MapViewerData[];
  total: number;
  page: number;
  limit: number;
}

export interface ApiError {
  error: string;
  message: string;
  code?: string;
  details?: Record<string, any>;
}

export interface HealthCheck {
  status: 'healthy' | 'unhealthy';
  service: string;
  timestamp: string;
  version?: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

export interface SearchParams {
  query?: string;
  filters?: Record<string, any>;
  pagination?: PaginationParams;
}
