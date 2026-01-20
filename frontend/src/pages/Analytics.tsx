import React, { useState } from 'react';
import { format, subDays } from 'date-fns';
import { Card, CardHeader, CardTitle, Select, Spinner } from '@/components/ui';
import { useAnalyticsSummary, useAIUsage } from '@/hooks';
import { formatNumber, formatPercent } from '@/utils';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export const Analytics: React.FC = () => {
  const [period, setPeriod] = useState('30');
  
  const dateFrom = format(subDays(new Date(), parseInt(period)), 'yyyy-MM-dd');
  const dateTo = format(new Date(), 'yyyy-MM-dd');
  
  const { data, isLoading } = useAnalyticsSummary(dateFrom, dateTo);
  const { data: aiUsage } = useAIUsage();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" />
      </div>
    );
  }

  const summary = data?.summary;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Аналитика</h1>
        <Select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          options={[
            { value: '7', label: 'Последние 7 дней' },
            { value: '30', label: 'Последние 30 дней' },
            { value: '90', label: 'Последние 90 дней' },
          ]}
          className="w-48"
        />
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <p className="text-sm text-gray-500">Всего материалов</p>
          <p className="text-3xl font-bold">{formatNumber(summary?.total_articles || 0)}</p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Опубликовано</p>
          <p className="text-3xl font-bold text-green-600">
            {formatNumber(summary?.published_articles || 0)}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Approval Rate</p>
          <p className="text-3xl font-bold text-blue-600">
            {formatPercent(summary?.approval_rate || 0)}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-gray-500">Ср. время обработки</p>
          <p className="text-3xl font-bold">
            {summary?.avg_processing_time_minutes 
              ? `${Math.round(summary.avg_processing_time_minutes)} мин`
              : '—'
            }
          </p>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Articles over time */}
        <Card>
          <CardHeader>
            <CardTitle>Материалы по дням</CardTitle>
          </CardHeader>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data?.articles_by_day || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(val) => format(new Date(val), 'dd.MM')}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(val) => format(new Date(val), 'dd.MM.yyyy')}
                />
                <Line 
                  type="monotone" 
                  dataKey="count" 
                  stroke="#3b82f6" 
                  strokeWidth={2}
                  name="Материалов"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Categories pie */}
        <Card>
          <CardHeader>
            <CardTitle>По категориям</CardTitle>
          </CardHeader>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data?.categories || []}
                  dataKey="total"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({ category, percent }) => 
                    `${category} (${(percent * 100).toFixed(0)}%)`
                  }
                >
                  {data?.categories?.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Sources performance */}
        <Card>
          <CardHeader>
            <CardTitle>Топ источников</CardTitle>
          </CardHeader>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data?.top_sources?.slice(0, 8) || []} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="source_name" type="category" width={150} />
                <Tooltip />
                <Legend />
                <Bar dataKey="approved" name="Одобрено" fill="#10b981" stackId="a" />
                <Bar dataKey="rejected" name="Отклонено" fill="#ef4444" stackId="a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* AI Usage */}
        <Card>
          <CardHeader>
            <CardTitle>Использование AI</CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Токенов сегодня:</span>
              <span className="font-bold">{formatNumber(aiUsage?.tokens_today || 0)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Лимит:</span>
              <span className="font-bold">{formatNumber(aiUsage?.limit || 0)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Осталось:</span>
              <span className="font-bold text-green-600">
                {formatNumber(aiUsage?.remaining || 0)}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-4">
              <div
                className="bg-primary-600 h-4 rounded-full transition-all"
                style={{ width: `${Math.min(aiUsage?.usage_percent || 0, 100)}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 text-center">
              {(aiUsage?.usage_percent || 0).toFixed(1)}% использовано
            </p>
          </div>
        </Card>
      </div>

      {/* Detailed tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Categories table */}
        <Card>
          <CardHeader>
            <CardTitle>Статистика по категориям</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Категория
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Всего
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Одобрено
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Approval
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data?.categories?.map((cat) => (
                  <tr key={cat.category}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {cat.category}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 text-right">
                      {formatNumber(cat.total)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 text-right">
                      {formatNumber(cat.approved)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 text-right">
                      {formatPercent(cat.approval_rate)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Sources table */}
        <Card>
          <CardHeader>
            <CardTitle>Статистика по источникам</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Источник
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Всего
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Качество
                  </th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Репутация
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {data?.top_sources?.map((src) => (
                  <tr key={src.source_id}>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {src.source_name}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 text-right">
                      {formatNumber(src.total)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 text-right">
                      {formatPercent(src.avg_quality)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 text-right">
                      {formatPercent(src.reputation_score)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </div>
  );
};