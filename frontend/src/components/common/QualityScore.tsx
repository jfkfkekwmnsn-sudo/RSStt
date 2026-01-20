import React from 'react';
import { cn } from '@/utils';

interface QualityScoreProps {
  score: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export const QualityScore: React.FC<QualityScoreProps> = ({ 
  score, 
  showLabel = true, 
  size = 'md' 
}) => {
  const percentage = Math.round(score * 100);
  
  const getColor = () => {
    if (percentage >= 70) return 'bg-green-500';
    if (percentage >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const sizes = {
    sm: 'h-1.5 w-16',
    md: 'h-2 w-24',
    lg: 'h-3 w-32',
  };

  return (
    <div className="flex items-center gap-2">
      <div className={cn('bg-gray-200 rounded-full overflow-hidden', sizes[size])}>
        <div
          className={cn('h-full rounded-full transition-all', getColor())}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <span className="text-sm text-gray-600 font-medium">{percentage}%</span>
      )}
    </div>
  );
};