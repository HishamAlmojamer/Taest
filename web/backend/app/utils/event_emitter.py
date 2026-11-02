"""
Event Emitter: Bridge between Python Backend and Node.js Ledger Engine

This module provides a client that emits domain events to the Gateway's
Event Bus. When the Python backend approves a sale, receives inventory,
or finalizes payroll, it calls this emitter to trigger the corresponding
journal entry creation in the Node.js Ledger Engine.

Architecture:
  Python Backend (operational) --> Event Emitter --> Gateway Event Bus --> Ledger Engine --> PostgreSQL

Accounting Logic:
  - Events are emitted WITHIN the same database transaction as the
    operational write, ensuring atomicity.
  - If the event processing fails (ledger write fails), the entire
    transaction rolls back in the Python backend.
"""

import httpx
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import select

from app.config import settings
from app.database import async_session_factory
from app.models.currency import Currency
from app.utils.security import create_access_token

logger = logging.getLogger(__name__)


class LedgerEventError(Exception):
    """Raised when a domain event cannot be posted to the ledger engine.

    Callers must let this bubble up so the surrounding database transaction is
    rolled back; an operational document must never be committed without its
    accounting entry.
    """


GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:3001")

_BASE_CURRENCY_CACHE: dict = {"code": None, "fetched_at": None}
_BASE_CURRENCY_TTL_SECONDS = 60


async def _base_currency_code() -> str:
    """Resolve the system base currency from the database (cached briefly).

    Falls back to 'SAR' when the table is not seeded or the lookup fails so the
    backend never hardcodes the currency in emitted ledger events.
    """
    now = datetime.now()
    cached = _BASE_CURRENCY_CACHE.get("code")
    fetched_at = _BASE_CURRENCY_CACHE.get("fetched_at")
    if cached and fetched_at and (now - fetched_at).total_seconds() < _BASE_CURRENCY_TTL_SECONDS:
        return cached
    code = "SAR"
    try:
        async with async_session_factory() as db:
            row = (await db.execute(
                select(Currency).where(Currency.is_base_currency.is_(True)).limit(1)
            )).scalar_one_or_none()
            if row and row.code:
                code = row.code
    except Exception as exc:  # pragma: no cover
        logger.warning("EventEmitter: failed to read base currency, using default: %s", exc)
    _BASE_CURRENCY_CACHE["code"] = code
    _BASE_CURRENCY_CACHE["fetched_at"] = now
    return code

_SERVICE_USER_ID = 0
_SERVICE_USERNAME = "system"
_SERVICE_ROLE = "admin"


def _build_service_headers(user_id: Optional[int] = None, role: Optional[str] = None) -> dict[str, str]:
    """Build Authorization header with a service token signed with the shared JWT secret.

    The gateway's authenticate middleware verifies this token using the same
    JWT_SECRET, so the backend can emit ledger events on behalf of the caller.
    """
    token = create_access_token({
        "sub": str(user_id if user_id is not None else _SERVICE_USER_ID),
        "username": _SERVICE_USERNAME,
        "role": role or _SERVICE_ROLE,
    })
    return {"Authorization": f"Bearer {token}"}


