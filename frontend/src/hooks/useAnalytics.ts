import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/api';
import { AnalyticsSummary, CategoryStats, SourceStats } from '@/types';

export function useAnalyticsSummary(dateFrom?: string, dateTo?: string) {
  return useQuery<AnalyticsSummary, Error>({
    queryKey: ['analytics', 'summary', dateFrom, dateTo],
    queryFn: () => analyticsApi.summary(dateFrom, dateTo),
    retry: 1,
    staleTime: 60000, // 1 minute
  });
}

export function useCategoryStats(dateFrom?: string, dateTo?: string) {
  return useQuery<CategoryStats[], Error>({
    queryKey: ['analytics', 'categories', dateFrom, dateTo],
    queryFn: () => analyticsApi.categories(dateFrom, dateTo),
  });
}

export function useSourceStats(dateFrom?: string, dateTo?: string, limit?: number) {
  return useQuery<SourceStats[], Error>({
    queryKey: ['analytics', 'sources', dateFrom, dateTo, limit],
    queryFn: () => analyticsApi.sources(dateFrom, dateTo, limit),
  });
}

export function useAIUsage() {
  return useQuery({
    queryKey: ['analytics', 'ai-usage'],
    queryFn: () => analyticsApi.aiUsage(),
  });
}