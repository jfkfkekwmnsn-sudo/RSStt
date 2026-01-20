import React from 'react';
import { Save, Key, Bell, Database, Cpu } from 'lucide-react';
import { Card, CardHeader, CardTitle, Button, Input, Select } from '@/components/ui';
import { useAIUsage } from '@/hooks';
import { formatNumber, formatPercent } from '@/utils';

export const Settings: React.FC = () => {
  const { data: aiUsage } = useAIUsage();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Настройки</h1>
        <p className="text-gray-500 mt-1">
          Конфигурация системы
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* AI Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cpu className="w-5 h-5" />
              AI Настройки
            </CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium">Токенов сегодня</p>
                <p className="text-2xl font-bold">{formatNumber(aiUsage?.tokens_today || 0)}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-500">Лимит</p>
                <p className="font-medium">{formatNumber(aiUsage?.limit || 0)}</p>
              </div>
            </div>
            
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-primary-600 h-3 rounded-full transition-all"
                style={{ width: `${Math.min(aiUsage?.usage_percent || 0, 100)}%` }}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-sm">AI рерайт включен</span>
              </label>
            </div>

            <Select
              label="Модель"
              options={[
                { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
                { value: 'gpt-4o', label: 'GPT-4o' },
                { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
              ]}
              defaultValue="gpt-4o-mini"
            />
          </div>
        </Card>

        {/* Telegram Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="w-5 h-5" />
              Telegram
            </CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <Input
              label="ID чата модерации"
              placeholder="-1001234567890"
            />
            
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded" defaultChecked />
                <span className="text-sm">Отправлять уведомления об ошибках</span>
              </label>
            </div>
            
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded" />
                <span className="text-sm">Уведомлять о пустой очереди</span>
              </label>
            </div>
          </div>
        </Card>

        {/* Publishing Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="w-5 h-5" />
              Публикация
            </CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <Input
              label="Минимальный интервал (секунды)"
              type="number"
              defaultValue={60}
            />
            
            <Input
              label="Макс. попыток публикации"
              type="number"
              defaultValue={3}
            />
            
            <Select
              label="Политика при конфликте времени"
              options={[
                { value: 'shift', label: 'Сдвигать' },
                { value: 'block', label: 'Блокировать' },
              ]}
              defaultValue="shift"
            />
          </div>
        </Card>

        {/* Ingestion Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="w-5 h-5" />
              Сбор контента
            </CardTitle>
          </CardHeader>
          <div className="space-y-4">
            <Input
              label="Интервал сбора по умолчанию (минуты)"
              type="number"
              defaultValue={15}
            />
            
            <Input
              label="Макс. материалов за раз"
              type="number"
              defaultValue={50}
            />
            
            <Input
              label="Свежесть материалов (дни)"
              type="number"
              defaultValue={7}
            />
          </div>
        </Card>
      </div>

      <div className="flex justify-end">
        <Button icon={<Save className="w-4 h-4" />}>
          Сохранить настройки
        </Button>
      </div>
    </div>
  );
};