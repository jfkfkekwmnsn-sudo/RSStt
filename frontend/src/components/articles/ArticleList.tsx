import React from 'react';
import { ArticleCard } from './ArticleCard';
import { EmptyState } from '@/components/common';
import { Pagination, Spinner } from '@/components/ui';
import { ArticleListItem, PaginatedResponse } from '@/types';
import { FileText } from 'lucide-react';

interface ArticleListProps {
  data?: PaginatedResponse<ArticleListItem>;
  isLoading?: boolean;
  page: number;
  onPageChange: (page: number) => void;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  showActions?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
}

export const ArticleList: React.FC<ArticleListProps> = ({
  data,
  isLoading,
  page,
  onPageChange,
  onApprove,
  onReject,
  showActions = true,
  emptyTitle = 'Нет материалов',
  emptyDescription = 'Материалы появятся здесь после сбора из источников',
}) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={<FileText className="w-8 h-8 text-gray-400" />}
        title={emptyTitle}
        description={emptyDescription}
      />
    );
  }

  return (
    <div>
      <div className="space-y-4">
        {data.items.map((article) => (
          <ArticleCard
            key={article.id}
            article={article}
            onApprove={onApprove}
            onReject={onReject}
            showActions={showActions}
          />
        ))}
      </div>

      {data.pages > 1 && (
        <div className="mt-6">
          <Pagination
            page={page}
            totalPages={data.pages}
            onPageChange={onPageChange}
          />
        </div>
      )}
    </div>
  );
};