async def emit_event(
    event_type: str,
    payload: dict[str, Any],
    metadata: Optional[dict[str, Any]] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
    branch_id: Optional[int] = None,
) -> dict[str, Any]:
    """
    Emit a domain event to the Gateway's Ledger Engine.

    Args:
        event_type: The event type (e.g., 'sales.invoice.approved')
        payload: The event payload data
        metadata: Optional metadata (userId, companyId, branchId)
        user_id: User who triggered the event
        company_id: Company context
        branch_id: Branch context

    Returns:
        Response from the gateway

    Raises:
        Exception: If the event emission fails (should trigger transaction rollback)
    """
    url = f"{GATEWAY_URL}/api/ledger/emit"

    event_metadata = metadata or {}
    if user_id:
        event_metadata["userId"] = user_id
    if company_id:
        event_metadata["companyId"] = company_id
    if branch_id:
        event_metadata["branchId"] = branch_id

    body = {
        "type": event_type,
        "payload": payload,
        "metadata": event_metadata,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                url,
                json=body,
                headers=_build_service_headers(user_id=user_id),
            )

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"EventEmitter: successfully emitted '{event_type}' "
                    f"[correlation_id: {result.get('data', {}).get('correlationId', 'N/A')}]"
                )
                return result
            error_msg = f"Event emission failed: HTTP {response.status_code} - {response.text}"
            logger.error("EventEmitter: %s", error_msg)
            raise LedgerEventError(error_msg)

    except httpx.ConnectError as exc:
        error_msg = (
            f"EventEmitter: Cannot connect to Gateway at {GATEWAY_URL}. "
            f"Ensure the gateway service is running."
        )
        logger.error(error_msg)
        raise LedgerEventError(error_msg) from exc

    except httpx.TimeoutException as exc:
        error_msg = f"EventEmitter: Timeout emitting event '{event_type}'"
        logger.error(error_msg)
        raise LedgerEventError(error_msg) from exc

    except httpx.HTTPError as exc:
        error_msg = f"EventEmitter: HTTP error emitting event '{event_type}': {exc}"
        logger.error(error_msg)
        raise LedgerEventError(error_msg) from exc


