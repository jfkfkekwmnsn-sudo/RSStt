import { apiClient } from '../client';
import { TokenResponse, CurrentUser, LoginRequest, MessageResponse } from '@/types';

export const authApi = {
  login: (data: LoginRequest) => 
    apiClient.post<TokenResponse>('/auth/login', data),

  refresh: (refreshToken: string) =>
    apiClient.post<TokenResponse>('/auth/refresh', { refresh_token: refreshToken }),

  logout: () =>
    apiClient.post<MessageResponse>('/auth/logout'),

  me: () =>
    apiClient.get<CurrentUser>('/auth/me'),

  changePassword: (currentPassword: string, newPassword: string) =>
    apiClient.post<MessageResponse>('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};