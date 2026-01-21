import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Modal, Spinner } from '@/components/ui';
import { ArticleDetailView, ArticleEditor, ArticlePreviewView } from '@/components/articles';
import { ConfirmDialog } from '@/components/common';
import { 
  useArticle, 
  useArticleVersions,
  useApproveArticle, 
  useRejectArticle,
  useUpdateArticle,
  useAIRewrite,
  useArticlePreview,
  useRestoreVersion,
} from '@/hooks';
import { ArticleUpdate } from '@/types';

export const ArticlePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [mode, setMode] = useState<'view' | 'edit'>('view');
  const [showPreview, setShowPreview] = useState(false);
  const [showRejectDialog, setShowRejectDialog] = useState(false);
  const [showScheduleDialog, setShowScheduleDialog] = useState(false);

  const { data: article, isLoading } = useArticle(id!);
  const { data: versions } = useArticleVersions(id!);
  const { data: preview } = useArticlePreview(id!);

  const approveArticle = useApproveArticle();
  const rejectArticle = useRejectArticle();
  const updateArticle = useUpdateArticle();
  const aiRewrite = useAIRewrite();
  const restoreVersion = useRestoreVersion();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!article) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Материал не найден</p>
      </div>
    );
  }

  const handleApprove = async () => {
    await approveArticle.mutateAsync({ id: article.id });
    navigate('/queue');
  };

  const handleReject = async () => {
    await rejectArticle.mutateAsync({ id: article.id });
    setShowRejectDialog(false);
    navigate('/queue');
  };

  const handleSave = async (data: ArticleUpdate) => {
    await updateArticle.mutateAsync({ id: article.id, data });
    setMode('view');
  };

  const handleAIRewrite = async () => {
    await aiRewrite.mutateAsync(article.id);
  };

  const handleRestoreVersion = async (versionId: string) => {
    try {
      await restoreVersion.mutateAsync({ articleId: article.id, versionId });
    } catch (err) {
      // error handled in hook
    }
  };

  return (
    <div>
      {mode === 'view' ? (
        <ArticleDetailView
          article={article}
          onApprove={handleApprove}
          onReject={() => setShowRejectDialog(true)}
          onEdit={() => setMode('edit')}
          onSchedule={() => setShowScheduleDialog(true)}
          isLoading={approveArticle.isPending}
        />
      ) : (
        <ArticleEditor
          article={article}
          versions={versions}
          onSave={handleSave}
          onPreview={() => setShowPreview(true)}
          onAIRewrite={handleAIRewrite}
          onRestoreVersion={handleRestoreVersion}
          isSaving={updateArticle.isPending}
        />
      )}

      {/* Preview Modal */}
      <Modal
        isOpen={showPreview}
        onClose={() => setShowPreview(false)}
        title="Предпросмотр"
        size="lg"
      >
        {preview && <ArticlePreviewView preview={preview} />}
      </Modal>

      {/* Reject Confirmation */}
      <ConfirmDialog
        isOpen={showRejectDialog}
        onClose={() => setShowRejectDialog(false)}
        onConfirm={handleReject}
        title="Отклонить материал?"
        message="Материал будет отклонен и не будет опубликован."
        confirmText="Отклонить"
        variant="danger"
        loading={rejectArticle.isPending}
      />
    </div>
  );
};