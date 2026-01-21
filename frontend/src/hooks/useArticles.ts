import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { articlesApi } from '@/api';
import { ArticleFilters, ArticleUpdate, ArticleApproveRequest } from '@/types';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/utils/error';

export function useArticles(filters: ArticleFilters & { page?: number; per_page?: number } = {}) {
  return useQuery({
    queryKey: ['articles', filters],
    queryFn: () => articlesApi.list(filters),
  });
}

export function useArticleQueue(params: { page?: number; per_page?: number; priority?: string; category?: string } = {}) {
  return useQuery({
    queryKey: ['articles', 'queue', params],
    queryFn: () => articlesApi.queue(params),
  });
}

export function useArticle(id: string) {
  return useQuery({
    queryKey: ['articles', id],
    queryFn: () => articlesApi.get(id),
    enabled: !!id,
  });
}

export function useArticleVersions(id: string) {
  return useQuery({
    queryKey: ['articles', id, 'versions'],
    queryFn: () => articlesApi.getVersions(id),
    enabled: !!id,
  });
}

export function useApproveArticle() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data?: ArticleApproveRequest }) => 
      articlesApi.approve(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      toast.success('Статья одобрена');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при одобрении');
      toast.error(message);
    },
  });
}

export function useRejectArticle() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) => 
      articlesApi.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      toast.success('Статья отклонена');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при отклонении');
      toast.error(message);
    },
  });
}

export function useUpdateArticle() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ArticleUpdate }) => 
      articlesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['articles', id] });
      toast.success('Статья обновлена');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при обновлении');
      toast.error(message);
    },
  });
}

export function useAIRewrite() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => articlesApi.aiRewrite(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['articles', id] });
      toast.success('AI рерайт применен');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка AI');
      toast.error(message);
    },
  });
}

export function useRestoreVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ articleId, versionId }: { articleId: string; versionId: string }) =>
      articlesApi.restoreVersion(articleId, versionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      toast.success('Версия восстановлена');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при восстановлении');
      toast.error(message);
    },
  });
}

export function useArticlePreview(id: string, templateId?: string, targetId?: string) {
  return useQuery({
    queryKey: ['articles', id, 'preview', templateId, targetId],
    queryFn: () => articlesApi.preview(id, templateId, targetId),
    enabled: !!id,
  });
}