import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sourcesApi } from '@/api';
import { SourceCreate, SourceUpdate } from '@/types';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/utils/error';

export function useSources(params?: { page?: number; per_page?: number; is_active?: boolean }) {
  return useQuery({
    queryKey: ['sources', params],
    queryFn: () => sourcesApi.list(params),
  });
}

export function useSource(id: string) {
  return useQuery({
    queryKey: ['sources', id],
    queryFn: () => sourcesApi.get(id),
    enabled: !!id,
  });
}

export function useSourceRuns(id: string, limit = 20) {
  return useQuery({
    queryKey: ['sources', id, 'runs', limit],
    queryFn: () => sourcesApi.getRuns(id, limit),
    enabled: !!id,
  });
}

export function useCreateSource() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: SourceCreate) => sourcesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      toast.success('Источник создан');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при создании');
      toast.error(message);
    },
  });
}

export function useUpdateSource() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SourceUpdate }) => 
      sourcesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      queryClient.invalidateQueries({ queryKey: ['sources', id] });
      toast.success('Источник обновлен');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при обновлении');
      toast.error(message);
    },
  });
}

export function useDeleteSource() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => sourcesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sources'] });
      toast.success('Источник удален');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при удалении');
      toast.error(message);
    },
  });
}

export function useFetchSource() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: string) => sourcesApi.fetchNow(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['sources', id] });
      toast.success('Запущен сбор материалов');
    },
    onError: (error) => {
      const message = getErrorMessage(error, 'Ошибка при запуске');
      toast.error(message);
    },
  });
}