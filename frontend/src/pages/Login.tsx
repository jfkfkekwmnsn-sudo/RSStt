import React from 'react';
import { Navigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Newspaper } from 'lucide-react';
import { Button, Input, Card } from '@/components/ui';
import { useAuth } from '@/hooks';
import { LoginRequest } from '@/types';

const loginSchema = z.object({
  username: z.string().min(3, 'Минимум 3 символа'),
  password: z.string().min(6, 'Минимум 6 символов'),
});

export const Login: React.FC = () => {
  const { isAuthenticated, login } = useAuth();
  const [isLoading, setIsLoading] = React.useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginRequest>({
    resolver: zodResolver(loginSchema),
  });

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (data: LoginRequest) => {
    setIsLoading(true);
    try {
      await login(data);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-100 rounded-full mb-4">
            <Newspaper className="w-8 h-8 text-primary-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">News Aggregator</h1>
          <p className="text-gray-600 mt-2">Войдите в систему</p>
        </div>

        <Card>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <Input
              label="Имя пользователя"
              {...register('username')}
              error={errors.username?.message}
              autoComplete="username"
            />

            <Input
              label="Пароль"
              type="password"
              {...register('password')}
              error={errors.password?.message}
              autoComplete="current-password"
            />

            <Button
              type="submit"
              className="w-full"
              loading={isLoading}
            >
              Войти
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
};