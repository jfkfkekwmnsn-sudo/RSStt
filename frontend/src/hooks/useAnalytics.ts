import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '@/api';

export function useAnalyticsSummary(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ['analytics', 'summary', dateFrom, dateTo],
    queryFn: () => analyticsApi.summary(dateFrom, dateTo),
  });
}

export function useCategoryStats(dateFrom?: string, dateTo?: string) {
  return useQuery({
    queryKey: ['analytics', 'categories', dateFrom, dateTo],
    queryFn: () => analyticsApi.categories(dateFrom, dateTo),
  });
}

export function useSourceStats(dateFrom?: string, dateTo?: string, limit?: number) {
  return useQuery({
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