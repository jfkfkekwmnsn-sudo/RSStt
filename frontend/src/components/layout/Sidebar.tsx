import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  FileText,
  Inbox,
  Rss,
  Settings,
  BarChart3,
  BookTemplate,
  Zap,
  Send,
  X,
} from 'lucide-react';
import { cn } from '@/utils';
import { useUIStore, useAuthStore } from '@/store';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
  roles?: string[];
}

const navItems: NavItem[] = [
  { to: '/', icon: <LayoutDashboard className="w-5 h-5" />, label: 'Дашборд' },
  { to: '/queue', icon: <Inbox className="w-5 h-5" />, label: 'Очередь' },
  { to: '/articles', icon: <FileText className="w-5 h-5" />, label: 'Материалы' },
  { to: '/sources', icon: <Rss className="w-5 h-5" />, label: 'Источники' },
  { to: '/rules', icon: <Zap className="w-5 h-5" />, label: 'Правила', roles: ['admin', 'chief_editor'] },
  { to: '/templates', icon: <BookTemplate className="w-5 h-5" />, label: 'Шаблоны', roles: ['admin', 'chief_editor'] },
  { to: '/targets', icon: <Send className="w-5 h-5" />, label: 'Каналы', roles: ['admin'] },
  { to: '/analytics', icon: <BarChart3 className="w-5 h-5" />, label: 'Аналитика' },
  { to: '/settings', icon: <Settings className="w-5 h-5" />, label: 'Настройки', roles: ['admin'] },
];

export const Sidebar: React.FC = () => {
  const { sidebarOpen, setSidebarOpen } = useUIStore();
  const { user } = useAuthStore();

  const filteredItems = navItems.filter(
    (item) => !item.roles || item.roles.includes(user?.role || '')
  );

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-0 left-0 z-50 h-full w-64 bg-white border-r border-gray-200 transform transition-transform lg:translate-x-0 lg:static lg:z-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 lg:hidden">
          <span className="text-lg font-semibold">Меню</span>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-1 rounded-lg hover:bg-gray-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-4 space-y-1">
          {filteredItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                )
              }
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  );
};