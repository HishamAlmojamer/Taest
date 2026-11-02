import { useState, useMemo, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useToast } from '@/components/ui/Toast';
import { getAccountsTree, getAccountsFlat, getAccount, createAccount, updateAccount, deleteAccount } from '@/api/accounting';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { TreeView } from '@/components/ui/TreeView';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCurrency } from '@/lib/utils';
import { cn } from '@/lib/utils';
import ExcelExportButton from '@/components/excel/ExcelExportButton';
import ExcelImportButton from '@/components/excel/ExcelImportButton';
import type { Account, AccountCreateData } from '@/types';

const TYPE_TABS = [
  { key: 'ALL', label: 'الكل', icon: '📋' },
  { key: 'ASSET', label: 'الأصول', icon: '🏦', color: 'text-blue-600 dark:text-blue-400' },
  { key: 'LIABILITY', label: 'الخصوم', icon: '📑', color: 'text-red-600 dark:text-red-400' },
  { key: 'EQUITY', label: 'حقوق الملكية', icon: '💼', color: 'text-purple-600 dark:text-purple-400' },
  { key: 'REVENUE', label: 'الإيرادات', icon: '📈', color: 'text-emerald-600 dark:text-emerald-400' },
  { key: 'EXPENSE', label: 'المصروفات', icon: '📉', color: 'text-amber-600 dark:text-amber-400' },
] as const;

const TYPE_LABELS: Record<string, string> = {
  ASSET: 'أصول', LIABILITY: 'خصوم', EQUITY: 'حقوق ملكية', REVENUE: 'إيرادات', EXPENSE: 'مصروفات',
};

const TYPE_COLORS: Record<string, string> = {
  ASSET: 'bg-blue-500/10 text-blue-700 dark:text-blue-400',
  LIABILITY: 'bg-red-500/10 text-red-700 dark:text-red-400',
  EQUITY: 'bg-purple-500/10 text-purple-700 dark:text-purple-400',
  REVENUE: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
  EXPENSE: 'bg-amber-500/10 text-amber-700 dark:text-amber-400',
};

interface AccountFormData {
  account_code: string;
  account_name: string;
  account_name_en: string;
  account_name_ar: string;
  account_type: string;
  parent_id: number | null;
  is_control: boolean;
  opening_balance: number;
  notes: string;
}

const DEFAULT_FORM: AccountFormData = {
  account_code: '',
  account_name: '',
  account_name_en: '',
  account_name_ar: '',
  account_type: 'asset',
  parent_id: null,
  is_control: false,
  opening_balance: 0,
  notes: '',
};

