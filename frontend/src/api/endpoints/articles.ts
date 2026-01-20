import { apiClient } from '../client';
import {
  PaginatedResponse,
  MessageResponse,
  Article,
  ArticleListItem,
  ArticleDetail,
  ArticleVersion,
  ArticleFilters,
  ArticleUpdate,
  ArticleApproveRequest,
  ArticlePreview,
} from '@/types';

export const articlesApi = {
  list: (params: ArticleFilters & { page?: number; per_page?: number }) =>
    apiClient.get<PaginatedResponse<ArticleListItem>>('/articles', { params }),

  queue: (params: { page?: number; per_page?: number; priority?: string; category?: string }) =>
    apiClient.get<PaginatedResponse<ArticleListItem>>('/articles/queue', { params }),

  get: (id: string) =>
    apiClient.get<ArticleDetail>(`/articles/${id}`),

  update: (id: string, data: ArticleUpdate) =>
    apiClient.patch<Article>(`/articles/${id}`, data),

  approve: (id: string, data?: ArticleApproveRequest) =>
    apiClient.post<MessageResponse>(`/articles/${id}/approve`, data),

  reject: (id: string, reason?: string) =>
    apiClient.post<MessageResponse>(`/articles/${id}/reject`, { reason }),

  schedule: (id: string, scheduledAt: string, targetId?: string) =>
    apiClient.post<MessageResponse>(`/articles/${id}/schedule`, {
      scheduled_at: scheduledAt,
      target_id: targetId,
    }),

  publish: (id: string, targetId?: string) =>
    apiClient.post<MessageResponse>(`/articles/${id}/publish`, null, {
      params: { target_id: targetId },
    }),

  retry: (id: string) =>
    apiClient.post<MessageResponse>(`/articles/${id}/retry`),

  getVersions: (id: string) =>
    apiClient.get<ArticleVersion[]>(`/articles/${id}/versions`),

  restoreVersion: (articleId: string, versionId: string) =>
    apiClient.post<Article>(`/articles/${articleId}/versions/${versionId}/restore`),

  preview: (id: string, templateId?: string, targetId?: string) =>
    apiClient.post<ArticlePreview>(`/articles/${id}/preview`, {
      template_id: templateId,
      target_id: targetId,
    }),

  aiRewrite: (id: string) =>
    apiClient.post<Article>(`/articles/${id}/ai/rewrite`),

  bulkApprove: (articleIds: string[], targetId?: string) =>
    apiClient.post('/articles/bulk/approve', { article_ids: articleIds }, {
      params: { target_id: targetId },
    }),

  bulkReject: (articleIds: string[], reason?: string) =>
    apiClient.post('/articles/bulk/reject', { article_ids: articleIds }, {
      params: { reason },
    }),
};