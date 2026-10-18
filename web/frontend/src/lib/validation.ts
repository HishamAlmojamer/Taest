// Common validation utilities for forms

export const validators = {
  required: (value: any, fieldName: string): string | null => {
    if (value === null || value === undefined || value === '') {
      return `${fieldName} مطلوب`;
    }
    return null;
  },

  email: (value: string, fieldName: string = 'البريد الإلكتروني'): string | null => {
    if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      return `${fieldName} غير صحيح`;
    }
    return null;
  },

  phone: (value: string, fieldName: string = 'رقم الهاتف'): string | null => {
    if (value && !/^[\d\s\-\+\(\)]{10,20}$/.test(value)) {
      return `${fieldName} غير صحيح`;
    }
    return null;
  },

  minLength: (value: string, min: number, fieldName: string): string | null => {
    if (value && value.length < min) {
      return `${fieldName} يجب أن يكون ${min} أحرف على الأقل`;
    }
    return null;
  },

  maxLength: (value: string, max: number, fieldName: string): string | null => {
    if (value && value.length > max) {
      return `${fieldName} يجب أن يكون ${max} حرف كحد أقصى`;
    }
    return null;
  },

  min: (value: number, min: number, fieldName: string): string | null => {
    if (value !== null && value !== undefined && value < min) {
      return `${fieldName} يجب أن يكون ${min} على الأقل`;
    }
    return null;
  },

  max: (value: number, max: number, fieldName: string): string | null => {
    if (value !== null && value !== undefined && value > max) {
      return `${fieldName} يجب أن يكون ${max} كحد أقصى`;
    }
    return null;
  },

  positiveNumber: (value: number, fieldName: string): string | null => {
    if (value !== null && value !== undefined && value < 0) {
      return `${fieldName} يجب أن يكون رقماً موجباً`;
    }
    return null;
  },

  date: (value: string, fieldName: string): string | null => {
    if (value && isNaN(Date.parse(value))) {
      return `${fieldName} تاريخ غير صحيح`;
    }
    return null;
  },

  dateRange: (startDate: string, endDate: string, fieldName: string = 'النطاق الزمني'): string | null => {
    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      return `${fieldName}: تاريخ البداية يجب أن يكون قبل تاريخ النهاية`;
    }
    return null;
  },

  arabicOnly: (value: string, fieldName: string): string | null => {
    if (value && !/^[\u0600-\u06FF\s]+$/.test(value)) {
      return `${fieldName} يجب أن يحتوي على أحرف عربية فقط`;
    }
    return null;
  },

  englishOnly: (value: string, fieldName: string): string | null => {
    if (value && !/^[a-zA-Z0-9\s\-_]+$/.test(value)) {
      return `${fieldName} يجب أن يحتوي على أحرف إنجليزية فقط`;
    }
    return null;
  },

  taxNumber: (value: string, fieldName: string = 'الرقم الضريبي'): string | null => {
    if (value && !/^\d{15}$/.test(value)) {
      return `${fieldName} يجب أن يكون 15 رقماً`;
    }
    return null;
  },

  commercialRegister: (value: string, fieldName: string = 'رقم السجل التجاري'): string | null => {
    if (value && !/^\d{10}$/.test(value)) {
      return `${fieldName} يجب أن يكون 10 أرقام`;
    }
    return null;
  },
};

export interface ValidationRule {
  validator: (value: any) => string | null;
  message?: string;
}

export function validateField(value: any, rules: ValidationRule[]): string | null {
  for (const rule of rules) {
    const error = rule.validator(value);
    if (error) return error;
  }
  return null;
}

export function validateForm(
  formData: Record<string, any>,
  schema: Record<string, ValidationRule[]>
): Record<string, string> {
  const errors: Record<string, string> = {};

  for (const [field, rules] of Object.entries(schema)) {
    const error = validateField(formData[field], rules);
    if (error) {
      errors[field] = error;
    }
  }

  return errors;
}

// Arabic error messages for common validation scenarios
export const errorMessages = {
  required: 'هذا الحقل مطلوب',
  email: 'البريد الإلكتروني غير صحيح',
  phone: 'رقم الهاتف غير صحيح',
  minLength: 'النص قصير جداً',
  maxLength: 'النص طويل جداً',
  min: 'القيمة صغيرة جداً',
  max: 'القيمة كبيرة جداً',
  positive: 'يجب أن تكون القيمة موجبة',
  date: 'التاريخ غير صحيح',
  dateRange: 'نطاق التاريخ غير صحيح',
  arabic: 'يجب استخدام الأحرف العربية',
  english: 'يجب استخدام الأحرف الإنجليزية',
};
