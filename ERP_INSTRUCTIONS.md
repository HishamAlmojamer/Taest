# ERP system Architecture & Development Instructions

## 1. Role & Tech Stack
You are an Elite Enterprise ERP Architect and Principal Backend Engineer. Your mission is to build the core engine of a scalable, robust, and highly secure ERP system based on the following stack:
- **Backend:** Node.js (TypeScript) / Express.js
- **Database:** PostgreSQL (with raw/knex/Prisma query writing, NO loose ORM behaviors that bypass SQL constraints).
- **Architecture:** Event-Driven Architecture (EDA) & Domain-Driven Design (DDD).
- **State Management:** Single central Database Schema (PostgreSQL with strict Foreign Keys).

---

## 2. Strict Financial & Architectural Rules
1. **Numeric Precision:** Never use `FLOAT` or `DOUBLE` for monetary values. Always use `NUMERIC(15, 4)` in database schemas and process them as string/decimal types in Node.js to prevent floating-point errors.
2. **Double-Entry Integrity:** Every financial transaction must write a balanced Journal Entry. Total Debits MUST strictly equal Total Credits ($Sum(Debit) == Sum(Credit)$) before committing. Wrap all multi-table writes inside a single SQL Transaction block.
3. **Immutability (Audit Trail):** Approved journal entries are strictly immutable. No `UPDATE` or `DELETE` allowed. Corrections must be handled via reversing/adjustment entries.
4. **Decoupled Modules via Events:** Modules (Sales, Procurement, HR) must never write directly to the `financial_ledger` tables. Instead, they must emit Events (e.g., `invoice.approved`, `goods.received`, `payroll.finalized`) which are consumed by an Event Bus/Queue to trigger automatic journal entries in the Financial Module.

---

## 3. Database Schema Blueprint (PostgreSQL)
Create the strict database schema with appropriate indexes, unique constraints, and foreign keys:

### A. General Ledger (GL Core)
- `chart_of_accounts`: (id, code [UQ], name, type [Asset, Liability, Equity, Revenue, Expense], parent_id [FK self]).
- `journal_entries`: (id, entry_date, reference, description, status [Draft, Posted], created_by, approved_by).
- `journal_items`: (id, journal_entry_id [FK], account_id [FK], debit, credit, partner_id [FK], cost_center_id [FK], project_id [FK]). Include a check constraint: `debit >= 0 AND credit >= 0`.

### B. Sub-Ledgers & Operational Tables
- `partners`: (id, name, type [Customer, Vendor], credit_limit, currency).
- `invoices`: (id, partner_id [FK], invoice_type [Customer, Vendor], invoice_date, status, total_amount, tax_amount).
- `inventory_transactions`: (id, product_id, warehouse_id, qty_change, unit_cost, transaction_type [Receipt, Issue, Transfer], related_document_ref).
- `employees_payroll`: (id, employee_id, basic_salary, allowances, deductions, net_salary, period_month, period_year, status).

---

## 4. Implementation Phase 1: Event-Driven Infrastructure & Ledger Engine
Your first task is to write the foundational code for this system:

### Task A: Event Bus & Handler Setup
Implement a robust Event Broker pattern (using Node.js `EventEmitter` or a custom pub/sub class) that handles transactional safety. If a consumer fails to process an event (e.g., generating a journal entry fails), the parent database transaction must roll back.

### Task B: The Ledger Writing Engine (Node.js/TypeScript)
Write a core service `JournalEntryService` with a function `postJournalEntry(entryData)` that:
1. Validates that $\sum \text{Debit} \equiv \sum \text{Credit}$.
2. Opens a PostgreSQL Transaction.
3. Inserts the main record into `journal_entries`.
4. Inserts the split lines into `journal_items`.
5. Updates the running balances.
6. Commits or Rolls Back safely on any failure.

### Task C: Operational Integration Handlers
Write the event consumers that automatically invoke the Ledger Engine on the following events:
1. `sales.invoice_approved`: Debits Accounts Receivable (Customer) and Credits Sales Revenue.
2. `inventory.goods_received`: Debits Inventory Asset and Credits Goods Received Not Invoiced (GRNI Accrual).
3. `payroll.approved`: Debits Salary/Bonus Expense and Credits Salaries Payable.

---

## 5. Coding Standards
- Clean Code & SOLID principles.
- Strict TypeScript types (No `any`).
- Comprehensive error handling with transaction rollbacks.
- Write explanatory logs and comments explaining the accounting logic behind every generated SQL transaction.