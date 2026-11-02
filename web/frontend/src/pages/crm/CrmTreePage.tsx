import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/ui/PageHeader';
import { TreeView } from '@/components/ui/TreeView';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useForm } from 'react-hook-form';
import {
  getCustomersTree, getSuppliersTree, createCustomer, createSupplier,
  updateCustomer, updateSupplier, deleteCustomer, deleteSupplier,
  type CustomerTreeNode, type SupplierTreeNode,
} from '@/api/crm';
import { formatCurrency, cn } from '@/lib/utils';
import { IconUsers, IconBuilding, IconPlus, IconRefresh } from '@/components/ui/Icons';

interface TreeItem {
  id: number;
  name: string;
  code?: string;
  nameAr?: string;
  city?: string;
  phone?: string;
  email?: string;
  balance?: number;
  parentId?: number;
  customerType?: string;
  contactPerson?: string;
  segmentName?: string;
  children?: TreeItem[];
}

interface TreeViewNode {
  id: number | string;
  label: string;
  code?: string;
  meta?: ReactNode;
  children?: TreeViewNode[];
}

const flatten = (items: TreeItem[]): TreeItem[] =>
  items.flatMap((n) => [n, ...(n.children ? flatten(n.children) : [])]);

const collectDescendants = (item: TreeItem | undefined): Set<number> => {
  const set = new Set<number>();
  if (!item) return set;
  const walk = (children: TreeItem[] | undefined) => {
    (children || []).forEach((c) => {
      set.add(c.id);
      walk(c.children);
    });
  };
  walk(item.children);
  return set;
};

const findById = (items: TreeItem[], id: number): TreeItem | undefined => {
  for (const n of items) {
    if (n.id === id) return n;
    const found = n.children ? findById(n.children, id) : undefined;
    if (found) return found;
  }
  return undefined;
};

