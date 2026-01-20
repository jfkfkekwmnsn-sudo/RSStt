import React from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Clock, Image as ImageIcon, Sparkles } from 'lucide-react';
import { Card, Badge, Button } from '@/components/ui';
import { StatusBadge, QualityScore, PriorityIndicator } from '@/components/common';
import { ArticleListItem } from '@/types';
import { formatRelativeTime, getCategoryEmoji, truncate } from '@/utils';

interface ArticleCardProps {
  article: ArticleListItem;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  showActions?: boolean;
}

export const ArticleCard: React.FC<ArticleCardProps> = ({
  article,
  onApprove,
  onReject,
  showActions = true,
}) => {
  const canModerate = article.status === 'pending' || article.status === 'needs_review';

  return (
    <Card className="hover:shadow-md transition-shadow">
      <div className="flex gap-4">
        {/* Image placeholder */}
        <div className="flex-shrink-0">
          {article.has_image ? (
            <div className="w-24 h-24 bg-gray-100 rounded-lg flex items-center justify-center">
              <ImageIcon className="w-8 h-8 text-gray-400" />
            </div>
          ) : (
            <div className="w-24 h-24 bg-gray-50 rounded-lg flex items-center justify-center">
              <span className="text-3xl">{getCategoryEmoji(article.category || '')}</span>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-2">
            <Link 
              to={`/articles/${article.id}`}
              className="text-base font-medium text-gray-900 hover:text-primary-600 line-clamp-2"
            >
              {article.title}
            </Link>
            <StatusBadge status={article.status} />
          </div>

          <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
            {article.category && (
              <span className="flex items-center gap-1">
                {getCategoryEmoji(article.category)} {article.category}
              </span>
            )}
            {article.source_name && (
              <span>{article.source_name}</span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {formatRelativeTime(article.created_at)}
            </span>
            {article.ai_used && (
              <span className="flex items-center gap-1 text-purple-600">
                <Sparkles className="w-3.5 h-3.5" />
                AI
              </span>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Качество:</span>
                <QualityScore score={article.quality_score} size="sm" />
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">Приоритет:</span>
                <PriorityIndicator priority={article.priority_score} />
              </div>
            </div>

            {showActions && canModerate && (
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.preventDefault();
                    onReject?.(article.id);
                  }}
                >
                  Отклонить
                </Button>
                <Button
                  size="sm"
                  onClick={(e) => {
                    e.preventDefault();
                    onApprove?.(article.id);
                  }}
                >
                  Одобрить
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};