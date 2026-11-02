/**
 * Event Handler Registry
 *
 * Centralizes all event handler registrations.
 * This is the single entry point for wiring up the Event Bus
 * with all operational event consumers.
 *
 * Architecture:
 *   - Each handler module exports functions for specific event types
 *   - This registry subscribes them to the Event Bus
 *   - Priority determines execution order (lower = first)
 */

import { getEventBus } from '../events/EventBus';
import { handleSalesInvoiceApproved, handleSalesInvoiceVoided } from './SalesEventHandler';
import { handleSalesReturnApproved, handleSalesReturnVoided, handlePurchaseReturnApproved, handlePurchaseReturnVoided } from './ReturnsEventHandler';
import { handleInventoryGoodsReceived, handleInventoryGoodsIssued } from './InventoryEventHandler';
import { handlePayrollApproved, handlePayrollVoided, handlePayrollSettled } from './PayrollEventHandler';
import {
  handleEmployeeAdvanceGranted,
  handleEmployeeAdvanceRepaid,
  handleEmployeeAdvanceVoided,
} from './AdvanceEventHandler';
import { handlePurchaseOrderApproved, handlePurchaseOrderVoided } from './PurchaseEventHandler';
import { handlePaymentReceived, handlePaymentMade } from './PaymentEventHandler';
import {
  handleChequeReceived,
  handleChequeIssued,
  handleChequeDeposited,
  handleChequeCleared,
  handleChequeReturned,
} from './ChequeEventHandler';
import { logger } from '../../services/logger';

/**
 * Register all event handlers with the Event Bus.
 * Call this once during application startup.
 */
export function registerEventHandlers(): void {
  const bus = getEventBus();

  logger.info('EventHandlerRegistry: registering all event handlers...');

// ==========================================
  // Sales Event Handlers
  // ==========================================
  bus.subscribe('sales.invoice.approved', handleSalesInvoiceApproved, 10);
  bus.subscribe('sales.invoice.voided', handleSalesInvoiceVoided, 10);

  // ==========================================
  // Returns Event Handlers
  // ==========================================
  bus.subscribe('sales.return.approved', handleSalesReturnApproved, 10);
  bus.subscribe('sales.return.voided', handleSalesReturnVoided, 10);
  bus.subscribe('purchase.return.approved', handlePurchaseReturnApproved, 10);
  bus.subscribe('purchase.return.voided', handlePurchaseReturnVoided, 10);

  // ==========================================
  // Inventory Event Handlers
  // ==========================================
  bus.subscribe('inventory.goods.received', handleInventoryGoodsReceived, 10);
  bus.subscribe('inventory.goods.issued', handleInventoryGoodsIssued, 10);

  // ==========================================
  // Payroll Event Handlers
  // ==========================================
  bus.subscribe('payroll.approved', handlePayrollApproved, 10);
  bus.subscribe('payroll.voided', handlePayrollVoided, 10);
  bus.subscribe('payroll.settled', handlePayrollSettled, 10);

  // ==========================================
  // Employee Advance Event Handlers
  // ==========================================
  bus.subscribe('employee.advance.granted', handleEmployeeAdvanceGranted, 10);
  bus.subscribe('employee.advance.repaid', handleEmployeeAdvanceRepaid, 10);
  bus.subscribe('employee.advance.voided', handleEmployeeAdvanceVoided, 10);

  // ==========================================
  // Purchase Event Handlers
  // ==========================================
  bus.subscribe('purchase.order.approved', handlePurchaseOrderApproved, 10);
  bus.subscribe('purchase.order.voided', handlePurchaseOrderVoided, 10);

  // ==========================================
  // Payment Event Handlers
  // ==========================================
  bus.subscribe('payment.received', handlePaymentReceived, 10);
  bus.subscribe('payment.made', handlePaymentMade, 10);

  // ==========================================
  // Cheque Event Handlers
  // ==========================================
  bus.subscribe('cheque.received', handleChequeReceived, 10);
  bus.subscribe('cheque.issued', handleChequeIssued, 10);
  bus.subscribe('cheque.deposited', handleChequeDeposited, 10);
  bus.subscribe('cheque.cleared', handleChequeCleared, 10);
  bus.subscribe('cheque.returned', handleChequeReturned, 10);

  const handlerCounts = bus.getHandlerCount();
  const totalHandlers = Object.values(handlerCounts).reduce<number>((a: number, b: number) => a + b, 0);
  logger.info(
    `EventHandlerRegistry: registered ${totalHandlers} handlers across ${Object.keys(handlerCounts).length} event types`
  );
}
