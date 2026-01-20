import React from 'react';
import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';
import { Button } from '@/components/ui';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-200">404</h1>
        <h2 className="text-2xl font-semibold text-gray-900 mt-4">
          Страница не найдена
        </h2>
        <p className="text-gray-600 mt-2">
          Запрашиваемая страница не существует или была удалена.
        </p>
        <Link to="/" className="inline-block mt-6">
          <Button icon={<Home className="w-4 h-4" />}>
            На главную
          </Button>
        </Link>
      </div>
    </div>
  );
};