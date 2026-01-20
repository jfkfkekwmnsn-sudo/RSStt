import { apiClient } from '../client';
import { AnalyticsSummary, CategoryStats, SourceStats } from '@/types';

export const analyticsApi = {
  summary: (dateFrom?: string, dateTo?: string) =>
    apiClient.get<AnalyticsSummary>('/analytics/summary', {
      params: { date_from: dateFrom, date_to: dateTo },
    }),

  categories: (dateFrom?: string, dateTo?: string) =>
    apiClient.get<CategoryStats[]>('/analytics/categories', {
      params: { date_from: dateFrom, date_to: dateTo },
    }),

  sources: (dateFrom?: string, dateTo?: string, limit?: number) =>
    apiClient.get<SourceStats[]>('/analytics/sources', {
      params: { date_from: dateFrom, date_to: dateTo, limit },
    }),

  aiUsage: () =>
    apiClient.get<{ tokens_today: number; limit: number; remaining: number; usage_percent: number }>(
      '/analytics/ai-usage'
    ),
};