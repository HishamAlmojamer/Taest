import type { ReactNode } from 'react';
import { formatDate } from '@/lib/utils';

export interface PrintMetaField {
  label: string;
  value: ReactNode;
}

export interface PrintCompany {
  nameAr?: string;
  name?: string;
  taxNumber?: string;
  commercialRegister?: string;
  address?: string;
  phone?: string;
  email?: string;
  website?: string;
  logo?: string;
}

interface PrintDocumentProps {
  company?: PrintCompany | null;
  title: string;
  meta?: PrintMetaField[];
  children: ReactNode;
  footer?: ReactNode;
  footerText?: string;
}

export function PrintDocument({ company, title, meta = [], children, footer, footerText }: PrintDocumentProps) {
  return (
    <div className="print-document bg-white text-gray-900 p-8 font-sans">
      {/* Header */}
      <div className="border-b-2 border-gray-800 pb-4 text-center">
        <div className="flex justify-center mb-2">
          {company?.logo ? (
            <img src={company.logo} alt="logo" className="h-20 w-20 object-contain" />
          ) : (
            <div className="h-20 w-20 rounded-full bg-primary-600 flex items-center justify-center text-white text-2xl font-bold">
              {(company?.nameAr || company?.name || 'ش').charAt(0)}
            </div>
          )}
        </div>
        <h1 className="text-2xl font-bold text-gray-900">{company?.nameAr || company?.name || 'شركتي'}</h1>
        <h2 className="text-xl font-bold text-gray-800 mt-1">{title}</h2>
        <div className="text-xs text-gray-600 mt-2 space-y-0.5">
          {(company?.taxNumber || company?.commercialRegister) && (
            <p>{company?.taxNumber ? `الرقم الضريبي: ${company.taxNumber}` : `السجل التجاري: ${company.commercialRegister}`}</p>
          )}
          {company?.address && <p>{company.address}</p>}
          <p className="flex flex-wrap gap-3 justify-center">
            {company?.phone && <span>{company.phone}</span>}
            {company?.email && <span>{company.email}</span>}
            {company?.website && <span>{company.website}</span>}
          </p>
        </div>
      </div>

      {/* Meta */}
      {meta.length > 0 && (
        <div className="grid grid-cols-2 gap-x-8 gap-y-2 my-6 text-sm">
          {meta.map((f, i) => (
            <div key={i} className="flex justify-between border-b border-gray-200 py-1.5">
              <span className="text-gray-500 font-medium ml-2">{f.label}:</span>
              <span className="text-gray-900 font-semibold text-left">{f.value}</span>
            </div>
          ))}
        </div>
      )}

      {/* Body */}
      <div>{children}</div>

      {/* Footer */}
      {(footer || footerText) && (
        <div className="mt-10 pt-4 border-t border-gray-200">
          {footerText && <p className="text-center text-sm text-gray-700">{footerText}</p>}
          {footer}
        </div>
      )}

      <p className="mt-6 text-center text-xs text-gray-400">
        تمت الطباعة في {formatDate(new Date().toISOString())}
      </p>
    </div>
  );
}
