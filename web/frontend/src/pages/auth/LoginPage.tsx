import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { login as loginApi, getLoginContext } from '@/api/auth';
import { useAuthStore } from '@/stores/authStore';
import type { FiscalYearOption, BranchOption } from '@/types';
import { cn } from '@/lib/utils';

const loginSchema = z.object({
  username: z.string().min(1, 'اسم المستخدم مطلوب'),
  password: z.string().min(1, 'كلمة المرور مطلوبة'),
  fiscalYearId: z.string().min(1, 'اختر السنة المالية'),
  branchId: z.string().min(1, 'اختر الفرع'),
});

type LoginForm = z.infer<typeof loginSchema>;

const SUPPORT_PHONES = ['773988932', '779254189'];
const LAST_USERNAME_KEY = 'erp:last-username';

function readLastUsername(): string {
  try {
    return window.localStorage.getItem(LAST_USERNAME_KEY) || '';
  } catch {
    return '';
  }
}

function formatPeriodLabel(name: string | null | undefined, startDate?: string, endDate?: string): string {
  if (name) return name;
  if (startDate || endDate) {
    const start = startDate ? startDate.slice(0, 4) : '';
    const end = endDate ? endDate.slice(0, 4) : '';
    return `${start}${end ? ` - ${end}` : ''}`;
  }
  return '';
}

function extractLoginError(error: unknown): string {
  const apiError = error as {
    response?: {
      status?: number;
      data?: { message?: string; error?: string; detail?: unknown };
    };
  };
  const data = apiError.response?.data;

  if (data?.message) return data.message;
  if (data?.error) return data.error;
  if (typeof data?.detail === 'string') return data.detail;
  if (Array.isArray(data?.detail)) {
    const first = data.detail[0] as { msg?: string } | undefined;
    if (first?.msg) return first.msg;
  }
  if (apiError.response?.status === 401) return 'اسم المستخدم أو كلمة المرور غير صحيحة';
  return 'تعذر تسجيل الدخول. تحقق من الاتصال بالخادم وحاول مرة أخرى.';
}

