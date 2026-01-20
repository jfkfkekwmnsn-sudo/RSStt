import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui';
import { ArticleList, ArticleFilters } from '@/components/articles';
import { ConfirmDialog } from '@/components/common';
import { useArticleQueue, useApproveArticle, useRejectArticle } from '@/hooks';

export const Queue: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [page, setPage] = useState(1);
  const [confirmAction, setConfirmAction] = useState<{
    type: 'approve' | 'reject';
    articleId: string;
  } | null>(null);

  const filters = {
    priority: searchParams.get('priority') || undefined,
    category: searchParams.get('category') || undefined,
  };

  const { data, isLoading, refetch } = useArticleQueue({
    page,
    per_page: 20,
    ...filters,
  });

  const approveArticle = useApproveArticle();
  const rejectArticle = useRejectArticle();

  const handleApprove = (id: string) => {
    setConfirmAction({ type: 'approve', articleId: id });
  };

  const handleReject = (id: string) => {
    setConfirmAction({ type: 'reject', articleId: id });
  };

  const handleConfirm = async () => {
    if (!confirmAction) return;

    if (confirmAction.type === 'approve') {
      await approveArticle.mutateAsync({ id: confirmAction.articleId });
    } else {
      await rejectArticle.mutateAsync({ id: confirmAction.articleId });
    }
    
    setConfirmAction(null);
  };

  const handleFiltersChange = (newFilters: any) => {
    const params = new URLSearchParams();
    if (newFilters.priority) params.set('priority', newFilters.priority);
    if (newFilters.category) params.set('category', newFilters.category);
    setSearchParams(params);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Очередь модерации</h1>
          <p className="text-gray-500 mt-1">
            {data?.total || 0} материалов ожидают проверки
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetch()}
          icon={<RefreshCw className="w-4 h-4" />}
        >
          Обновить
        </Button>
      </div>

      <ArticleFilters
        filters={filters}
        onFiltersChange={handleFiltersChange}
      />

      <ArticleList
        data={data}
        isLoading={isLoading}
        page={page}
        onPageChange={setPage}
        onApprove={handleApprove}
        onReject={handleReject}
        showActions={true}
        emptyTitle="Очередь пуста"
        emptyDescription="Все материалы обработаны. Новые появятся после сбора из источников."
      />

      <ConfirmDialog
        isOpen={!!confirmAction}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleConfirm}
        title={confirmAction?.type === 'approve' ? 'Одобрить материал?' : 'Отклонить материал?'}
        message={
          confirmAction?.type === 'approve'
            ? 'Материал будет отправлен на публикацию.'
            : 'Материал будет отклонен и не будет опубликован.'
        }
        confirmText={confirmAction?.type === 'approve' ? 'Одобрить' : 'Отклонить'}
        variant={confirmAction?.type === 'approve' ? 'info' : 'danger'}
        loading={approveArticle.isPending || rejectArticle.isPending}
      />
    </div>
  );
};