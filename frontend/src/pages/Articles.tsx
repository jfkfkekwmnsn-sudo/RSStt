import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArticleList, ArticleFilters } from '@/components/articles';
import type { ArticleFilters as ArticleFiltersType } from '@/types';
import { useArticles } from '@/hooks';
import { ArticleStatus } from '@/types';

export const Articles: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [page, setPage] = useState(1);

  const filters = {
    status: searchParams.get('status') 
      ? [searchParams.get('status') as ArticleStatus] 
      : undefined,
    category: searchParams.get('category') || undefined,
    source_id: searchParams.get('source_id') || undefined,
    search: searchParams.get('search') || undefined,
  };

  const { data, isLoading } = useArticles({
    page,
    per_page: 20,
    ...filters,
  });

  const handleFiltersChange = (newFilters: Partial<ArticleFiltersType & { page?: number; per_page?: number }>) => {
    const params = new URLSearchParams();
    if (newFilters.status?.[0]) params.set('status', newFilters.status[0]);
    if (newFilters.category) params.set('category', newFilters.category);
    if (newFilters.source_id) params.set('source_id', newFilters.source_id);
    if (newFilters.search) params.set('search', newFilters.search);
    setSearchParams(params);
    setPage(1);
  }; 

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Все материалы</h1>
        <p className="text-gray-500 mt-1">
          {data?.total || 0} материалов
        </p>
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
        showActions={false}
      />
    </div>
  );
};