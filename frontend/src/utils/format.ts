import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

export function formatDate(date: string | Date, formatStr = 'dd.MM.yyyy HH:mm'): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, formatStr, { locale: ru });
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true, locale: ru });
}

export function formatPercent(value: number, decimals = 0): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('ru-RU').format(value);
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: 'Ожидает',
    approved: 'Одобрено',
    rejected: 'Отклонено',
    scheduled: 'Запланировано',
    published: 'Опубликовано',
    failed: 'Ошибка',
    duplicate: 'Дубликат',
    needs_review: 'На проверку',
  };
  return labels[status] || status;
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    approved: 'bg-green-100 text-green-800',
    rejected: 'bg-red-100 text-red-800',
    scheduled: 'bg-blue-100 text-blue-800',
    published: 'bg-emerald-100 text-emerald-800',
    failed: 'bg-red-100 text-red-800',
    duplicate: 'bg-gray-100 text-gray-800',
    needs_review: 'bg-orange-100 text-orange-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}

export function getCategoryEmoji(category: string): string {
  const emojis: Record<string, string> = {
    технологии: '💻',
    политика: '🏛',
    экономика: '📈',
    спорт: '⚽',
    наука: '🔬',
    культура: '🎭',
    новости: '📰',
  };
  return emojis[category?.toLowerCase()] || '📰';
}