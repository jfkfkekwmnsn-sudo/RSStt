import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, Badge } from '@/components/ui';
import { ArticlePreview as ArticlePreviewType } from '@/types';

interface ArticlePreviewProps {
  preview: ArticlePreviewType;
}

export const ArticlePreviewView: React.FC<ArticlePreviewProps> = ({ preview }) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Предпросмотр публикации</CardTitle>
          <Badge variant={preview.is_valid_for_telegram ? 'success' : 'warning'}>
            {preview.estimated_length} символов
          </Badge>
        </div>
      </CardHeader>

      {/* Warnings */}
      {preview.warnings.length > 0 && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-yellow-800">
              {preview.warnings.map((warning, index) => (
                <p key={index}>{warning}</p>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Preview */}
      <div className="bg-gray-900 rounded-lg p-4 text-white">
        <div className="max-w-md mx-auto">
          {/* Telegram-like message bubble */}
          <div className="bg-blue-600 rounded-2xl rounded-bl-sm p-4">
            {preview.has_image && preview.image_url && (
              <div className="mb-3 -mx-4 -mt-4">
                <img
                  src={preview.image_url}
                  alt=""
                  className="w-full rounded-t-2xl max-h-48 object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            )}
            <div 
              className="text-sm whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ 
                __html: preview.text
                  .replace(/</g, '&lt;')
                  .replace(/>/g, '&gt;')
                  .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                  .replace(/\n/g, '<br/>')
              }}
            />
          </div>
        </div>
      </div>
    </Card>
  );
};