import React, { useState } from 'react';
import { Plus, Edit, Trash2, Send, MessageCircle } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Modal, Input, Badge, Spinner } from '@/components/ui';
import { ConfirmDialog } from '@/components/common';
import { apiClient } from '@/api';
import { PublishTarget } from '@/types';
import { formatRelativeTime } from '@/utils';
import toast from 'react-hot-toast';

export const Targets: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: targets, isLoading } = useQuery({
    queryKey: ['targets'],
    queryFn: () => apiClient.get<PublishTarget[]>('/targets'),
  });

  const deleteTarget = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/targets/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['targets'] });
      toast.success('Канал удален');
      setDeleteId(null);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Каналы публикации</h1>
          <p className="text-gray-500 mt-1">
            Telegram каналы для публикации материалов
          </p>
        </div>
        <Button onClick={() => setShowModal(true)} icon={<Plus className="w-4 h-4" />}>
          Добавить канал
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {targets?.map((target) => (
          <Card key={target.id}>
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <MessageCircle className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{target.name}</h3>
                  <p className="text-sm text-gray-500">
                    {target.telegram_chat_username 
                      ? `@${target.telegram_chat_username}` 
                      : `ID: ${target.telegram_chat_id}`}
                  </p>
                </div>
              </div>
              <Badge variant={target.is_active ? 'success' : 'default'}>
                {target.is_active ? 'Активен' : 'Неактивен'}
              </Badge>
            </div>
            
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between text-sm">
                <div className="text-gray-500">
                  <span>Опубликовано: {target.total_published}</span>
                  {target.last_published_at && (
                    <span className="ml-3">
                      Последняя: {formatRelativeTime(target.last_published_at)}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Edit className="w-4 h-4" />}
                  />
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setDeleteId(target.id)}
                    icon={<Trash2 className="w-4 h-4 text-red-500" />}
                  />
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {(!targets || targets.length === 0) && (
        <Card>
          <div className="text-center py-8">
            <Send className="w-12 h-12 mx-auto text-gray-400 mb-4" />
            <p className="text-gray-500">Нет каналов публикации</p>
            <Button className="mt-4" onClick={() => setShowModal(true)}>
              Добавить канал
            </Button>
          </div>
        </Card>
      )}

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteTarget.mutate(deleteId)}
        title="Удалить канал?"
        message="Канал будет удален. История публикаций сохранится."
        confirmText="Удалить"
        variant="danger"
        loading={deleteTarget.isPending}
      />
    </div>
  );
};