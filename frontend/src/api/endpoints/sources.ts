import { apiClient } from '../client';
import {
  PaginatedResponse,
  MessageResponse,
  Source,
  SourceListItem,
  SourceRun,
  SourceCreate,
  SourceUpdate,
} from '@/types';

export const sourcesApi = {
  list: (params?: { page?: number; per_page?: number; is_active?: boolean; type?: string; search?: string }) =>
    apiClient.get<PaginatedResponse<SourceListItem>>('/sources', { params }),

  get: (id: string) =>
    apiClient.get<Source>(`/sources/${id}`),

  create: (data: SourceCreate) =>
    apiClient.post<Source>('/sources', data),

  update: (id: string, data: SourceUpdate) =>
    apiClient.patch<Source>(`/sources/${id}`, data),

  delete: (id: string) =>
    apiClient.delete<MessageResponse>(`/sources/${id}`),

  fetchNow: (id: string) =>
    apiClient.post<{ success: boolean; message: string; run_id?: string }>(`/sources/${id}/fetch-now`),

  getRuns: (id: string, limit?: number) =>
    apiClient.get<SourceRun[]>(`/sources/${id}/runs`, { params: { limit } }),
};