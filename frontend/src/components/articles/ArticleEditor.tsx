import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Save, Eye, RotateCcw, Sparkles } from 'lucide-react';
import { Card, CardHeader, CardTitle, Button, Input, Select } from '@/components/ui';
import { ArticleDetail, ArticleUpdate, ArticleVersion } from '@/types';

interface ArticleEditorProps {
  article: ArticleDetail;
  versions?: ArticleVersion[];
  onSave: (data: ArticleUpdate) => Promise<void>;
  onPreview?: () => void;
  onAIRewrite?: () => void;
  onRestoreVersion?: (versionId: string) => void;
  isSaving?: boolean;
}

const categoryOptions = [
  { value: 'технологии', label: 'Технологии' },
  { value: 'политика', label: 'Политика' },
  { value: 'экономика', label: 'Экономика' },
  { value: 'спорт', label: 'Спорт' },
  { value: 'наука', label: 'Наука' },
  { value: 'культура', label: 'Культура' },
  { value: 'новости', label: 'Новости' },
];

export const ArticleEditor: React.FC<ArticleEditorProps> = ({
  article,
  versions = [],
  onSave,
  onPreview,
  onAIRewrite,
  onRestoreVersion,
  isSaving,
}) => {
  const [showVersions, setShowVersions] = useState(false);

  const { register, handleSubmit, reset, formState: { isDirty } } = useForm<ArticleUpdate>({
    defaultValues: {
      title: article.title,
      content_clean: article.content_clean || '',
      category: article.category || '',
      tags: article.tags || [],
      main_image_url: article.main_image_url || '',
    },
  });

  useEffect(() => {
    reset({
      title: article.title,
      content_clean: article.content_clean || '',
      category: article.category || '',
      tags: article.tags || [],
      main_image_url: article.main_image_url || '',
    });
  }, [article, reset]);

  const onSubmit = async (data: ArticleUpdate) => {
    await onSave(data);
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit(onSubmit)}>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Редактирование</CardTitle>
              <div className="flex items-center gap-2">
                {onAIRewrite && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={onAIRewrite}
                    icon={<Sparkles className="w-4 h-4" />}
                  >
                    AI Рерайт
                  </Button>
                )}
                {onPreview && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={onPreview}
                    icon={<Eye className="w-4 h-4" />}
                  >
                    Превью
                  </Button>
                )}
                <Button
                  type="submit"
                  size="sm"
                  loading={isSaving}
                  disabled={!isDirty}
                  icon={<Save className="w-4 h-4" />}
                >
                  Сохранить
                </Button>
              </div>
            </div>
          </CardHeader>

          <div className="space-y-4">
            <Input
              label="Заголовок"
              {...register('title', { required: true })}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Текст
              </label>
              <textarea
                {...register('content_clean')}
                rows={12}
                className="block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <Select
                label="Категория"
                options={categoryOptions}
                {...register('category')}
              />
              
              <Input
                label="URL изображения"
                {...register('main_image_url')}
                placeholder="https://..."
              />
            </div>

            <Input
              label="Теги (через запятую)"
              {...register('tags')}
              placeholder="тег1, тег2, тег3"
            />
          </div>
        </Card>
      </form>

      {/* Version history */}
      {versions.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>История версий ({versions.length})</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowVersions(!showVersions)}
              >
                {showVersions ? 'Скрыть' : 'Показать'}
              </Button>
            </div>
          </CardHeader>

          {showVersions && (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {versions.map((version) => (
                <div
                  key={version.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium">
                      Версия {version.version_number}
                    </p>
                    <p className="text-xs text-gray-500">
                      {version.created_by_name || 'Система'} • {new Date(version.created_at).toLocaleString('ru')}
                    </p>
                    {version.change_summary && (
                      <p className="text-xs text-gray-600 mt-1">{version.change_summary}</p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onRestoreVersion?.(version.id)}
                    icon={<RotateCcw className="w-4 h-4" />}
                  >
                    Восстановить
                  </Button>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};