async def emit_payment_received(
    payment_id: int,
    customer_id: int,
    customer_name: str,
    amount: float,
    payment_method: str,
    reference_number: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a payment.received event (Dr Bank / Cr AR)."""
    return await emit_event(
        event_type="payment.received",
        payload={
            "paymentId": payment_id,
            "customerId": customer_id,
            "customerName": customer_name,
            "amount": float(amount),
            "paymentMethod": payment_method,
            "referenceNumber": reference_number,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_payment_made(
    payment_id: int,
    supplier_id: int,
    supplier_name: str,
    amount: float,
    payment_method: str,
    reference_number: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a payment.made event (Dr AP / Cr Bank)."""
    return await emit_event(
        event_type="payment.made",
        payload={
            "paymentId": payment_id,
            "supplierId": supplier_id,
            "supplierName": supplier_name,
            "amount": float(amount),
            "paymentMethod": payment_method,
            "referenceNumber": reference_number,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_sales_return_approved(
    return_id: int,
    return_number: str,
    customer_id: int,
    customer_name: str,
    total_amount: float,
    tax_amount: float,
    final_amount: float,
    refund_method: str,
    is_restocked: bool,
    items: list[dict],
    sale_id: Optional[int] = None,
    sale_invoice_number: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a sales.return.approved event (Dr Sales Return / Cr AR, restore inventory if restocked)."""
    return await emit_event(
        event_type="sales.return.approved",
        payload={
            "returnId": return_id,
            "returnNumber": return_number,
            "saleId": sale_id,
            "saleInvoiceNumber": sale_invoice_number,
            "customerId": customer_id,
            "customerName": customer_name,
            "totalAmount": float(total_amount),
            "taxAmount": float(tax_amount),
            "finalAmount": float(final_amount),
            "refundMethod": refund_method,
            "isRestocked": bool(is_restocked),
            "currencyCode": await _base_currency_code(),
            "items": items,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_purchase_return_approved(
    return_id: int,
    return_number: str,
    supplier_id: int,
    supplier_name: str,
    total_amount: float,
    tax_amount: float,
    final_amount: float,
    refund_method: str,
    is_restocked: bool,
    items: list[dict],
    purchase_id: Optional[int] = None,
    purchase_order_number: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a purchase.return.approved event (Dr AP / Cr Purchase Return, adjust inventory if restocked)."""
    return await emit_event(
        event_type="purchase.return.approved",
        payload={
            "returnId": return_id,
            "returnNumber": return_number,
            "purchaseId": purchase_id,
            "purchaseOrderNumber": purchase_order_number,
            "supplierId": supplier_id,
            "supplierName": supplier_name,
            "totalAmount": float(total_amount),
            "taxAmount": float(tax_amount),
            "finalAmount": float(final_amount),
            "refundMethod": refund_method,
            "isRestocked": bool(is_restocked),
            "currencyCode": await _base_currency_code(),
            "items": items,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_sale_approved(
    invoice_id: int,
    invoice_number: str,
    customer_id: int,
    customer_name: str,
    total_amount: float,
    tax_amount: float,
    discount: float,
    final_amount: float,
    items: list[dict],
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a sales.invoice.approved event."""
    return await emit_event(
        event_type="sales.invoice.approved",
        payload={
            "invoiceId": invoice_id,
            "invoiceNumber": invoice_number,
            "customerId": customer_id,
            "customerName": customer_name,
            "totalAmount": float(total_amount),
            "taxAmount": float(tax_amount),
            "discount": float(discount),
            "finalAmount": float(final_amount),
            "currencyCode": await _base_currency_code(),
            "items": items,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_sale_voided(
    invoice_id: int,
    invoice_number: str,
    customer_id: Optional[int],
    customer_name: Optional[str],
    original_entry_id: Optional[int],
    stock_movement_ids: list[int],
    reason: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a sales.invoice.voided event (reverses revenue + COGS entries)."""
    return await emit_event(
        event_type="sales.invoice.voided",
        payload={
            "invoiceId": invoice_id,
            "invoiceNumber": invoice_number,
            "customerId": customer_id or 0,
            "customerName": customer_name or "Unknown Customer",
            "originalEntryId": original_entry_id,
            "stockMovementIds": [int(sm) for sm in (stock_movement_ids or [])],
            "reason": reason,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_goods_issued(
    transaction_id: int,
    product_id: int,
    product_name: str,
    warehouse_id: int,
    warehouse_name: str,
    quantity: int,
    unit_cost: float,
    total_cost: float,
    customer_id: Optional[int] = None,
    customer_name: Optional[str] = None,
    sales_order_id: Optional[int] = None,
    sales_order_number: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit an inventory.goods.issued event (Dr COGS / Cr Inventory)."""
    return await emit_event(
        event_type="inventory.goods.issued",
        payload={
            "transactionId": transaction_id,
            "productId": product_id,
            "productName": product_name,
            "warehouseId": warehouse_id,
            "warehouseName": warehouse_name,
            "quantity": quantity,
            "unitCost": float(unit_cost),
            "totalCost": float(total_cost),
            "currencyCode": await _base_currency_code(),
            "customerId": customer_id,
            "customerName": customer_name,
            "salesOrderId": sales_order_id,
            "salesOrderNumber": sales_order_number,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_purchase_approved(
    purchase_order_id: int,
    purchase_order_number: str,
    supplier_id: int,
    supplier_name: str,
    total_amount: float,
    tax_amount: float,
    discount: float,
    final_amount: float,
    items: list[dict],
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a purchase.order.approved event (Dr Inventory + VAT Input / Cr AP)."""
    return await emit_event(
        event_type="purchase.order.approved",
        payload={
            "purchaseOrderId": purchase_order_id,
            "purchaseOrderNumber": purchase_order_number,
            "supplierId": supplier_id,
            "supplierName": supplier_name,
            "totalAmount": float(total_amount),
            "taxAmount": float(tax_amount),
            "discount": float(discount),
            "finalAmount": float(final_amount),
            "currencyCode": await _base_currency_code(),
            "items": items,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_purchase_voided(
    purchase_order_id: int,
    purchase_order_number: str,
    original_entry_id: Optional[int],
    reason: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a purchase.order.voided event (reverses the original entry)."""
    return await emit_event(
        event_type="purchase.order.voided",
        payload={
            "purchaseOrderId": purchase_order_id,
            "purchaseOrderNumber": purchase_order_number,
            "originalEntryId": original_entry_id,
            "reason": reason,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_goods_received(
    transaction_id: int,
    product_id: int,
    product_name: str,
    warehouse_id: int,
    warehouse_name: str,
    quantity: int,
    unit_cost: float,
    total_cost: float,
    supplier_id: Optional[int] = None,
    supplier_name: Optional[str] = None,
    purchase_order_number: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit an inventory.goods.received event."""
    return await emit_event(
        event_type="inventory.goods.received",
        payload={
            "transactionId": transaction_id,
            "productId": product_id,
            "productName": product_name,
            "warehouseId": warehouse_id,
            "warehouseName": warehouse_name,
            "quantity": quantity,
            "unitCost": float(unit_cost),
            "totalCost": float(total_cost),
            "currencyCode": await _base_currency_code(),
            "supplierId": supplier_id,
            "supplierName": supplier_name,
            "purchaseOrderNumber": purchase_order_number,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_payroll_approved(
    payroll_id: int,
    employee_id: int,
    employee_name: str,
    employee_code: str,
    department_id: int,
    department_name: str,
    period_month: int,
    period_year: int,
    basic_salary: float,
    housing_allowance: float,
    transportation_allowance: float,
    other_allowances: float,
    total_allowances: float,
    overtime: float,
    bonus: float,
    deductions: float,
    net_salary: float,
    advance_deduction: float = 0,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a payroll.approved event."""
    return await emit_event(
        event_type="payroll.approved",
        payload={
            "payrollId": payroll_id,
            "employeeId": employee_id,
            "employeeName": employee_name,
            "employeeCode": employee_code,
            "departmentId": department_id,
            "departmentName": department_name,
            "periodMonth": period_month,
            "periodYear": period_year,
            "basicSalary": float(basic_salary),
            "housingAllowance": float(housing_allowance),
            "transportationAllowance": float(transportation_allowance),
            "otherAllowances": float(other_allowances),
            "totalAllowances": float(total_allowances),
            "overtime": float(overtime),
            "bonus": float(bonus),
            "deductions": float(deductions),
            "advanceDeduction": float(advance_deduction),
            "netSalary": float(net_salary),
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_payroll_settled(
    payroll_id: int,
    employee_id: int,
    employee_name: str,
    period_month: int,
    period_year: int,
    net_salary: float,
    payment_method: str,
    bank_account_id: Optional[int] = None,
    bank_account_name: Optional[str] = None,
    payment_date: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a payroll.settled event (salary actually paid from bank/cash)."""
    return await emit_event(
        event_type="payroll.settled",
        payload={
            "payrollId": payroll_id,
            "employeeId": employee_id,
            "employeeName": employee_name,
            "periodMonth": period_month,
            "periodYear": period_year,
            "netSalary": float(net_salary),
            "paymentMethod": payment_method,
            "bankAccountId": bank_account_id,
            "bankAccountName": bank_account_name,
            "paymentDate": payment_date,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_payroll_voided(
    payroll_id: int,
    employee_id: int,
    original_entry_id: Optional[int],
    reason: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit a payroll.voided event."""
    return await emit_event(
        event_type="payroll.voided",
        payload={
            "payrollId": payroll_id,
            "employeeId": employee_id,
            "originalEntryId": original_entry_id,
            "reason": reason,
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_advance_granted(
    advance_id: int,
    employee_id: int,
    employee_name: str,
    employee_code: str,
    advance_type: str,
    amount: float,
    payment_method: str,
    bank_account_id: Optional[int] = None,
    bank_account_name: Optional[str] = None,
    request_date: Optional[str] = None,
    notes: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit an employee.advance.granted event (money given to the employee)."""
    return await emit_event(
        event_type="employee.advance.granted",
        payload={
            "advanceId": advance_id,
            "employeeId": employee_id,
            "employeeName": employee_name,
            "employeeCode": employee_code,
            "advanceType": advance_type,
            "amount": float(amount),
            "paymentMethod": payment_method,
            "bankAccountId": bank_account_id,
            "bankAccountName": bank_account_name,
            "requestDate": request_date,
            "notes": notes,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_advance_repaid(
    advance_id: int,
    employee_id: int,
    employee_name: str,
    amount: float,
    payment_method: str,
    bank_account_id: Optional[int] = None,
    bank_account_name: Optional[str] = None,
    repayment_date: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit an employee.advance.repaid event (cash repayment by the employee)."""
    return await emit_event(
        event_type="employee.advance.repaid",
        payload={
            "advanceId": advance_id,
            "employeeId": employee_id,
            "employeeName": employee_name,
            "amount": float(amount),
            "paymentMethod": payment_method,
            "bankAccountId": bank_account_id,
            "bankAccountName": bank_account_name,
            "repaymentDate": repayment_date,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_advance_voided(
    advance_id: int,
    employee_id: int,
    employee_name: str,
    original_entry_id: Optional[int],
    reason: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit an employee.advance.voided event (reverses the grant)."""
    return await emit_event(
        event_type="employee.advance.voided",
        payload={
            "advanceId": advance_id,
            "employeeId": employee_id,
            "employeeName": employee_name,
            "originalEntryId": original_entry_id,
            "reason": reason,
        },
        user_id=user_id,
        company_id=company_id,
    )


# ──────────────────────────────────────────────
# Cheques — lifecycle accounting events
# ──────────────────────────────────────────────

async def emit_cheque_received(
    cheque_id: int,
    cheque_number: str,
    amount: float,
    customer_id: Optional[int],
    customer_name: Optional[str],
    payer_name: Optional[str],
    bank_name: Optional[str],
    due_date: Optional[str],
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit cheque.received event (Dr Cheques-on-Hand / Cr Customer-AR)."""
    return await emit_event(
        event_type="cheque.received",
        payload={
            "chequeId": cheque_id,
            "chequeNumber": cheque_number,
            "amount": float(amount),
            "customerId": customer_id,
            "customerName": customer_name,
            "payerName": payer_name,
            "bankName": bank_name,
            "dueDate": due_date,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_cheque_issued(
    cheque_id: int,
    cheque_number: str,
    amount: float,
    supplier_id: Optional[int],
    supplier_name: Optional[str],
    payee_name: Optional[str],
    bank_name: Optional[str],
    due_date: Optional[str],
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit cheque.issued event (Dr Supplier-AP / Cr Cheques-Issued)."""
    return await emit_event(
        event_type="cheque.issued",
        payload={
            "chequeId": cheque_id,
            "chequeNumber": cheque_number,
            "amount": float(amount),
            "supplierId": supplier_id,
            "supplierName": supplier_name,
            "payeeName": payee_name,
            "bankName": bank_name,
            "dueDate": due_date,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_cheque_deposited(
    cheque_id: int,
    cheque_number: str,
    amount: float,
    bank_id: Optional[int],
    bank_name: Optional[str],
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit cheque.deposited event (Dr Bank / Cr Cheques-on-Hand) — received cheques only."""
    return await emit_event(
        event_type="cheque.deposited",
        payload={
            "chequeId": cheque_id,
            "chequeNumber": cheque_number,
            "amount": float(amount),
            "bankId": bank_id,
            "bankName": bank_name,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_cheque_cleared(
    cheque_id: int,
    cheque_number: str,
    amount: float,
    cheque_type: str,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit cheque.cleared event (for issued cheques: Dr Cheques-Issued / Cr Bank)."""
    return await emit_event(
        event_type="cheque.cleared",
        payload={
            "chequeId": cheque_id,
            "chequeNumber": cheque_number,
            "amount": float(amount),
            "chequeType": cheque_type,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )


async def emit_cheque_returned(
    cheque_id: int,
    cheque_number: str,
    amount: float,
    cheque_type: str,
    reason: Optional[str],
    original_entry_id: Optional[int],
    pre_status: Optional[str] = None,
    user_id: Optional[int] = None,
    company_id: Optional[int] = None,
) -> dict[str, Any]:
    """Emit cheque.returned event (bounced/returned cheque).

    `pre_status` is the status the cheque had before the return transition. It
    tells the ledger engine whether the cheque had already been deposited:
    - deposited / under_collection: post Dr AR / Cr Bank (deposit bounced)
    - on_hand (pre-deposit): reverse the original received/issued entry
    """
    return await emit_event(
        event_type="cheque.returned",
        payload={
            "chequeId": cheque_id,
            "chequeNumber": cheque_number,
            "amount": float(amount),
            "chequeType": cheque_type,
            "reason": reason,
            "originalEntryId": original_entry_id,
            "preStatus": pre_status,
            "currencyCode": await _base_currency_code(),
        },
        user_id=user_id,
        company_id=company_id,
    )
