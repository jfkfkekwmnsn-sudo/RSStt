import React from 'react';
import { Badge } from '@/components/ui';
import { getStatusLabel, getStatusColor } from '@/utils';
import { ArticleStatus } from '@/types';

interface StatusBadgeProps {
  status: ArticleStatus;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'md' }) => {
  const colorClass = getStatusColor(status);
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colorClass}`}>
      {getStatusLabel(status)}
    </span>
  );
};