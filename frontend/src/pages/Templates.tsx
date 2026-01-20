import React, { useState } from 'react';
import { Plus, Edit, Trash2, FileText, Eye } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Modal, Input, Badge, Spinner } from '@/components/ui';
import { ConfirmDialog } from '@/components/common';
import { apiClient } from '@/api';
import { Template } from '@/types';
import toast from 'react-hot-toast';

export const Templates: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [previewTemplate, setPreviewTemplate] = useState<Template | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: templates, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => apiClient.get<Template[]>('/templates'),
  });

  const deleteTemplate = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/templates/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['templates'] });
      toast.success('Шаблон удален');
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
          <h1 className="text-2xl font-bold text-gray-900">Шаблоны</h1>
          <p className="text-gray-500 mt-1">
            Форматирование публикаций
          </p>
        </div>
        <Button onClick={() => setShowModal(true)} icon={<Plus className="w-4 h-4" />}>
          Добавить шаблон
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {templates?.map((template) => (
          <Card key={template.id}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary-600" />
                <h3 className="font-semibold text-gray-900">{template.name}</h3>
              </div>
              <div className="flex items-center gap-1">
                {template.is_default && (
                  <Badge variant="info" size="sm">По умолчанию</Badge>
                )}
                <Badge variant={template.is_active ? 'success' : 'default'} size="sm">
                  {template.is_active ? 'Активен' : 'Неактивен'}
                </Badge>
              </div>
            </div>
            
            <div className="text-sm text-gray-500 mb-3">
              <span>Область: {template.scope}</span>
              {template.scope_value && <span> ({template.scope_value})</span>}
            </div>
            
            <div className="bg-gray-50 rounded p-2 text-xs font-mono text-gray-600 mb-3 line-clamp-3">
              {template.body}
            </div>
            
            <div className="flex items-center justify-end gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPreviewTemplate(template)}
                icon={<Eye className="w-4 h-4" />}
              />
              <Button
                variant="ghost"
                size="sm"
                icon={<Edit className="w-4 h-4" />}
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setDeleteId(template.id)}
                icon={<Trash2 className="w-4 h-4 text-red-500" />}
              />
            </div>
          </Card>
        ))}
      </div>

      {/* Preview Modal */}
      <Modal
        isOpen={!!previewTemplate}
        onClose={() => setPreviewTemplate(null)}
        title="Предпросмотр шаблона"
        size="lg"
      >
        {previewTemplate && (
          <div className="bg-gray-900 rounded-lg p-4 text-white">
            <pre className="whitespace-pre-wrap text-sm">{previewTemplate.body}</pre>
          </div>
        )}
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteTemplate.mutate(deleteId)}
        title="Удалить шаблон?"
        message="Шаблон будет удален безвозвратно."
        confirmText="Удалить"
        variant="danger"
        loading={deleteTemplate.isPending}
      />
    </div>
  );
};