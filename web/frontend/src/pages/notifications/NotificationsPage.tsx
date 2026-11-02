import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/stores/authStore';
import { getNotifications, markNotificationRead, markAllNotificationsRead, deleteNotification, createNotification } from '@/api/notifications';
import type { AppNotification } from '@/types';
import { IconCheckCircle, IconTrash, IconPlus } from '@/components/ui/Icons';
import { cn, formatDate } from '@/lib/utils';

const TYPE_ICON: Record<string, string> = {
  system: '⚙️',
  low_stock: '📦',
  workflow: '🔄',
  reminder: '⏰',
};

interface BroadcastForm {
  title: string;
  message?: string;
  notification_type?: string;
  link?: string;
}

export default function NotificationsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const [showModal, setShowModal] = useState(false);
  const [showUnread, setShowUnread] = useState(false);
  const { register, handleSubmit, reset } = useForm<BroadcastForm>();

  const { data, isLoading } = useQuery({
    queryKey: ['notifications', showUnread],
    queryFn: () => getNotifications({ page: 1, pageSize: 50, unreadOnly: showUnread }),
  });
  const notifications: AppNotification[] = data?.items || [];
  const unreadCount = notifications.filter((n) => !n.isRead).length;

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['notifications'] });

  const readMutation = useMutation({
    mutationFn: (id: number) => markNotificationRead(id),
    onSuccess: invalidate,
  });

  const readAllMutation = useMutation({ mutationFn: markAllNotificationsRead, onSuccess: invalidate });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteNotification(id),
    onSuccess: invalidate,
  });

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      createNotification({
        title: String(payload.title || ''),
        message: payload.message ? String(payload.message) : undefined,
        notificationType: (payload.notification_type as string) || 'system',
        link: payload.link ? String(payload.link) : undefined,
        companyId: Number(user?.companyId || 1),
      }),
    onSuccess: () => { invalidate(); setShowModal(false); reset(); },
  });

  const openNotification = (n: AppNotification) => {
    if (!n.isRead) readMutation.mutate(n.id);
    if (n.link) navigate(n.link);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="الإشعارات"
        subtitle="مركز الإشعارات والإشعارات الجماعية"
        icon={<span className="text-2xl">🔔</span>}
        actions={
          <div className="flex gap-2">
            <button className="btn-ghost" onClick={() => setShowUnread((v) => !v)}>
              {showUnread ? 'كل الإشعارات' : `غير المقروء (${unreadCount})`}
            </button>
            <button className="btn-ghost" disabled={unreadCount === 0} onClick={() => readAllMutation.mutate()}>
              تحديد الكل كمقروء
            </button>
            <button className="btn-primary" onClick={() => { reset({ notification_type: 'system' }); setShowModal(true); }}>
              <IconPlus className="h-4 w-4 ml-1 inline" /> إشعار جديد
            </button>
          </div>
        }
      />

      {notifications.length === 0 && !isLoading ? (
        <EmptyState title="لا توجد إشعارات" description={showUnread ? 'لا توجد إشعارات غير مقروءة' : 'لا توجد إشعارات بعد'} />
      ) : (
        <div className="card divide-y divide-gray-100 dark:divide-zinc-800">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={cn(
                'flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors',
                !n.isRead && (n.isRead ? '' : 'bg-primary-500/5')
              )}
              onClick={() => openNotification(n)}
            >
              <span className="text-xl mt-0.5">{TYPE_ICON[n.notificationType] || TYPE_ICON.system}</span>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className={cn('text-sm truncate', !n.isRead ? 'font-semibold' : 'text-gray-600 dark:text-zinc-400')}>{n.title}</p>
                  {!n.isRead && <span className="h-2 w-2 rounded-full bg-primary-500 flex-shrink-0" />}
                </div>
                {!!n.message && <p className="text-xs text-gray-500 dark:text-zinc-500 mt-0.5 line-clamp-2">{n.message}</p>}
                <p className="text-xs text-gray-400 dark:text-zinc-600 mt-1">{formatDate(n.createdAt || new Date().toISOString())}</p>
              </div>
              <div className="flex items-center gap-1 flex-shrink-0">
                {!n.isRead && (
                  <button
                    className="btn-ghost p-1.5 text-emerald-600"
                    title="تعيين كمقروء"
                    onClick={(e) => { e.stopPropagation(); readMutation.mutate(n.id); }}
                  >
                    <IconCheckCircle className="h-4 w-4" />
                  </button>
                )}
                <button
                  className="btn-ghost p-1.5 text-red-600"
                  title="حذف"
                  onClick={(e) => { e.stopPropagation(); deleteMutation.mutate(n.id); }}
                >
                  <IconTrash className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="إشعار جديد">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d as unknown as Record<string, unknown>))} className="space-y-4">
          <div><label className="label">العنوان *</label><input className="input" {...register('title', { required: true })} /></div>
          <div><label className="label">الرسالة</label><textarea className="input" rows={3} {...register('message')} /></div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">النوع</label>
              <select className="input" {...register('notification_type')}>
                <option value="system">النظام</option>
                <option value="low_stock">مخزون منخفض</option>
                <option value="workflow">سير العمل</option>
                <option value="reminder">تذكير</option>
              </select>
            </div>
            <div><label className="label">الرابط (مسار)</label><input className="input" placeholder="/sales/5" {...register('link')} /></div>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setShowModal(false)}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'جارٍ الإرسال...' : 'إرسال'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}