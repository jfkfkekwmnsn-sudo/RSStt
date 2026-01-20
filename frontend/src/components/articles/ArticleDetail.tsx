import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ExternalLink, Clock, User, Tag, Image as ImageIcon, 
  Sparkles, ArrowLeft, Edit, Check, X, Calendar
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Button, Badge } from '@/components/ui';
import { StatusBadge, QualityScore, PriorityIndicator } from '@/components/common';
import { ArticleDetail as ArticleDetailType } from '@/types';
import { formatDate, formatRelativeTime, getCategoryEmoji } from '@/utils';

interface ArticleDetailProps {
  article: ArticleDetailType;
  onApprove?: () => void;
  onReject?: () => void;
  onEdit?: () => void;
  onSchedule?: () => void;
  isLoading?: boolean;
}

export const ArticleDetailView: React.FC<ArticleDetailProps> = ({
  article,
  onApprove,
  onReject,
  onEdit,
  onSchedule,
  isLoading,
}) => {
  const canModerate = article.status === 'pending' || article.status === 'needs_review';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/queue"
          className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="w-4 h-4" />
          Назад к очереди
        </Link>
        
        <div className="flex items-center gap-2">
          <StatusBadge status={article.status} />
          {article.ai_used && (
            <Badge variant="info">
              <Sparkles className="w-3 h-3 mr-1" />
              AI
            </Badge>
          )}
        </div>
      </div>

      {/* Main content */}
      <Card>
        <div className="space-y-6">
          {/* Title and meta */}
          <div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              {getCategoryEmoji(article.category || '')} {article.title}
            </h1>
            
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              {article.source_name && (
                <span className="flex items-center gap-1">
                  📡 {article.source_name}
                </span>
              )}
              {article.category && (
                <span className="flex items-center gap-1">
                  📁 {article.category}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatRelativeTime(article.created_at)}
              </span>
              {article.pub_date && (
                <span className="flex items-center gap-1">
                  📅 {formatDate(article.pub_date, 'dd.MM.yyyy')}
                </span>
              )}
            </div>
          </div>

          {/* Image */}
          {article.main_image_url && (
            <div className="rounded-lg overflow-hidden bg-gray-100">
              <img
                src={article.main_image_url}
                alt={article.title}
                className="w-full max-h-96 object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          )}

          {/* Content */}
          <div className="prose prose-gray max-w-none">
            {article.content_clean ? (
              <div className="whitespace-pre-wrap">{article.content_clean}</div>
            ) : article.description ? (
              <p>{article.description}</p>
            ) : (
              <p className="text-gray-500 italic">Контент недоступен</p>
            )}
          </div>

          {/* Tags */}
          {article.tags && article.tags.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <Tag className="w-4 h-4 text-gray-400" />
              {article.tags.map((tag) => (
                <Badge key={tag} variant="default">#{tag}</Badge>
              ))}
            </div>
          )}

          {/* Link */}
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-primary-600 hover:text-primary-700"
          >
            <ExternalLink className="w-4 h-4" />
            Открыть оригинал
          </a>
        </div>
      </Card>

      {/* Scores */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Качество</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{Math.round(article.quality_score * 100)}%</span>
              <QualityScore score={article.quality_score} showLabel={false} size="lg" />
            </div>
            {article.quality_factors && (
              <div className="space-y-2 text-sm">
                {Object.entries(article.quality_factors).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key}:</span>
                    <span className="font-medium">{(value * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Приоритет</CardTitle>
          </CardHeader>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold">{article.priority_score}</span>
              <PriorityIndicator priority={article.priority_score} showValue={false} />
            </div>
            {article.priority_factors && (
              <div className="space-y-2 text-sm">
                {Object.entries(article.priority_factors).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-gray-600">{key}:</span>
                    <span className="font-medium">+{value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </Card>
      </div>

      {/* Moderation info */}
      {article.moderated_at && (
        <Card>
          <CardHeader>
            <CardTitle>Модерация</CardTitle>
          </CardHeader>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Модератор:</span>
              <p className="font-medium">{article.moderator_name || 'Неизвестно'}</p>
            </div>
            <div>
              <span className="text-gray-500">Время:</span>
              <p className="font-medium">{formatDate(article.moderated_at)}</p>
            </div>
            {article.rejection_reason && (
              <div className="col-span-2">
                <span className="text-gray-500">Причина отклонения:</span>
                <p className="font-medium text-red-600">{article.rejection_reason}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Similar articles */}
      {article.similar_articles && article.similar_articles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Похожие материалы</CardTitle>
          </CardHeader>
          <div className="space-y-2">
            {article.similar_articles.map((similar) => (
              <Link
                key={similar.id}
                to={`/articles/${similar.id}`}
                className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 line-clamp-1">
                    {similar.title}
                  </span>
                  <StatusBadge status={similar.status} size="sm" />
                </div>
              </Link>
            ))}
          </div>
        </Card>
      )}

      {/* Actions */}
      {canModerate && (
        <div className="flex items-center justify-end gap-3 sticky bottom-4 bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <Button variant="outline" onClick={onEdit} icon={<Edit className="w-4 h-4" />}>
            Редактировать
          </Button>
          <Button variant="outline" onClick={onSchedule} icon={<Calendar className="w-4 h-4" />}>
            Запланировать
          </Button>
          <Button variant="danger" onClick={onReject} icon={<X className="w-4 h-4" />}>
            Отклонить
          </Button>
          <Button onClick={onApprove} icon={<Check className="w-4 h-4" />} loading={isLoading}>
            Одобрить
          </Button>
        </div>
      )}
    </div>
  );
};