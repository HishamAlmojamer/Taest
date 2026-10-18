import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { CommandPalette } from '@/components/command/CommandPalette';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';

export function AppLayout() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-zinc-950">
      <CommandPalette />

      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <div
        className={cn(
          'fixed lg:static inset-y-0 right-0 z-40 transform transition-transform duration-300 lg:transform-none',
          mobileOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0',
          sidebarOpen ? 'lg:w-64' : 'lg:w-20'
        )}
      >
        <Sidebar collapsed={!sidebarOpen} onNavigate={() => setMobileOpen(false)} />
      </div>

      <div className="flex flex-col flex-1 overflow-hidden">
        <Header
          onMenuToggle={() => {
            if (window.innerWidth < 1024) {
              setMobileOpen(!mobileOpen);
            } else {
              toggleSidebar();
            }
          }}
        />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet key={location.pathname} />
        </main>
      </div>
    </div>
  );
}
