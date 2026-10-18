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

logger = logging.getLogger(__name__)

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://gateway:3001")


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
            response = await client.post(url, json=body)

            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"EventEmitter: successfully emitted '{event_type}' "
                    f"[correlation_id: {result.get('data', {}).get('correlationId', 'N/A')}]"
                )
                return result
            else:
                error_msg = f"Event emission failed: HTTP {response.status_code} - {response.text}"
                logger.error(f"EventEmitter: {error_msg}")
                raise Exception(error_msg)

    except httpx.ConnectError:
        error_msg = (
            f"EventEmitter: Cannot connect to Gateway at {GATEWAY_URL}. "
            f"Ensure the gateway service is running."
        )
        logger.error(error_msg)
        # In development, we log but don't block the operation
        # In production, this should raise to trigger rollback
        raise Exception(error_msg)

    except httpx.TimeoutException:
        error_msg = f"EventEmitter: Timeout emitting event '{event_type}'"
        logger.error(error_msg)
        raise Exception(error_msg)


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
            "currencyCode": "SAR",
            "items": items,
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
            "currencyCode": "SAR",
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
            "netSalary": float(net_salary),
            "currencyCode": "SAR",
        },
        user_id=user_id,
        company_id=company_id,
    )