export default function LoginPage() {
  const navigate = useNavigate();
  const authLogin = useAuthStore((s) => s.login);
  const setSessionContext = useAuthStore((s) => s.setSessionContext);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [contextLoading, setContextLoading] = useState(true);
  const [contextError, setContextError] = useState('');
  const [fiscalPeriods, setFiscalPeriods] = useState<FiscalYearOption[]>([]);
  const [branches, setBranches] = useState<BranchOption[]>([]);
  const [rememberedUsername] = useState(readLastUsername);
  const usernameRef = useRef<HTMLInputElement | null>(null);
  const passwordRef = useRef<HTMLInputElement | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: rememberedUsername,
      password: '',
      fiscalYearId: '',
      branchId: '',
    },
  });

  useEffect(() => {
    if (rememberedUsername) {
      passwordRef.current?.focus();
    } else {
      usernameRef.current?.focus();
    }
  }, [rememberedUsername]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setContextLoading(true);
      setContextError('');
      try {
        const context = await getLoginContext();
        if (cancelled) return;
        setFiscalPeriods(context.fiscalPeriods || []);
        setBranches(context.branches || []);
      } catch {
        if (!cancelled) {
          setContextError('تعذر تحميل بيانات السنة المالية والفروع. تأكد من الاتصال بالخادم.');
        }
      } finally {
        if (!cancelled) setContextLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (fiscalPeriods.length > 0 && !getValues('fiscalYearId')) {
      const today = new Date().toISOString().slice(0, 10);
      const current =
        fiscalPeriods.find((period) => {
          if (period.isLocked) return false;
          const start = period.startDate?.slice(0, 10);
          const end = period.endDate?.slice(0, 10);
          return (!start || start <= today) && (!end || end >= today);
        }) ??
        fiscalPeriods.find((period) => !period.isLocked) ??
        fiscalPeriods[0];

      if (current) {
        setValue('fiscalYearId', String(current.id), { shouldValidate: false });
      }
    }

    if (branches.length > 0 && !getValues('branchId')) {
      setValue('branchId', String(branches[0].id), { shouldValidate: false });
    }
  }, [fiscalPeriods, branches, getValues, setValue]);

  const onSubmit = async (data: LoginForm) => {
    setError('');
    setLoading(true);
    const username = data.username.trim();

    try {
      const response = await loginApi({
        username,
        password: data.password,
        fiscalYearId: Number(data.fiscalYearId),
        branchId: Number(data.branchId),
      });
      authLogin(response.user, response.accessToken, response.refreshToken);
      setSessionContext(Number(data.fiscalYearId), Number(data.branchId));
      try {
        window.localStorage.setItem(LAST_USERNAME_KEY, username);
      } catch {
        // Storage may be disabled; login should still succeed.
      }
      navigate('/dashboard');
    } catch (loginError: unknown) {
      setError(extractLoginError(loginError));
    } finally {
      setLoading(false);
    }
  };

  const usernameField = register('username');
  const passwordField = register('password');

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-bl from-primary-600 via-primary-700 to-primary-900 p-4">
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-[0.12]" />
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-white/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -left-24 h-80 w-80 rounded-full bg-emerald-300/20 blur-3xl" />

      <div className="relative w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-white shadow-xl dark:bg-zinc-900">
            <svg className="h-10 w-10 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">نظام إدارة المخازن</h1>
          <p className="mt-1 text-primary-200">ERP System</p>
        </div>

        <div className="rounded-2xl bg-white/95 p-6 shadow-2xl ring-1 ring-black/5 backdrop-blur sm:p-8 dark:bg-zinc-900/95 dark:ring-white/5">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900 dark:text-zinc-100">تسجيل الدخول</h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-zinc-400">
              أدخل بياناتك للمتابعة إلى لوحة التحكم
            </p>
          </div>

          {error && (
            <div
              role="alert"
              className="mb-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300"
            >
              <svg className="mt-0.5 h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {contextError && (
            <div
              role="alert"
              className="mb-4 flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-700 dark:border-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
            >
              <svg className="mt-0.5 h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span>{contextError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" aria-busy={loading}>
            <div>
              <label htmlFor="login-fiscal-year" className="label">
                السنة المالية
              </label>
              <select
                id="login-fiscal-year"
                {...register('fiscalYearId')}
                className={cn('select', errors.fiscalYearId && 'input-error')}
                disabled={contextLoading || fiscalPeriods.length === 0}
                aria-invalid={Boolean(errors.fiscalYearId)}
                aria-describedby={errors.fiscalYearId ? 'login-fiscal-year-error' : undefined}
              >
                <option value="">
                  {contextLoading ? 'جاري تحميل السنوات المالية...' : 'اختر السنة المالية'}
                </option>
                {fiscalPeriods.map((period) => (
                  <option key={period.id} value={period.id}>
                    {formatPeriodLabel(period.name, period.startDate, period.endDate)}
                    {period.isLocked ? ' (مقفلة)' : ''}
                  </option>
                ))}
              </select>
              {errors.fiscalYearId && (
                <p id="login-fiscal-year-error" className="mt-1 text-xs text-red-600 dark:text-red-400">
                  {errors.fiscalYearId.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="login-branch" className="label">
                الفرع
              </label>
              <select
                id="login-branch"
                {...register('branchId')}
                className={cn('select', errors.branchId && 'input-error')}
                disabled={contextLoading || branches.length === 0}
                aria-invalid={Boolean(errors.branchId)}
                aria-describedby={errors.branchId ? 'login-branch-error' : undefined}
              >
                <option value="">
                  {contextLoading ? 'جاري تحميل الفروع...' : 'اختر الفرع'}
                </option>
                {branches.map((branch) => (
                  <option key={branch.id} value={branch.id}>
                    {branch.name}
                    {branch.code ? ` (${branch.code})` : ''}
                  </option>
                ))}
              </select>
              {errors.branchId && (
                <p id="login-branch-error" className="mt-1 text-xs text-red-600 dark:text-red-400">
                  {errors.branchId.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="login-username" className="label">
                اسم المستخدم
              </label>
              <input
                id="login-username"
                {...usernameField}
                ref={(element) => {
                  usernameField.ref(element);
                  usernameRef.current = element;
                }}
                type="text"
                className={cn('input', errors.username && 'input-error')}
                placeholder="أدخل معرف الحساب"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                aria-invalid={Boolean(errors.username)}
                aria-describedby={errors.username ? 'login-username-error' : undefined}
              />
              {errors.username && (
                <p id="login-username-error" className="mt-1 text-xs text-red-600 dark:text-red-400">
                  {errors.username.message}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="login-password" className="label">
                كلمة المرور
              </label>
              <div className="relative">
                <input
                  id="login-password"
                  {...passwordField}
                  ref={(element) => {
                    passwordField.ref(element);
                    passwordRef.current = element;
                  }}
                  type={showPassword ? 'text' : 'password'}
                  className={cn('input pl-11', errors.password && 'input-error')}
                  placeholder="أدخل رمز الأمان"
                  autoComplete="current-password"
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={errors.password ? 'login-password-error' : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  aria-label={showPassword ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'}
                  className="absolute left-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-zinc-700 dark:hover:text-zinc-200"
                >
                  {showPassword ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {errors.password && (
                <p id="login-password-error" className="mt-1 text-xs text-red-600 dark:text-red-400">
                  {errors.password.message}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || contextLoading}
              className="btn-primary w-full py-3 text-base font-semibold"
            >
              {loading && (
                <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              )}
              {loading ? 'جاري الدخول...' : 'دخول'}
            </button>
          </form>

          <div className="mt-6 border-t border-gray-100 pt-5 dark:border-zinc-800">
            <p className="flex items-center gap-1.5 text-sm font-semibold text-gray-700 dark:text-zinc-300">
              <svg className="h-4 w-4 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M4.636 18.364a9 9 0 010-12.728m0 0l2.829 2.829M4.636 5.636L3 3m0 0l2.121 2.121M3 3l4.95 4.95m0 0L3 3" />
              </svg>
              الدعم الفني
            </p>
            <p className="mt-1.5 text-sm text-gray-600 dark:text-zinc-400">المهندس هشام المجمر</p>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {SUPPORT_PHONES.map((phone) => (
                <a
                  key={phone}
                  href={`tel:${phone}`}
                  dir="ltr"
                  className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm font-medium text-gray-800 transition-colors hover:border-primary-500 hover:text-primary-600 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200"
                >
                  <svg className="h-4 w-4 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                  </svg>
                  {phone}
                </a>
              ))}
            </div>
            <p className="mt-3 text-xs text-gray-500 dark:text-zinc-500">
              في حال واجهت أي مشكلة في تسجيل الدخول، تواصل مع الدعم الفني مباشرة.
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-sm text-primary-200">
          نظام إدارة المخازن المتكامل v1.0
        </p>
      </div>
    </div>
  );
}
