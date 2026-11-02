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
  | 'sales.return.approved'
  | 'sales.return.voided'
  | 'purchase.return.approved'
  | 'purchase.return.voided'
  | 'inventory.goods.received'
  | 'inventory.goods.issued'
  | 'payroll.approved'
  | 'payroll.voided'
  | 'payroll.settled'
  | 'employee.advance.granted'
  | 'employee.advance.repaid'
  | 'employee.advance.voided'
  | 'purchase.order.approved'
  | 'purchase.order.voided'
  | 'payment.received'
  | 'payment.made'
  | 'cheque.received'
  | 'cheque.issued'
  | 'cheque.deposited'
  | 'cheque.cleared'
  | 'cheque.returned';

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
  'sales.return.approved': SalesReturnApprovedPayload;
  'sales.return.voided': SalesReturnVoidedPayload;
  'purchase.return.approved': PurchaseReturnApprovedPayload;
  'purchase.return.voided': PurchaseReturnVoidedPayload;
  'inventory.goods.received': InventoryGoodsReceivedPayload;
  'inventory.goods.issued': InventoryGoodsIssuedPayload;
  'payroll.approved': PayrollApprovedPayload;
  'payroll.voided': PayrollVoidedPayload;
  'payroll.settled': PayrollSettledPayload;
  'employee.advance.granted': EmployeeAdvanceGrantedPayload;
  'employee.advance.repaid': EmployeeAdvanceRepaidPayload;
  'employee.advance.voided': EmployeeAdvanceVoidedPayload;
  'purchase.order.approved': PurchaseOrderApprovedPayload;
  'purchase.order.voided': PurchaseOrderVoidedPayload;
  'payment.received': PaymentReceivedPayload;
  'payment.made': PaymentMadePayload;
  'cheque.received': ChequeReceivedPayload;
  'cheque.issued': ChequeIssuedPayload;
  'cheque.deposited': ChequeDepositedPayload;
  'cheque.cleared': ChequeClearedPayload;
  'cheque.returned': ChequeReturnedPayload;
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
  customerName: string;
  originalEntryId: number;
  /** Stock movement ids of this sale's goods-issued transactions (COGS entries to reverse). */
  stockMovementIds: number[];
  reason: string;
}

export interface SalesReturnApprovedPayload {
  returnId: number;
  returnNumber: string;
  saleId?: number;
  saleInvoiceNumber?: string;
  customerId: number;
  customerName: string;
  totalAmount: number;
  taxAmount: number;
  finalAmount: number;
  refundMethod: string;
  isRestocked: boolean;
  currencyCode: string;
  items: Array<{
    productId: number;
    quantity: number;
    unitPrice: number;
    totalPrice: number;
  }>;
}

export interface SalesReturnVoidedPayload {
  returnId: number;
  returnNumber: string;
  customerId: number;
  originalEntryId?: number;
  reason: string;
}

export interface PurchaseReturnApprovedPayload {
  returnId: number;
  returnNumber: string;
  purchaseId?: number;
  purchaseOrderNumber?: string;
  supplierId: number;
  supplierName: string;
  totalAmount: number;
  taxAmount: number;
  finalAmount: number;
  refundMethod: string;
  isRestocked: boolean;
  currencyCode: string;
  items: Array<{
    productId: number;
    quantity: number;
    unitCost: number;
    totalCost: number;
  }>;
}

export interface PurchaseReturnVoidedPayload {
  returnId: number;
  returnNumber: string;
  supplierId: number;
  originalEntryId?: number;
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
  advanceDeduction: number;
  netSalary: number;
  currencyCode: string;
}

export interface PayrollVoidedPayload {  payrollId: number;
  employeeId: number;
  originalEntryId: number;
  reason: string;
}

export interface PayrollSettledPayload {
  payrollId: number;
  employeeId: number;
  employeeName: string;
  periodMonth: number;
  periodYear: number;
  netSalary: number;
  paymentMethod: string;
  bankAccountId?: number;
  bankAccountName?: string;
  paymentDate?: string;
  currencyCode: string;
}

export interface EmployeeAdvanceGrantedPayload {
  advanceId: number;
  employeeId: number;
  employeeName: string;
  employeeCode: string;
  advanceType: string;
  amount: number;
  paymentMethod: string;
  bankAccountId?: number;
  bankAccountName?: string;
  requestDate?: string;
  notes?: string;
  currencyCode: string;
}

export interface EmployeeAdvanceRepaidPayload {
  advanceId: number;
  employeeId: number;
  employeeName: string;
  amount: number;
  paymentMethod: string;
  bankAccountId?: number;
  bankAccountName?: string;
  repaymentDate?: string;
  currencyCode: string;
}

export interface EmployeeAdvanceVoidedPayload {
  advanceId: number;
  employeeId: number;
  employeeName: string;
  originalEntryId?: number;
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

export interface ChequeReceivedPayload {
  chequeId: number;
  chequeNumber: string;
  amount: number;
  customerId?: number;
  customerName?: string;
  payerName?: string;
  bankName?: string;
  dueDate?: string;
  currencyCode: string;
}

export interface ChequeIssuedPayload {
  chequeId: number;
  chequeNumber: string;
  amount: number;
  supplierId?: number;
  supplierName?: string;
  payeeName?: string;
  bankName?: string;
  dueDate?: string;
  currencyCode: string;
}

export interface ChequeDepositedPayload {
  chequeId: number;
  chequeNumber: string;
  amount: number;
  bankId?: number;
  bankName?: string;
  currencyCode: string;
}

export interface ChequeClearedPayload {
  chequeId: number;
  chequeNumber: string;
  amount: number;
  chequeType: string;
  currencyCode: string;
}

export interface ChequeReturnedPayload {
  chequeId: number;
  chequeNumber: string;
  amount: number;
  chequeType: string;
  reason?: string;
  originalEntryId?: number;
  /** Status the cheque had before the return (deposited / under_collection / on_hand). */
  preStatus?: string;
  currencyCode: string;
}

export type EventHandler<T = Record<string, unknown>> = (
  event: BaseEvent<T>,
  client: PoolClient
) => Promise<unknown>;

export interface EventSubscription {
  eventType: EventType | '*';
  handler: EventHandler;
  priority?: number;
}