export default function ChartOfAccountsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<string>('ALL');
  const [showFormModal, setShowFormModal] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | null>(null);
  const [deletingAccount, setDeletingAccount] = useState<Account | null>(null);
  const [selectedAccountId, setSelectedAccountId] = useState<number | null>(null);
  const [expandAllSignal, setExpandAllSignal] = useState(0);
  const [collapseAllSignal, setCollapseAllSignal] = useState(0);
  const [formData, setFormData] = useState<AccountFormData>(DEFAULT_FORM);

  const { data: treeData, isLoading: loadingTree } = useQuery({
    queryKey: ['accounts-tree', activeTab],
    queryFn: () => getAccountsTree(activeTab !== 'ALL' ? activeTab : undefined),
  });

  const { data: flatAccounts, isLoading: loadingFlat } = useQuery({
    queryKey: ['accounts-flat'],
    queryFn: () => getAccountsFlat(),
  });

  const { data: selectedAccount, isLoading: loadingSelected } = useQuery({
    queryKey: ['account-detail', selectedAccountId],
    queryFn: () => getAccount(selectedAccountId!),
    enabled: selectedAccountId !== null,
  });

  const errMsg = useCallback((e: any) => {
    return (typeof e?.response?.data?.detail === 'string' ? e.response.data.detail : undefined)
      || (e?.response?.data?.detail && typeof e.response.data.detail === 'object' && e.response.data.detail.message)
      || e?.message || 'حدث خطأ غير متوقع';
  }, []);

  const createMutation = useMutation({
    mutationFn: (data: AccountCreateData) => createAccount(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts-tree'] });
      queryClient.invalidateQueries({ queryKey: ['accounts-flat'] });
      setShowFormModal(false);
      setFormData(DEFAULT_FORM);
      toast.success('تم إضافة الحساب بنجاح');
    },
    onError: (e: any) => toast.error('خطأ في الإضافة: ' + errMsg(e)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<AccountCreateData> }) => updateAccount(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts-tree'] });
      queryClient.invalidateQueries({ queryKey: ['accounts-flat'] });
      queryClient.invalidateQueries({ queryKey: ['account-detail'] });
      setShowFormModal(false);
      setEditingAccount(null);
      setFormData(DEFAULT_FORM);
      toast.success('تم حفظ التعديلات بنجاح');
    },
    onError: (e: any) => toast.error('خطأ في التعديل: ' + errMsg(e)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteAccount(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['accounts-tree'] });
      queryClient.invalidateQueries({ queryKey: ['accounts-flat'] });
      setShowDeleteDialog(false);
      setDeletingAccount(null);
      setSelectedAccountId(null);
      toast.success('تم حذف الحساب بنجاح');
    },
    onError: (e: any) => toast.error('خطأ في الحذف: ' + errMsg(e)),
  });

  const descendantIds = useMemo(() => {
    const ids = new Set<number>();
    if (!editingAccount || !treeData) return ids;
    const findNode = (accounts: Account[]): Account | null => {
      for (const a of accounts) {
        if (a.id === editingAccount.id) return a;
        const sub = findNode(a.children || []);
        if (sub) return sub;
      }
      return null;
    };
    const node = findNode(treeData);
    const visit = (accounts: Account[]) =>
      accounts.forEach((a) => {
        ids.add(a.id);
        if (a.children) visit(a.children);
      });
    if (node) visit(node.children || []);
    return ids;
  }, [treeData, editingAccount]);

  const parentOptions = useMemo(() => {
    if (!flatAccounts) return [];
    return flatAccounts.filter((a: Account) =>
      a.id !== editingAccount?.id &&
      !descendantIds.has(a.id) &&
      a.type?.toLowerCase() === formData.account_type.toLowerCase(),
    );
  }, [flatAccounts, editingAccount, descendantIds, formData.account_type]);

  const openAddModal = useCallback((parentId?: number | null, parentType?: string) => {
    setEditingAccount(null);
    setFormData({
      ...DEFAULT_FORM,
      parent_id: parentId ?? null,
      account_type: parentType ? parentType.toLowerCase() : 'asset',
    });
    setShowFormModal(true);
  }, []);

  const openEditModal = useCallback((account: Account) => {
    setEditingAccount(account);
    setFormData({
      account_code: account.code,
      account_name: account.name,
      account_name_en: account.nameEn || '',
      account_name_ar: account.nameAr || '',
      account_type: account.type.toLowerCase(),
      parent_id: account.parentId ?? null,
      is_control: account.isControl || false,
      opening_balance: Number(account.openingBalance ?? 0),
      notes: account.notes || '',
    });
    setShowFormModal(true);
  }, []);

  const CODE_RE = /^[A-Za-z0-9][A-Za-z0-9._/\\-]*$/;

  const handleSubmit = useCallback(() => {
    const code = formData.account_code.trim();
    const name = formData.account_name.trim();
    if (!code) { toast.error('كود الحساب مطلوب'); return; }
    if (!name) { toast.error('اسم الحساب مطلوب'); return; }
    if (!CODE_RE.test(code)) {
      toast.error('كود الحساب قد يحتوي فقط على أرقام وحروف والرموز ., _ , / , - (بدون مسافات)');
      return;
    }
    if (formData.is_control && Number(formData.opening_balance) !== 0) {
      toast.error('حساب التحكم لا يمكن أن يحمل رصيداً افتتاحياً');
      return;
    }

    if (editingAccount) {
      updateMutation.mutate({
        id: editingAccount.id,
        data: {
          account_code: code,
          account_name: name,
          account_name_en: formData.account_name_en.trim() || undefined,
          account_name_ar: formData.account_name_ar.trim() || undefined,
          account_type: formData.account_type,
          parent_id: formData.parent_id || undefined,
          is_control: formData.is_control,
          opening_balance: Number(formData.opening_balance || 0),
          notes: formData.notes.trim() || undefined,
        },
      });
    } else {
      createMutation.mutate({
        account_code: code,
        account_name: name,
        account_name_en: formData.account_name_en.trim() || undefined,
        account_name_ar: formData.account_name_ar.trim() || undefined,
        account_type: formData.account_type,
        parent_id: formData.parent_id || undefined,
        is_control: formData.is_control,
        opening_balance: Number(formData.opening_balance || 0),
        notes: formData.notes.trim() || undefined,
      });
    }
  }, [formData, editingAccount, createMutation, updateMutation]);

  const treeNodes = useMemo(() => {
    if (!treeData) return [];
    return treeData.map((a: Account) => buildTreeNode(a, setSelectedAccountId, selectedAccountId));
  }, [treeData, selectedAccountId]);

  const totalDebit = useMemo(() => {
    if (!flatAccounts) return 0;
    return flatAccounts
      .filter((a: Account) => (a.balance ?? 0) > 0 && (a.type?.toLowerCase() === 'asset' || a.type?.toLowerCase() === 'expense'))
      .reduce((sum: number, a: Account) => sum + (a.balance ?? 0), 0);
  }, [flatAccounts]);

  const totalCredit = useMemo(() => {
    if (!flatAccounts) return 0;
    return flatAccounts
      .filter((a: Account) => (a.balance ?? 0) > 0 && (a.type?.toLowerCase() === 'liability' || a.type?.toLowerCase() === 'equity' || a.type?.toLowerCase() === 'revenue'))
      .reduce((sum: number, a: Account) => sum + (a.balance ?? 0), 0);
  }, [flatAccounts]);

  const levelMap = useMemo(() => {
    const map = new Map<number, number>();
    const visit = (accounts: Account[], depth: number) =>
      accounts.forEach((a: Account) => { map.set(a.id, depth); if (a.children) visit(a.children, depth + 1); });
    if (treeData) visit(treeData, 1);
    return map;
  }, [treeData]);

  const selectedDetails = selectedAccount as (Account & { children: Account[] }) | undefined;

  const editingHasChildren = editingAccount ? (editingAccount.children?.length ?? 0) > 0 : false;
  const typeLocked = editingHasChildren || formData.parent_id !== null;
  const balanceLocked = Boolean(formData.is_control) || editingHasChildren;

  if (loadingTree && loadingFlat) return <LoadingSpinner />;

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Main Panel */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">دليل الحسابات</h1>
            <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">
              {flatAccounts?.length ?? 0} حساب &middot; مدين: {formatCurrency(totalDebit)} &middot; دائن: {formatCurrency(totalCredit)}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <ExcelExportButton url="/excel/exports/chart-of-accounts" filename="chart-of-accounts.xlsx" label="تصدير الحسابات" className="!px-3 !py-2 !text-sm" />
            <ExcelExportButton url="/excel/templates/chart-of-accounts" filename="chart-of-accounts-template.xlsx" label="قالب الاستيراد" className="!px-3 !py-2 !text-sm" />
            <ExcelImportButton
              url="/excel/imports/chart-of-accounts"
              label="استيراد"
              className="!px-3 !py-2 !text-sm"
              onSuccess={() => {
                queryClient.invalidateQueries({ queryKey: ['accounts-tree'] });
                queryClient.invalidateQueries({ queryKey: ['accounts-flat'] });
              }}
            />
            <button
              onClick={() => openAddModal()}
              className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
              حساب جديد
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-6 py-2 border-b border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800/50 overflow-x-auto">
          {TYPE_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap',
                activeTab === tab.key
                  ? 'bg-white dark:bg-zinc-700 text-gray-900 dark:text-zinc-100 shadow-sm border border-gray-200 dark:border-zinc-600'
                  : 'text-gray-600 dark:text-zinc-400 hover:bg-white/50 dark:hover:bg-zinc-700/50 hover:text-gray-900 dark:hover:text-zinc-200'
              )}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tree Content */}
        <div className="flex-1 overflow-auto bg-white dark:bg-zinc-900 p-4">
          {loadingTree ? (
            <LoadingSpinner />
          ) : treeNodes.length === 0 ? (
            <EmptyState
              title="لا توجد حسابات"
              description="ابدأ بإضافة حسابات في الدليل المحاسبي"
              action={
                <button onClick={() => openAddModal()} className="btn-primary mt-4">
                  إضافة حساب أول
                </button>
              }
            />
          ) : (
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setExpandAllSignal((n) => n + 1)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-200 dark:border-zinc-700 text-gray-600 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
                  توسيع الكل
                </button>
                <button
                  onClick={() => setCollapseAllSignal((n) => n + 1)}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-200 dark:border-zinc-700 text-gray-600 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" /></svg>
                  طي الكل
                </button>
              </div>
              <TreeView
                nodes={treeNodes}
                searchable
                searchPlaceholder="بحث بالاسم أو الكود..."
                defaultExpanded={true}
                expandAllSignal={expandAllSignal}
                collapseAllSignal={collapseAllSignal}
                onSelect={(node) => setSelectedAccountId(node.id as number)}
              />
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selectedAccountId && (
        <div className="w-80 border-r border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 flex flex-col overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-zinc-100 text-sm">تفاصيل الحساب</h3>
            <button onClick={() => setSelectedAccountId(null)} className="text-gray-400 hover:text-gray-600 dark:hover:text-zinc-300">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>

          {loadingSelected ? (
            <div className="p-4"><LoadingSpinner /></div>
          ) : selectedDetails ? (
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {/* Account Header */}
              <div className="text-center pb-4 border-b border-gray-100 dark:border-zinc-800">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-primary-100 dark:bg-primary-500/20 mb-3">
                  <span className="text-2xl font-bold text-primary-600 dark:text-primary-400">
                    {(selectedDetails as Account).code}
                  </span>
                </div>
                <h4 className="font-semibold text-gray-900 dark:text-zinc-100">{selectedDetails.name}</h4>
                {selectedDetails.nameAr && (
                  <p className="text-sm text-gray-500 dark:text-zinc-400 mt-0.5">{selectedDetails.nameAr}</p>
                )}
                <span className={cn('inline-block mt-2 px-2.5 py-0.5 rounded-full text-xs font-medium', TYPE_COLORS[selectedDetails.type] || '')}>
                  {TYPE_LABELS[selectedDetails.type] || selectedDetails.type}
                </span>
              </div>

              {/* Balance */}
              <div className="bg-gray-50 dark:bg-zinc-800 rounded-lg p-3">
                <p className="text-xs text-gray-500 dark:text-zinc-400 mb-1">الرصيد الحالي</p>
                <p className={cn(
                  'text-xl font-bold',
                  (selectedDetails.balance ?? 0) >= 0
                    ? 'text-gray-900 dark:text-zinc-100'
                    : 'text-red-600 dark:text-red-400'
                )}>
                  {formatCurrency(selectedDetails.balance ?? 0)}
                </p>
              </div>

              {/* Cumulative balance for control accounts */}
              {(selectedDetails.isControl || (selectedDetails.children?.length ?? 0) > 0) && (
                <div className="bg-primary-50 dark:bg-primary-500/10 rounded-lg p-3">
                  <p className="text-xs text-primary-600 dark:text-primary-400 mb-1 flex items-center gap-1">
                    الرصيد المتراكم (شامل الحسابات الفرعية)
                  </p>
                  <p className={cn(
                    'text-xl font-bold',
                    (selectedDetails.cumulativeBalance ?? 0) >= 0
                      ? 'text-gray-900 dark:text-zinc-100'
                      : 'text-red-600 dark:text-red-400'
                  )}>
                    {formatCurrency(selectedDetails.cumulativeBalance ?? 0)}
                  </p>
                </div>
              )}

              {/* Info */}
              <div className="space-y-3 text-sm">
                <InfoRow label="الكود" value={selectedDetails.code} />
                <InfoRow label="الاسم بالإنجليزية" value={selectedDetails.nameEn || '-'} />
                {selectedDetails.parentId && (
                  <InfoRow label="الحساب الأب" value={`${parentOptions.find((p: Account) => p.id === selectedDetails.parentId)?.code || ''} - ${parentOptions.find((p: Account) => p.id === selectedDetails.parentId)?.name || ''}`} />
                )}
                <InfoRow label="المستوى" value={`L${levelMap.get(selectedDetails.id) ?? '-'}`} />
                <InfoRow label="حساب تحكم" value={selectedDetails.isControl ? 'نعم (ترحيله محظور)' : 'لا (يمكن الترحيل عليه)'} />
                <InfoRow label="الحالة" value={selectedDetails.isActive !== false ? 'نشط' : 'غير نشط'} />
                {selectedDetails.children && selectedDetails.children.length > 0 && (
                  <InfoRow label="عدد الحسابات الفرعية" value={`${selectedDetails.children.length}`} />
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <button
                  onClick={() => openAddModal(selectedDetails.id, selectedDetails.type)}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400 rounded-lg text-sm font-medium hover:bg-primary-100 dark:hover:bg-primary-500/20 transition-colors"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                  حساب فرعي
                </button>
                <button
                  onClick={() => openEditModal(selectedDetails as Account)}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-300 rounded-lg text-sm font-medium hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                  تعديل
                </button>
                <button
                  onClick={() => { setDeletingAccount(selectedDetails as Account); setShowDeleteDialog(true); }}
                  className="flex items-center justify-center px-3 py-2 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 rounded-lg text-sm font-medium hover:bg-red-100 dark:hover:bg-red-500/20 transition-colors"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>

              {/* Children List */}
              {selectedDetails.children && selectedDetails.children.length > 0 && (
                <div className="pt-2">
                  <p className="text-xs font-medium text-gray-500 dark:text-zinc-400 mb-2">الحسابات الفرعية</p>
                  <div className="space-y-1">
                    {selectedDetails.children.map((child: Account) => (
                      <button
                        key={child.id}
                        onClick={() => setSelectedAccountId(child.id)}
                        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-zinc-800 rounded-lg text-sm hover:bg-gray-100 dark:hover:bg-zinc-700 transition-colors text-right"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="text-xs text-gray-400 dark:text-zinc-500 font-mono">{child.code}</span>
                          <span className="text-gray-700 dark:text-zinc-300 truncate">{child.name}</span>
                        </div>
                        <span className="text-xs text-gray-500 dark:text-zinc-400 whitespace-nowrap mr-2">
                          {formatCurrency(child.balance ?? 0)}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* Add/Edit Modal */}
      <Modal
        isOpen={showFormModal}
        onClose={() => { setShowFormModal(false); setEditingAccount(null); setFormData(DEFAULT_FORM); }}
        title={editingAccount ? `تعديل: ${editingAccount.name}` : 'حساب جديد'}
        size="lg"
      >
        <div className="space-y-4">
          {/* Row 1: Code + Type */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">كود الحساب *</label>
              <input
                type="text"
                value={formData.account_code}
                onChange={(e) => setFormData(prev => ({ ...prev, account_code: e.target.value }))}
                placeholder="مثال: 1101"
                className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">نوع الحساب *</label>
              <select
                value={formData.account_type}
                onChange={(e) => setFormData(prev => ({ ...prev, account_type: e.target.value }))}
                disabled={typeLocked}
                className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="asset">أصول</option>
                <option value="liability">خصوم</option>
                <option value="equity">حقوق ملكية</option>
                <option value="revenue">إيرادات</option>
                <option value="expense">مصروفات</option>
              </select>
              {typeLocked && (
                <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                  {formData.parent_id
                    ? 'نوع الحساب يتبع نوع الحساب الأب ولا يمكن تغييره'
                    : 'لا يمكن تغيير نوع حساب له حسابات فرعية'}
                </p>
              )}
            </div>
          </div>

          {/* Row 2: Name Ar */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">اسم الحساب (عربي) *</label>
            <input
              type="text"
              value={formData.account_name}
              onChange={(e) => setFormData(prev => ({ ...prev, account_name: e.target.value }))}
              placeholder="مثال: النقد في البنك"
              className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
            />
          </div>

          {/* Row 3: Name En + Name Ar Alt */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">الاسم بالإنجليزية</label>
              <input
                type="text"
                value={formData.account_name_en}
                onChange={(e) => setFormData(prev => ({ ...prev, account_name_en: e.target.value }))}
                placeholder="Cash at Bank"
                className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
                dir="ltr"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">الاسم البديل (عربي)</label>
              <input
                type="text"
                value={formData.account_name_ar}
                onChange={(e) => setFormData(prev => ({ ...prev, account_name_ar: e.target.value }))}
                placeholder="اختياري"
                className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              />
            </div>
          </div>

          {/* Row 4: Parent Account */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">الحساب الأب</label>
            <select
              value={formData.parent_id ?? ''}
              onChange={(e) => {
                const pid = e.target.value ? Number(e.target.value) : null;
                const parent = pid ? flatAccounts?.find((a: Account) => a.id === pid) : null;
                setFormData(prev => ({
                  ...prev,
                  parent_id: pid,
                  account_type: parent ? parent.type.toLowerCase() : prev.account_type,
                }));
              }}
              className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
            >
              <option value="">— حساب رئيسي (بدون أب) —</option>
              {parentOptions.map((a: Account) => (
                <option key={a.id} value={a.id}>
                  {a.code} - {a.name}
                </option>
              ))}
            </select>
            {formData.parent_id && (
              <p className="mt-1 text-xs text-gray-500 dark:text-zinc-400">
                سيُعطى الحساب نفس نوع الحساب الأب تلقائياً ({TYPE_LABELS[formData.account_type.toUpperCase()] || formData.account_type})
              </p>
            )}
          </div>

          {/* Row 5: Opening Balance + Is Control */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">الرصيد الافتتاحي</label>
              <input
                type="number"
                value={formData.opening_balance}
                onChange={(e) => setFormData(prev => ({ ...prev, opening_balance: Number(e.target.value) }))}
                disabled={balanceLocked}
                className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none disabled:opacity-50 disabled:cursor-not-allowed"
                dir="ltr"
              />
              {balanceLocked && (
                <p className="mt-1 text-xs text-amber-600 dark:text-amber-400">
                  {formData.is_control ? 'حساب التحكم لا يحمل رصيداً افتتاحياً'
                    : 'الحسابات الفرعية لا تحمل رصيداً افتتاحياً'}
                </p>
              )}
            </div>
            <div className="flex items-end pb-1">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_control}
                  onChange={(e) => {
                    const checked = e.target.checked;
                    setFormData(prev => ({
                      ...prev,
                      is_control: checked,
                      opening_balance: checked ? 0 : prev.opening_balance,
                    }));
                  }}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-zinc-300">حساب تحكم (لا يُسجل عليه)</span>
              </label>
            </div>
          </div>

          {/* Row 6: Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">ملاحظات</label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-zinc-700">
            <button
              type="button"
              onClick={() => { setShowFormModal(false); setEditingAccount(null); setFormData(DEFAULT_FORM); }}
              className="px-4 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800 text-sm font-medium transition-colors"
            >
              إلغاء
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={!formData.account_code || !formData.account_name || createMutation.isPending || updateMutation.isPending}
              className="px-5 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              {createMutation.isPending || updateMutation.isPending
                ? 'جاري الحفظ...'
                : editingAccount ? 'حفظ التعديلات' : 'إضافة الحساب'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => { setShowDeleteDialog(false); setDeletingAccount(null); }}
        onConfirm={() => deletingAccount && deleteMutation.mutate(deletingAccount.id)}
        title="حذف الحساب"
        message={`هل أنت متأكد من حذف الحساب "${deletingAccount?.name}" (${deletingAccount?.code})؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

function buildTreeNode(
  account: Account,
  setSelectedId: (id: number | null) => void,
  selectedId: number | null,
  level: number = 1,
): any {
  const hasChildren = account.children && account.children.length > 0;
  const isControl = account.isControl || hasChildren;
  const shownBalance = isControl ? (account.cumulativeBalance ?? account.balance ?? 0) : (account.balance ?? 0);

  return {
    id: account.id,
    code: account.code,
    label: account.name,
    meta: (
      <div className="flex items-center gap-2" dir="ltr">
        <span className={cn(
          'text-xs px-1.5 py-0.5 rounded',
          TYPE_COLORS[account.type] || 'bg-gray-100 dark:bg-zinc-800',
        )}>
          {TYPE_LABELS[account.type] || account.type}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-zinc-400 font-bold">
          L{level}
        </span>
        {isControl ? (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-violet-500/10 text-violet-600 dark:text-violet-400 font-semibold">
            تحكم
          </span>
        ) : (
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold">
            ترحيل
          </span>
        )}
        <span className={cn(
          'text-xs font-mono',
          shownBalance >= 0 ? 'text-gray-600 dark:text-zinc-400' : 'text-red-600 dark:text-red-400',
        )}>
          {formatCurrency(shownBalance)}
        </span>
      </div>
    ),
    children: account.children?.map((child: Account) => buildTreeNode(child, setSelectedId, selectedId, level + 1)),
  };
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-gray-500 dark:text-zinc-400">{label}</span>
      <span className="text-gray-900 dark:text-zinc-100 font-medium text-left">{value}</span>
    </div>
  );
}
