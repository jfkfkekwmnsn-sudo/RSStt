import React, { useState } from 'react';
import { Plus, RefreshCw, Trash2, Edit, Play, AlertCircle } from 'lucide-react';
import { Card, Button, Modal, Input, Select, Table, Badge, Spinner } from '@/components/ui';
import { ConfirmDialog } from '@/components/common';
import { useSources, useCreateSource, useUpdateSource, useDeleteSource, useFetchSource } from '@/hooks';
import { Source, SourceCreate, SourceUpdate, SourceListItem } from '@/types';
import { formatRelativeTime } from '@/utils';
import { useForm } from 'react-hook-form';

export const Sources: React.FC = () => {
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [editingSource, setEditingSource] = useState<SourceListItem | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const { data, isLoading, refetch } = useSources({ page, per_page: 20 });
  const createSource = useCreateSource();
  const updateSource = useUpdateSource();
  const deleteSource = useDeleteSource();
  const fetchSource = useFetchSource();

  const { register, handleSubmit, reset, formState: { errors } } = useForm<SourceCreate>();

  const handleOpenModal = (source?: SourceListItem) => {
    if (source) {
      setEditingSource(source);
      reset({
        name: source.name,
        feed_url: '', // Need to fetch full source
        type: source.type,
        is_active: source.is_active,
        is_trusted: source.is_trusted,
      });
    } else {
      setEditingSource(null);
      reset({
        name: '',
        feed_url: '',
        type: 'rss',
        is_active: true,
        is_trusted: false,
        fetch_interval_minutes: 15,
      });
    }
    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingSource(null);
    reset();
  };

  const onSubmit = async (data: SourceCreate) => {
    if (editingSource) {
      await updateSource.mutateAsync({ 
        id: editingSource.id, 
        data: data as SourceUpdate 
      });
    } else {
      await createSource.mutateAsync(data);
    }
    handleCloseModal();
  };

  const handleDelete = async () => {
    if (deleteId) {
      await deleteSource.mutateAsync(deleteId);
      setDeleteId(null);
    }
  };

  const handleFetch = async (id: string) => {
    await fetchSource.mutateAsync(id);
  };

  const columns = [
    {
      key: 'name',
      title: 'Название',
      render: (value: string, record: SourceListItem) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{value}</span>
          {record.is_trusted && (
            <Badge variant="success" size="sm">Доверенный</Badge>
          )}
        </div>
      ),
    },
    {
      key: 'type',
      title: 'Тип',
      render: (value: string) => (
        <Badge variant="default">{value.toUpperCase()}</Badge>
      ),
    },
    {
      key: 'is_active',
      title: 'Статус',
      render: (value: boolean, record: SourceListItem) => (
        <div className="flex items-center gap-2">
          {value ? (
            <Badge variant="success">Активен</Badge>
          ) : (
            <Badge variant="default">Неактивен</Badge>
          )}
          {record.consecutive_errors > 0 && (
            <span className="text-red-500 flex items-center gap-1" title={`${record.consecutive_errors} ошибок подряд`}>
              <AlertCircle className="w-4 h-4" />
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'total_articles',
      title: 'Материалов',
      render: (value: number) => value.toLocaleString(),
    },
    {
      key: 'reputation_score',
      title: 'Репутация',
      render: (value: number) => `${Math.round(value * 100)}%`,
    },
    {
      key: 'last_fetch_at',
      title: 'Последний сбор',
      render: (value: string | null) => value ? formatRelativeTime(value) : 'Никогда',
    },
    {
      key: 'actions',
      title: '',
      render: (_: any, record: SourceListItem) => (
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleFetch(record.id)}
            icon={<Play className="w-4 h-4" />}
            title="Запустить сбор"
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => handleOpenModal(record)}
            icon={<Edit className="w-4 h-4" />}
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setDeleteId(record.id)}
            icon={<Trash2 className="w-4 h-4 text-red-500" />}
          />
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Источники</h1>
          <p className="text-gray-500 mt-1">
            {data?.total || 0} источников
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            icon={<RefreshCw className="w-4 h-4" />}
          >
            Обновить
          </Button>
          <Button
            onClick={() => handleOpenModal()}
            icon={<Plus className="w-4 h-4" />}
          >
            Добавить
          </Button>
        </div>
      </div>

      <Card padding="none">
        <Table
          columns={columns}
          data={data?.items || []}
          rowKey="id"
          loading={isLoading}
          emptyText="Нет источников"
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        isOpen={showModal}
        onClose={handleCloseModal}
        title={editingSource ? 'Редактировать источник' : 'Новый источник'}
      >
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Название"
            {...register('name', { required: 'Обязательное поле' })}
            error={errors.name?.message}
          />
          
          <Input
            label="URL фида"
            {...register('feed_url', { required: 'Обязательное поле' })}
            error={errors.feed_url?.message}
            placeholder="https://example.com/rss"
          />

          <Select
            label="Тип"
            {...register('type')}
            options={[
              { value: 'rss', label: 'RSS' },
              { value: 'scraper', label: 'Scraper' },
              { value: 'custom', label: 'Custom' },
            ]}
          />

          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Интервал (мин)"
              type="number"
              {...register('fetch_interval_minutes', { valueAsNumber: true })}
            />
            <Input
              label="Макс. материалов"
              type="number"
              {...register('max_items_per_fetch', { valueAsNumber: true })}
            />
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2">
              <input type="checkbox" {...register('is_active')} className="rounded" />
              <span className="text-sm">Активен</span>
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" {...register('is_trusted')} className="rounded" />
              <span className="text-sm">Доверенный</span>
            </label>
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button variant="outline" onClick={handleCloseModal}>
              Отмена
            </Button>
            <Button 
              type="submit" 
              loading={createSource.isPending || updateSource.isPending}
            >
              {editingSource ? 'Сохранить' : 'Создать'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteId}
        onClose={() => setDeleteId(null)}
        onConfirm={handleDelete}
        title="Удалить источник?"
        message="Источник будет удален. Материалы от этого источника сохранятся."
        confirmText="Удалить"
        variant="danger"
        loading={deleteSource.isPending}
      />
    </div>
  );
};