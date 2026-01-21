import React from 'react';
import { Link } from 'react-router-dom';
import { 
  FileText, CheckCircle, XCircle, Clock, Send, 
  TrendingUp, AlertTriangle, ArrowRight 
} from 'lucide-react';
import { Card, CardHeader, CardTitle, Spinner } from '@/components/ui';
import { useAnalyticsSummary, useArticleQueue } from '@/hooks';
import { formatNumber, formatPercent } from '@/utils';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';

export const Dashboard: React.FC = () => {
  const { data: analytics, isLoading: analyticsLoading, error: analyticsError } = useAnalyticsSummary();
  const { data: queue, isLoading: queueLoading } = useArticleQueue({ per_page: 5 });

  if (analyticsLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  if (analyticsError) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <p className="text-red-600 font-medium mb-2">Ошибка загрузки аналитики</p>
          <p className="text-gray-600 text-sm">Проверьте соединение с сервером</p>
        </div>
      </div>
    );
  }

  const stats = analytics?.summary;

  const statCards = [
    {
      title: 'Всего материалов',
      value: stats?.total_articles || 0,
      icon: FileText,
      color: 'text-blue-600 bg-blue-100',
    },
    {
      title: 'В очереди',
      value: stats?.pending_articles || 0,
      icon: Clock,
      color: 'text-yellow-600 bg-yellow-100',
      link: '/queue',
    },
    {
      title: 'Одобрено',
      value: stats?.approved_articles || 0,
      icon: CheckCircle,
      color: 'text-green-600 bg-green-100',
    },
    {
      title: 'Опубликовано',
      value: stats?.published_articles || 0,
      icon: Send,
      color: 'text-emerald-600 bg-emerald-100',
    },
    {
      title: 'Отклонено',
      value: stats?.rejected_articles || 0,
      icon: XCircle,
      color: 'text-red-600 bg-red-100',
    },
    {
      title: 'Approval Rate',
      value: formatPercent(stats?.approval_rate || 0),
      icon: TrendingUp,
      color: 'text-purple-600 bg-purple-100',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Дашборд</h1>
        <div className="text-sm text-gray-500">
          Сегодня: {formatNumber(stats?.articles_today || 0)} материалов
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {statCards.map((stat) => (
          <Card key={stat.title} padding="sm">
            {stat.link ? (
              <Link to={stat.link} className="block hover:bg-gray-50 -m-3 p-3 rounded-lg transition-colors">
                <StatCardContent {...stat} />
              </Link>
            ) : (
              <StatCardContent {...stat} />
            )}
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Материалы по дням</CardTitle>
          </CardHeader>
          <div className="h-64">
            {analytics?.articles_by_day && (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.articles_by_day}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="date" 
                    tickFormatter={(val) => new Date(val).toLocaleDateString('ru', { day: 'numeric', month: 'short' })}
                  />
                  <YAxis />
                  <Tooltip 
                    labelFormatter={(val) => new Date(val).toLocaleDateString('ru')}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="count" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={false}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>

        {/* Categories */}
        <Card>
          <CardHeader>
            <CardTitle>По категориям</CardTitle>
          </CardHeader>
          <div className="h-64">
            {analytics?.categories && (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={analytics.categories.slice(0, 6)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" />
                  <YAxis dataKey="category" type="category" width={100} />
                  <Tooltip />
                  <Bar dataKey="total" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      {/* Queue preview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Очередь модерации</CardTitle>
            <Link 
              to="/queue" 
              className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
            >
              Все материалы
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </CardHeader>

        {queueLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : queue?.items.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
            <p>Очередь пуста! Все материалы обработаны.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {queue?.items.map((article) => (
              <Link
                key={article.id}
                to={`/articles/${article.id}`}
                className="block p-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {article.title}
                    </p>
                    <p className="text-xs text-gray-500">
                      {article.source_name} • {article.category}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <span className="text-xs text-gray-500">
                      Q: {Math.round(article.quality_score * 100)}%
                    </span>
                    <span className="text-xs text-gray-500">
                      P: {article.priority_score}
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};

const StatCardContent: React.FC<{
  title: string;
  value: number | string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  color: string;
}> = ({ title, value, icon: Icon, color }) => (
  <>
    <div className={`inline-flex p-2 rounded-lg ${color} mb-2`}>
      <Icon className="w-5 h-5" />
    </div>
    <p className="text-2xl font-bold text-gray-900">{formatNumber(Number(value) || 0)}</p>
    <p className="text-xs text-gray-500">{title}</p>
  </>
);