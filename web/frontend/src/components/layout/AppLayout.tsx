import { useEffect, useRef, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { CommandPalette } from '@/components/command/CommandPalette';
import { useUIStore } from '@/stores/uiStore';
import { cn } from '@/lib/utils';

export function AppLayout() {
  const { sidebarOpen, setSidebarOpen, toggleSidebar } = useUIStore();
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const mainRef = useRef<HTMLElement>(null);

  useEffect(() => {
    setMobileOpen(false);
    mainRef.current?.scrollTo({ top: 0, behavior: 'auto' });
  }, [location.pathname]);

  useEffect(() => {
    if (!mobileOpen) return;

    const previousBodyOverflow = document.body.style.overflow;
    const main = mainRef.current;
    const previousMainOverflow = main?.style.overflow ?? '';

    document.body.style.overflow = 'hidden';
    if (main) main.style.overflow = 'hidden';

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setMobileOpen(false);
    };
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousBodyOverflow;
      if (main) main.style.overflow = previousMainOverflow;
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [mobileOpen]);

  useEffect(() => {
    const media = window.matchMedia('(min-width: 1024px)');
    const handleChange = (event: MediaQueryListEvent) => {
      if (event.matches) setMobileOpen(false);
    };
    media.addEventListener('change', handleChange);
    return () => media.removeEventListener('change', handleChange);
  }, []);

  const collapsed = !sidebarOpen && !mobileOpen;

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50 dark:bg-zinc-950">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:right-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-gray-900 focus:shadow-lg dark:focus:bg-zinc-900 dark:focus:text-zinc-100"
      >
        تخطَّ إلى المحتوى الرئيسي
      </a>

      <CommandPalette />

      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 animate-fade-in bg-black/50 backdrop-blur-[1px] lg:hidden"
          onClick={() => setMobileOpen(false)}
          aria-hidden="true"
        />
      )}

      <div
        className={cn(
          'fixed inset-y-0 right-0 z-40 w-72 transform transition-transform duration-300 lg:static lg:transform-none',
          mobileOpen ? 'translate-x-0 shadow-2xl' : 'translate-x-full lg:translate-x-0 lg:shadow-none',
          sidebarOpen ? 'lg:w-64' : 'lg:w-20'
        )}
      >
        <Sidebar
          collapsed={collapsed}
          onNavigate={() => setMobileOpen(false)}
          onExpand={() => setSidebarOpen(true)}
          onClose={() => setMobileOpen(false)}
        />
      </div>

      <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <Header
          onMenuToggle={() => {
            if (window.matchMedia('(min-width: 1024px)').matches) {
              toggleSidebar();
            } else {
              setMobileOpen((open) => !open);
            }
          }}
        />
        <main
          ref={mainRef}
          id="main-content"
          tabIndex={-1}
          className="relative flex-1 overflow-y-auto focus:outline-none"
        >
          <div key={location.pathname} className="mx-auto w-full max-w-[1600px] animate-fade-in p-4 sm:p-6 lg:p-8">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
