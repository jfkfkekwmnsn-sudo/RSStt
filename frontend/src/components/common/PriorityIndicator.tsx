import React from 'react';
import { cn } from '@/utils';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';

interface PriorityIndicatorProps {
  priority: number;
  showValue?: boolean;
}

export const PriorityIndicator: React.FC<PriorityIndicatorProps> = ({ 
  priority, 
  showValue = true 
}) => {
  const getLevel = () => {
    if (priority >= 70) return { icon: ArrowUp, color: 'text-green-600', label: 'Высокий' };
    if (priority >= 40) return { icon: Minus, color: 'text-yellow-600', label: 'Средний' };
    return { icon: ArrowDown, color: 'text-gray-400', label: 'Низкий' };
  };

  const { icon: Icon, color, label } = getLevel();

  return (
    <div className="flex items-center gap-1">
      <Icon className={cn('w-4 h-4', color)} />
      {showValue && <span className="text-sm text-gray-600">{priority}</span>}
    </div>
  );
};