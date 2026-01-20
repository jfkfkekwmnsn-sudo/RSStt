import React, { useState } from 'react';
import { Plus, Edit, Trash2, Play, Zap } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, Button, Modal, Input, Select, Badge, Spinner } from '@/components/ui';
import { ConfirmDialog } from '@/components/common';
import { apiClient } from '@/api';
import { Rule } from '@/types';
import toast from 'react-hot-toast';

export const Rules: React.FC = () => {
  const [showModal, setShowModal] = useState(false);
  const [editingRule, setEditingRule] = useState<Rule | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: rules, isLoading } = useQuery({
    queryKey: ['rules'],
    queryFn: () => apiClient.get<Rule[]>('/rules'),
  });

  const deleteRule = useMutation({
    mutationFn: (id: string) => apiClient.delete(`/rules/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['rules'] });
      toast.success('Правило удалено');
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
          <h1 className="text-2xl font-bold text-gray-900">Правила</h1>
          <p className="text-gray-500 mt-1">
            Автоматизация обработки материалов
          </p>
        </div>
        <Button onClick={() => setShowModal(true)} icon={<Plus className="w-4 h-4" />}>
          Добавить правило
        </Button>
      </div>

      <div className="space-y-4">
        {rules?.map((rule) => (
          <Card key={rule.id}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className={`w-5 h-5 ${rule.is_active ? 'text-yellow-500' : 'text-gray-400'}`} />
                  <h3 className="font-semibold text-gray-900">{rule.name}</h3>
                  <Badge variant={rule.is_active ? 'success' : 'default'}>
                    {rule.is_active ? 'Активно' : 'Неактивно'}
                  </Badge>
                  <span className="text-sm text-gray-500">Приоритет: {rule.priority}</span>
                </div>
                
                {rule.description && (
                  <p className="text-gray-600 text-sm mb-3">{rule.description}</p>
                )}
                
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <span>Условий: {rule.conditions?.conditions?.length || 0}</span>
                  <span>Действий: {rule.actions?.actions?.length || 0}</span>
                  <span>Срабатываний: {rule.times_matched}</span>
                </div>
              </div>
              
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  icon={<Play className="w-4 h-4" />}
                  title="Тестировать"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setEditingRule(rule);
                    setShowModal(true);
                  }}
                  icon={<Edit className="w-4 h-4" />}
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setDeleteId(rule.id)}
                  icon={<Trash2 className="w-4 h-4 text-red-500" />}
                />
              </div>
            </div>
          </Card>
        ))}

        {(!rules || rules.length === 0) && (
          <Card>
            <div className="text-center py-8">
              <Zap className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-500">Нет правил</p>
              <Button 
                className="mt-4" 
                onClick={() => setShowModal(true)}
              >
                Создать первое правило
              </Button>
            </div>
          </Card>
        )}
      </div>

      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={() => deleteId && deleteRule.mutate(deleteId)}
        title="Удалить правило?"
        message="Правило будет удалено безвозвратно."
        confirmText="Удалить"
        variant="danger"
        loading={deleteRule.isPending}
      />
    </div>
  );
};