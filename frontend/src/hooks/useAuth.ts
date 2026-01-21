import { useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store';
import { authApi } from '@/api';
import { LoginRequest } from '@/types';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/utils/error';

export function useAuth() {
  const navigate = useNavigate();
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;

  const { 
    isAuthenticated, 
    user, 
    accessToken,
    setTokens, 
    setUser, 
    logout: storeLogout,
    setLoading 
  } = useAuthStore();

  useEffect(() => {
    const checkAuth = async () => {
      if (accessToken && !user) {
        try {
          const userData = await authApi.me();
          setUser(userData);
        } catch (error) {
          storeLogout();
        }
      }
      setLoading(false);
    };
    
    checkAuth();
  }, [accessToken, user, setUser, storeLogout, setLoading]);

  const login = useCallback(async (data: LoginRequest) => {
    try {
      const response = await authApi.login(data);
      setTokens(response.access_token, response.refresh_token);
      
      const userData = await authApi.me();
      setUser(userData);
      
      toast.success('Добро пожаловать!');
      navigateRef.current('/');
    } catch (error) {
      const message = getErrorMessage(error, 'Ошибка авторизации');
      toast.error(message);
      throw error;
    }
  }, [setTokens, setUser]);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch (error) {
      // Ignore logout errors
    } finally {
      storeLogout();
      navigateRef.current('/login');
    }
  }, [storeLogout]);

  const hasPermission = useCallback((permission: string) => {
    return user?.permissions?.includes(permission) || user?.is_superuser;
  }, [user]);

  const hasRole = useCallback((roles: string | string[]) => {
    if (!user) return false;
    const roleArray = Array.isArray(roles) ? roles : [roles];
    return roleArray.includes(user.role) || user.is_superuser;
  }, [user]);

  return {
    isAuthenticated,
    user,
    login,
    logout,
    hasPermission,
    hasRole,
  };
}