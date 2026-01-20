export type UserRole = 'admin' | 'editor' | 'chief_editor' | 'analyst' | 'service';

export interface User {
  id: string;
  email: string;
  username: string;
  role: UserRole;
  telegram_user_id?: number;
  telegram_username?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface CurrentUser {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  telegram_user_id?: number;
  is_superuser: boolean;
  permissions: string[];
}

export interface LoginRequest {
  username: string;
  password: string;
}