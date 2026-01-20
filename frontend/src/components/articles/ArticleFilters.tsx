import React from 'react';
import { Search, Filter, X } from 'lucide-react';
import { Input, Select, Button } from '@/components/ui';
import { ArticleStatus } from '@/types';

interface ArticleFiltersProps {
  filters: {
    search?: string;
    status?: ArticleStatus[];
    category?: string;
    source_id?: string;
    has_image?: boolean;
  };
  onFiltersChange: (filters: any) => void;
  categories?: string[];
  sources?: { id: string; name: string }[];
}

const statusOptions = [
  { value: '', label: 'Все статусы' },
  { value: 'pending', label: 'Ожидает' },
  { value: 'approved', label: 'Одобрено' },
  { value: 'rejected', label: 'Отклонено' },
  { value: 'published', label: 'Опубликовано' },
  { value: 'scheduled', label: 'Запланировано' },
  { value: 'failed', label: 'Ошибка' },
];

export const ArticleFilters: React.FC<ArticleFiltersProps> = ({
  filters,
  onFiltersChange,
  categories = [],
  sources = [],
}) => {
  const [isExpanded, setIsExpanded] = React.useState(false);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ ...filters, search: e.target.value });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    onFiltersChange({ 
      ...filters, 
      status: value ? [value as ArticleStatus] : undefined 
    });
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFiltersChange({ ...filters, category: e.target.value || undefined });
  };

  const handleSourceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFiltersChange({ ...filters, source_id: e.target.value || undefined });
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters = filters.status?.length || filters.category || filters.source_id || filters.search;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск по заголовку..."
              value={filters.search || ''}
              onChange={handleSearchChange}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        {/* Quick filters */}
        <div className="flex gap-2">
          <Select
            options={statusOptions}
            value={filters.status?.[0] || ''}
            onChange={handleStatusChange}
            className="w-40"
          />
          
          <Button
            variant="outline"
            onClick={() => setIsExpanded(!isExpanded)}
            icon={<Filter className="w-4 h-4" />}
          >
            Фильтры
          </Button>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              onClick={clearFilters}
              icon={<X className="w-4 h-4" />}
            >
              Сбросить
            </Button>
          )}
        </div>
      </div>

      {/* Expanded filters */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Select
            label="Категория"
            options={[
              { value: '', label: 'Все категории' },
              ...categories.map((c) => ({ value: c, label: c })),
            ]}
            value={filters.category || ''}
            onChange={handleCategoryChange}
          />
          
          <Select
            label="Источник"
            options={[
              { value: '', label: 'Все источники' },
              ...sources.map((s) => ({ value: s.id, label: s.name })),
            ]}
            value={filters.source_id || ''}
            onChange={handleSourceChange}
          />

          <Select
            label="Изображения"
            options={[
              { value: '', label: 'Любые' },
              { value: 'true', label: 'С изображениями' },
              { value: 'false', label: 'Без изображений' },
            ]}
            value={filters.has_image === undefined ? '' : String(filters.has_image)}
            onChange={(e) => onFiltersChange({ 
              ...filters, 
              has_image: e.target.value === '' ? undefined : e.target.value === 'true'
            })}
          />
        </div>
      )}
    </div>
  );
};