import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { getProducts } from '@/api/inventory';
import { getCustomers } from '@/api/crm';
import { getTaxRates } from '@/api/taxes';
import { createSale } from '@/api/sales';
import { useAuthStore } from '@/stores/authStore';
import { useCompany } from '@/hooks/useCompany';
import { useGeneralSettings } from '@/hooks/useGeneralSettings';
import { formatCurrency, formatDate } from '@/lib/utils';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { cn } from '@/lib/utils';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

interface CartLine {
  productId: number;
  productName: string;
  price: number;
  qty: number;
}

export default function PosPage() {
  const navigate = useNavigate();
  const company = useCompany();
  const settings = useGeneralSettings();
  const { branchId, fiscalYearId, user } = useAuthStore();
  const toast = useToast();

  const [search, setSearch] = useState('');
  const [customerId, setCustomerId] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [cart, setCart] = useState<CartLine[]>([]);
  const [receipt, setReceipt] = useState<any>(null);

  const { data: productsData } = useQuery({
    queryKey: ['products-pos'],
    queryFn: () => getProducts({ page: 1, pageSize: 1000 }),
  });

  const { data: customersData } = useQuery({
    queryKey: ['customers-select'],
    queryFn: () => getCustomers({ page: 1, pageSize: 1000 }),
  });

  const { data: taxRates } = useQuery({
    queryKey: ['tax-rates'],
    queryFn: () => getTaxRates(),
  });

  const activeTax = (taxRates || []).find((t: any) => t.isActive && t.rate > 0);
  const taxRatePercent = activeTax ? Number(activeTax.rate) : 15;

  const products = useMemo(
    () =>
      (productsData?.items || []).filter((p: any) =>
        search ? String(p.name || '').toLowerCase().includes(search.toLowerCase()) || String(p.code || '').toLowerCase().includes(search.toLowerCase()) : true
      ),
    [productsData, search]
  );

  const addToCart = (p: any) => {
    setCart((prev) => {
      const existing = prev.find((l) => l.productId === Number(p.id));
      if (existing) {
        return prev.map((l) => (l.productId === existing.productId ? { ...l, qty: l.qty + 1 } : l));
      }
      return [...prev, { productId: Number(p.id), productName: p.name || `#${p.id}`, price: Number(p.sellingPrice || 0), qty: 1 }];
    });
  };

  const setQty = (productId: number, qty: number) => {
    setCart((prev) => (qty <= 0 ? prev.filter((l) => l.productId !== productId) : prev.map((l) => (l.productId === productId ? { ...l, qty } : l))));
  };

  const removeLine = (productId: number) => setCart((prev) => prev.filter((l) => l.productId !== productId));

  const subtotal = cart.reduce((s, l) => s + l.price * l.qty, 0);
  const taxAmount = subtotal * (taxRatePercent / 100);
  const total = subtotal + taxAmount;

  const checkoutMutation = useMutation({
    mutationFn: createSale,
    onSuccess: (sale: any) => {
      toast.success('تم إتمام البيع بنجاح');
      setReceipt(sale);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const checkout = () => {
    if (cart.length === 0) return;
    checkoutMutation.mutate({
      customerId: customerId ? Number(customerId) : null,
      totalAmount: subtotal,
      discount: 0,
      finalAmount: total,
      paymentMethod,
      paymentStatus: paymentMethod === 'credit' ? 'unpaid' : 'paid',
      companyId: Number(user?.companyId || 1),
      branchId: branchId ?? 1,
      fiscalPeriodId: fiscalYearId,
      taxAmount,
      taxId: activeTax ? activeTax.id : undefined,
      items: cart.map((l) => ({ productId: l.productId, quantity: l.qty, unitPrice: l.price, totalPrice: l.price * l.qty })),
    } as never);
  };

  const customerName = (customersData?.items || []).find((c: any) => String(c.id) === String(customerId))?.name || 'عميل نقدي';

  return (
    <div className="space-y-6">
      <PageHeader
        title="نقطة البيع (POS)"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 100 4 2 2 0 000-4z" /></svg>}
        actions={<button onClick={() => navigate('/sales')} className="btn-secondary">رجوع</button>}
      />

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Products */}
        <div className="lg:col-span-3 card space-y-4">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث باسم المنتج أو الكود..."
            className="input"
            autoFocus
          />
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[60vh] overflow-y-auto">
            {products.map((p: any) => (
              <button
                key={p.id}
                onClick={() => addToCart(p)}
                disabled={Number(p.currentStock) <= 0}
                className={cn(
                  'rounded-xl border border-gray-200 dark:border-zinc-700 p-3 text-right hover:border-primary-500 hover:shadow-md transition-all',
                  Number(p.currentStock) <= 0 && 'opacity-40 cursor-not-allowed'
                )}
              >
                <p className="text-sm font-semibold line-clamp-1">{p.name}</p>
                <p className="text-xs text-gray-500 dark:text-zinc-400 mt-1">{p.code || ''}</p>
                <p className="text-primary-600 font-bold mt-2">{formatCurrency(Number(p.sellingPrice || 0))}</p>
                <p className={cn('text-xs mt-1', Number(p.currentStock) <= 5 ? 'text-red-500' : 'text-gray-400')}>
                  المخزون: {p.currentStock ?? 0}
                </p>
              </button>
            ))}
            {products.length === 0 && <p className="col-span-full text-center text-sm text-gray-400 py-8">لا توجد منتجات</p>}
          </div>
        </div>

        {/* Cart */}
        <div className="lg:col-span-2 card space-y-4">
          <h3 className="text-lg font-semibold">السلة</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="label">العميل</label>
              <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} className="input text-sm">
                <option value="">عميل نقدي</option>
                {(customersData?.items || []).map((c: any) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">طريقة الدفع</label>
              <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)} className="input text-sm">
                <option value="cash">نقدي</option>
                <option value="card">بطاقة</option>
                <option value="bank_transfer">تحويل بنكي</option>
                <option value="check">شيك</option>
                <option value="credit">آجل</option>
              </select>
            </div>
          </div>

          <div className="max-h-[40vh] overflow-y-auto divide-y divide-gray-100 dark:divide-zinc-800">
            {cart.map((line) => (
              <div key={line.productId} className="flex items-center gap-2 py-2">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{line.productName}</p>
                  <p className="text-xs text-gray-500 dark:text-zinc-400">{formatCurrency(line.price)}</p>
                </div>
                <div className="flex items-center gap-1">
                  <button onClick={() => setQty(line.productId, line.qty - 1)} className="h-7 w-7 rounded bg-gray-100 dark:bg-zinc-800 text-sm font-bold">−</button>
                  <input
                    type="number"
                    value={line.qty}
                    min={1}
                    onChange={(e) => setQty(line.productId, Number(e.target.value))}
                    className="input text-sm w-14 text-center"
                  />
                  <button onClick={() => setQty(line.productId, line.qty + 1)} className="h-7 w-7 rounded bg-gray-100 dark:bg-zinc-800 text-sm font-bold">+</button>
                </div>
                <span className="text-sm font-semibold w-20 text-left">{formatCurrency(line.price * line.qty)}</span>
                <button onClick={() => removeLine(line.productId)} className="text-red-500 hover:text-red-700 text-sm">✕</button>
              </div>
            ))}
            {cart.length === 0 && <p className="text-center text-sm text-gray-400 py-8">السلة فارغة</p>}
          </div>

          <div className="space-y-2 border-t border-gray-200 dark:border-zinc-700 pt-3">
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع</span><span>{formatCurrency(subtotal)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة ({taxRatePercent}%)</span><span>{formatCurrency(taxAmount)}</span></div>
            <div className="flex justify-between text-lg font-bold"><span>الإجمالي</span><span className="text-primary-600">{formatCurrency(total)}</span></div>
          </div>

          <button
            onClick={checkout}
            disabled={cart.length === 0 || checkoutMutation.isPending}
            className="btn-primary w-full py-3 text-base disabled:opacity-50"
          >
            {checkoutMutation.isPending ? 'جاري إتمام البيع...' : `إتمام البيع — ${formatCurrency(total)}`}
          </button>
        </div>
      </div>

      <PrintPreviewModal
        isOpen={!!receipt}
        onClose={() => {
          setReceipt(null);
          setCart([]);
        }}
        title={`إيصال ${receipt?.invoiceNumber || ''}`}
        filename={`إيصال-${receipt?.invoiceNumber || 'pos'}`}
      >
        <PrintDocument
          company={company}
          title="إيصال بيع"
          footerText={settings.receipt_footer}
          meta={[
            { label: 'رقم الإيصال', value: receipt?.invoiceNumber || '-' },
            { label: 'التاريخ', value: formatDate(receipt?.date || receipt?.createdAt || new Date().toISOString()) },
            { label: 'العميل', value: customerName },
            { label: 'طريقة الدفع', value: paymentMethod },
          ]}
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700">
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">#</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المنتج</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الكمية</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">السعر</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الإجمالي</th>
              </tr>
            </thead>
            <tbody>
              {(receipt?.items || cart).map((line: any, idx: number) => (
                <tr key={idx}>
                  <td className="px-3 py-2 border border-gray-300">{idx + 1}</td>
                  <td className="px-3 py-2 border border-gray-300">{line.productName || '-'}</td>
                  <td className="px-3 py-2 border border-gray-300">{line.quantity}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(line.unitPrice || line.price || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300 font-medium">{formatCurrency((line.unitPrice || line.price || 0) * line.quantity)}</td>
                </tr>
              ))}
              <tr className="bg-gray-50 font-semibold">
                <td className="px-3 py-2 border border-gray-300" colSpan={4}>المجموع الفرعي</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(receipt?.totalAmount ?? subtotal)}</td>
              </tr>
              <tr>
                <td className="px-3 py-2 border border-gray-300" colSpan={4}>الضريبة</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(receipt?.taxAmount ?? taxAmount)}</td>
              </tr>
              <tr className="bg-gray-100 font-bold">
                <td className="px-3 py-2 border border-gray-300" colSpan={4}>الإجمالي</td>
                <td className="px-3 py-2 border border-gray-300 text-primary-600">{formatCurrency(receipt?.finalAmount ?? total)}</td>
              </tr>
            </tbody>
          </table>
          <div className="mt-10 grid grid-cols-2 gap-8 text-center text-sm text-gray-700">
            <div><p className="border-t border-gray-400 pt-2 font-medium">توقيع العميل</p></div>
            <div><p className="border-t border-gray-400 pt-2 font-medium">ختم الشركة</p></div>
          </div>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