export default function CrmTreePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'customers' | 'suppliers'>('customers');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [showAdd, setShowAdd] = useState(false);
  const [showParent, setShowParent] = useState(false);
  const [parentValue, setParentValue] = useState<string>('');
  const [deleting, setDeleting] = useState<TreeItem | null>(null);

  const { register, handleSubmit, reset } = useForm();

  const isCustomers = tab === 'customers';

  const { data: custTree, isLoading: loadingCustomers } = useQuery({
    queryKey: ['crm-customers-tree'],
    queryFn: () => getCustomersTree(),
  });
  const { data: suppTree, isLoading: loadingSuppliers } = useQuery({
    queryKey: ['crm-suppliers-tree'],
    queryFn: () => getSuppliersTree(),
  });

  const customers: TreeItem[] = (custTree?.items || []) as unknown as TreeItem[];
  const suppliers: TreeItem[] = (suppTree?.items || []) as unknown as TreeItem[];

  const allCustomers = useMemo(() => flatten(customers), [customers]);
  const allSuppliers = useMemo(() => flatten(suppliers), [suppliers]);
  const allNodes = isCustomers ? allCustomers : allSuppliers;

  const selected: TreeItem | null = selectedId != null ? findById(allNodes, selectedId) || null : null;
  const parentName = selected?.parentId != null ? findById(allNodes, selected.parentId)?.name : null;
  const descendants = useMemo(
    () => collectDescendants(selectedId != null ? findById(allNodes, selectedId) : undefined),
    [allNodes, selectedId]
  );
  const parentOptions = allNodes.filter((n) => n.id !== selectedId && !descendants.has(n.id));

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['crm-customers-tree'] });
    queryClient.invalidateQueries({ queryKey: ['crm-suppliers-tree'] });
    queryClient.invalidateQueries({ queryKey: ['customers'] });
    queryClient.invalidateQueries({ queryKey: ['suppliers'] });
  };

  const addMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      isCustomers ? createCustomer(payload) : createSupplier(payload),
    onSuccess: () => {
      invalidate();
      setShowAdd(false);
      reset();
    },
  });

  const parentMutation = useMutation({
    mutationFn: (parentId: number | null) =>
      isCustomers
        ? updateCustomer(selectedId as number, { parentId })
        : updateSupplier(selectedId as number, { parentId }),
    onSuccess: () => {
      invalidate();
      setShowParent(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => (isCustomers ? deleteCustomer(id) : deleteSupplier(id)),
    onSuccess: () => {
      invalidate();
      setDeleting(null);
      setSelectedId(null);
    },
  });

  const toNode = (n: TreeItem): TreeViewNode => ({
    id: n.id,
    label: n.name,
    code: n.code || undefined,
    meta: formatCurrency(n.balance ?? 0),
    children: n.children?.length ? n.children.map(toNode) : undefined,
  });
  const treeNodes = (isCustomers ? customers : suppliers).map(toNode);

  const openAdd = () => {
    reset({
      name: '',
      name_ar: '',
      code: '',
      phone: '',
      city: '',
      customer_type: 'customer',
      contact_person: '',
      notes: '',
    });
    setShowAdd(true);
  };

  const openParent = () => {
    setParentValue(selected?.parentId != null ? String(selected.parentId) : '');
    setShowParent(true);
  };

  const mutationError = addMutation.error || parentMutation.error || deleteMutation.error;

  return (
    <div className="space-y-6">
      <PageHeader
        title="شجرة العملاء والموردين"
        subtitle="عرض وتنظيم العملاء والموردين بعلاقة أب-ابن"
        icon={isCustomers ? <IconUsers className="h-6 w-6" /> : <IconBuilding className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openAdd} disabled={!selected}>
            <span className="ml-2 flex items-center gap-1"><IconPlus className="h-4 w-4" /></span>
            إضافة فرع
          </button>
        }
      />

      <div className="flex items-center gap-2">
        {(['customers', 'suppliers'] as const).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setSelectedId(null); }}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              tab === t
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-300 hover:bg-gray-200 dark:hover:bg-zinc-700'
            )}
          >
            {t === 'customers' ? 'العملاء' : 'الموردون'}
          </button>
        ))}
        {(loadingCustomers || loadingSuppliers) && <IconRefresh className="h-4 w-4 animate-spin text-gray-400" />}
      </div>

      {mutationError && (
        <div className="rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950 px-4 py-3 text-sm text-red-700 dark:text-red-300">
          {(mutationError as Error).message || 'حدث خطأ أثناء تنفيذ العملية'}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          {isCustomers ? (
            loadingCustomers ? (
              <LoadingSpinner />
            ) : (
              <TreeView
                nodes={treeNodes}
                searchable
                searchPlaceholder="بحث عن عميل..."
                defaultExpanded
                onSelect={(node) => setSelectedId(Number(node.id))}
              />
            )
          ) : loadingSuppliers ? (
            <LoadingSpinner />
          ) : (
            <TreeView
              nodes={treeNodes}
              searchable
              searchPlaceholder="بحث عن مورد..."
              defaultExpanded
              onSelect={(node) => setSelectedId(Number(node.id))}
            />
          )}
        </div>

        <div className="lg:col-span-3">
          {!selected ? (
            <div className="card p-10 text-center text-gray-500 dark:text-zinc-400">
              <p className="text-lg mb-2">اختر عنصراً من الشجرة</p>
              <p className="text-sm">
                اضغط على أي عميل أو مورد لعرض تفاصيله، أو استخدم «إضافة فرع» لإنشاء عنصر فرعي تحت العنصر المحدد.
              </p>
            </div>
          ) : (
            <div className="card p-6 space-y-5">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 dark:text-zinc-100 flex items-center gap-2">
                    {selected.name}
                    {selected.code && (
                      <span className="font-mono text-xs text-gray-500 dark:text-zinc-400 bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded">{selected.code}</span>
                    )}
                  </h2>
                  {selected.nameAr && <p className="text-sm text-gray-500 dark:text-zinc-400">{selected.nameAr}</p>}
                </div>
                <div className="flex gap-2">
                  {isCustomers && (
                    <button className="btn-ghost text-sm" onClick={() => navigate(`/crm/customers/${selected.id}`)}>
                      فتح الملف
                    </button>
                  )}
                  <button className="btn-ghost text-sm" onClick={openParent}>تغيير الأصل</button>
                  <button className="btn-ghost text-sm text-red-600" onClick={() => setDeleting(selected)}>
                    حذف
                  </button>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <div>
                  <p className="label">الحالة</p>
                  <span className={cn('text-sm font-medium', selected.parentId ? '' : 'text-primary-600')}>
                    {selected.parentId ? 'فرع' : 'جذر (عنصر رئيسي)'}
                  </span>
                </div>
                {selected.parentId != null && (
                  <div>
                    <p className="label">الأصل</p>
                    <p className="text-sm font-medium">{parentName || `#${selected.parentId}`}</p>
                  </div>
                )}
                <div>
                  <p className="label">عدد الأفرع المباشرة</p>
                  <p className="text-sm font-medium">{(selected.children || []).length}</p>
                </div>
                <div>
                  <p className="label">{isCustomers ? 'نوع العميل' : 'مسؤول الاتصال'}</p>
                  <p className="text-sm font-medium">{isCustomers ? (selected.customerType || '-') : (selected.contactPerson || '-')}</p>
                </div>
                <div>
                  <p className="label">الشريحة</p>
                  <p className="text-sm font-medium">{selected.segmentName || '-'}</p>
                </div>
                <div>
                  <p className="label">الرصيد</p>
                  <p className="text-sm font-medium">{formatCurrency(selected.balance ?? 0)}</p>
                </div>
                <div>
                  <p className="label">المدينة</p>
                  <p className="text-sm font-medium">{selected.city || '-'}</p>
                </div>
                <div>
                  <p className="label">الهاتف</p>
                  <p className="text-sm font-medium" dir="ltr">{selected.phone || '-'}</p>
                </div>
                <div>
                  <p className="label">البريد</p>
                  <p className="text-sm font-medium" dir="ltr">{selected.email || '-'}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <Modal isOpen={showAdd} onClose={() => setShowAdd(false)} title={isCustomers ? 'إضافة عميل فرعي' : 'إضافة مورد فرعي'} size="md">
        <form onSubmit={handleSubmit((d) => {
          const payload: Record<string, unknown> = {
            name: d.name,
            nameAr: d.name_ar,
            code: d.code,
            phone: d.phone,
            city: d.city,
            notes: d.notes,
            parentId: selectedId,
          };
          if (isCustomers) payload.customerType = d.customer_type;
          else payload.contactPerson = d.contact_person;
          addMutation.mutate(payload);
        })} className="space-y-4">
          <div>
            <label className="label">الأصل</label>
            <input className="input" value={selected?.name || ''} disabled />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label">الاسم *</label>
              <input className="input" {...register('name', { required: true })} />
            </div>
            <div>
              <label className="label">الاسم بالعربية</label>
              <input className="input" {...register('name_ar')} />
            </div>
            <div>
              <label className="label">الكود</label>
              <input className="input" {...register('code')} />
            </div>
            <div>
              <label className="label">الهاتف</label>
              <input className="input" {...register('phone')} />
            </div>
            <div>
              <label className="label">المدينة</label>
              <input className="input" {...register('city')} />
            </div>
            {isCustomers ? (
              <div>
                <label className="label">نوع العميل</label>
                <select className="input" {...register('customer_type')}>
                  <option value="customer">عميل نقدي</option>
                  <option value="company">شركة</option>
                  <option value="wholesale">جملة</option>
                  <option value="retail">تجزئة</option>
                </select>
              </div>
            ) : (
              <div>
                <label className="label">مسؤول الاتصال</label>
                <input className="input" {...register('contact_person')} />
              </div>
            )}
          </div>
          <div>
            <label className="label">ملاحظات</label>
            <textarea className="input" rows={2} {...register('notes')} />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setShowAdd(false)}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={addMutation.isPending}>
              {addMutation.isPending ? 'جارٍ الحفظ...' : 'إضافة'}
            </button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={showParent} onClose={() => setShowParent(false)} title="تغيير الأصل" size="sm">
        <div className="space-y-4">
          <div>
            <label className="label">العنصر الحالي</label>
            <input className="input" value={selected?.name || ''} disabled />
          </div>
          <div>
            <label className="label">الأصل الجديد</label>
            <select className="input" value={parentValue} onChange={(e) => setParentValue(e.target.value)}>
              <option value="">بدون (جذر)</option>
              {parentOptions.map((n) => (
                <option key={n.id} value={n.id}>{n.code ? `${n.code} - ` : ''}{n.name}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setShowParent(false)}>إلغاء</button>
            <button
              className="btn-primary"
              disabled={parentMutation.isPending}
              onClick={() => parentMutation.mutate(parentValue === '' ? null : Number(parentValue))}
            >
              {parentMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title={isCustomers ? 'حذف العميل' : 'حذف المورد'}
        message={`هل أنت متأكد من حذف "${deleting?.name}"؟ لا يمكن حذف عنصر لديه أفرع أو فواتير مرتبطة.`}
        confirmText="حذف"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
