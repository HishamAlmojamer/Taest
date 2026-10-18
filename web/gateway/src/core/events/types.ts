/**
 * Event-Driven Architecture: Type Definitions
 *
 * This module defines all domain events that flow through the Event Bus.
 * Each event represents a significant business occurrence that may trigger
 * side effects in other modules (e.g., generating journal entries).
 *
 * Accounting Logic:
 * - Events decouple operational modules from the financial ledger.
 * - Modules emit events; the Ledger Engine consumes them to create
 *   balanced double-entry journal entries automatically.
 */

import { PoolClient } from 'pg';

export type EventType =
  | 'sales.invoice.approved'
  | 'sales.invoice.voided'
  | 'inventory.goods.received'
  | 'inventory.goods.issued'
  | 'payroll.approved'
  | 'payroll.voided'
  | 'purchase.order.approved'
  | 'purchase.order.voided'
  | 'payment.received'
  | 'payment.made';

export interface BaseEvent<T = Record<string, unknown>> {
  id: string;
  type: EventType;
  timestamp: Date;
  correlationId: string;
  payload: T;
  metadata: {
    userId?: number;
    companyId?: number;
    branchId?: number;
  };
}

export interface EventPayloadMap {
  'sales.invoice.approved': SalesInvoiceApprovedPayload;
  'sales.invoice.voided': SalesInvoiceVoidedPayload;
  'inventory.goods.received': InventoryGoodsReceivedPayload;
  'inventory.goods.issued': InventoryGoodsIssuedPayload;
  'payroll.approved': PayrollApprovedPayload;
  'payroll.voided': PayrollVoidedPayload;
  'purchase.order.approved': PurchaseOrderApprovedPayload;
  'purchase.order.voided': PurchaseOrderVoidedPayload;
  'payment.received': PaymentReceivedPayload;
  'payment.made': PaymentMadePayload;
}

export interface SalesInvoiceApprovedPayload {
  invoiceId: number;
  invoiceNumber: string;
  customerId: number;
  customerName: string;
  totalAmount: number;
  taxAmount: number;
  discount: number;
  finalAmount: number;
  currencyCode: string;
  items: Array<{
    productId: number;
    quantity: number;
    unitPrice: number;
    totalPrice: number;
  }>;
}

export interface SalesInvoiceVoidedPayload {
  invoiceId: number;
  invoiceNumber: string;
  customerId: number;
  originalEntryId: number;
  reason: string;
}

export interface InventoryGoodsReceivedPayload {
  transactionId: number;
  productId: number;
  productName: string;
  warehouseId: number;
  warehouseName: string;
  quantity: number;
  unitCost: number;
  totalCost: number;
  purchaseOrderId?: number;
  purchaseOrderNumber?: string;
  supplierId?: number;
  supplierName?: string;
  batchNumber?: string;
  currencyCode: string;
}

export interface InventoryGoodsIssuedPayload {
  transactionId: number;
  productId: number;
  productName: string;
  warehouseId: number;
  warehouseName: string;
  quantity: number;
  unitCost: number;
  totalCost: number;
  salesOrderId?: number;
  salesOrderNumber?: string;
  customerId?: number;
  currencyCode: string;
}

export interface PayrollApprovedPayload {
  payrollId: number;
  employeeId: number;
  employeeName: string;
  employeeCode: string;
  departmentId: number;
  departmentName: string;
  periodMonth: number;
  periodYear: number;
  basicSalary: number;
  housingAllowance: number;
  transportationAllowance: number;
  otherAllowances: number;
  totalAllowances: number;
  overtime: number;
  bonus: number;
  deductions: number;
  netSalary: number;
  currencyCode: string;
}

export interface PayrollVoidedPayload {
  payrollId: number;
  employeeId: number;
  originalEntryId: number;
  reason: string;
}

export interface PurchaseOrderApprovedPayload {
  purchaseOrderId: number;
  purchaseOrderNumber: string;
  supplierId: number;
  supplierName: string;
  totalAmount: number;
  taxAmount: number;
  finalAmount: number;
  currencyCode: string;
  items: Array<{
    productId: number;
    quantity: number;
    unitPrice: number;
    totalPrice: number;
  }>;
}

export interface PurchaseOrderVoidedPayload {
  purchaseOrderId: number;
  purchaseOrderNumber: string;
  originalEntryId: number;
  reason: string;
}

export interface PaymentReceivedPayload {
  paymentId: number;
  customerId: number;
  customerName: string;
  amount: number;
  paymentMethod: string;
  referenceNumber?: string;
  currencyCode: string;
}

export interface PaymentMadePayload {
  paymentId: number;
  supplierId: number;
  supplierName: string;
  amount: number;
  paymentMethod: string;
  referenceNumber?: string;
  currencyCode: string;
}

export type EventHandler<T = Record<string, unknown>> = (
  event: BaseEvent<T>,
  clien