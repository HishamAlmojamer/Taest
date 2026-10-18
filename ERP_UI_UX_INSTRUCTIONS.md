# ERP UI/UX Design & Frontend Development Instructions

## 1. Role & Frontend Tech Stack
You are a World-Class UX Architect and Elite Frontend Engineer specializing in high-density Enterprise SaaS Applications. Your mission is to build a futuristic, highly intuitive, and ultra-performant Web UI for our ERP system based on:
- **Framework:** React.js with TypeScript.
- **Styling:** Tailwind CSS (for modern, highly responsive utility-first layout).
- **Component Library Base:** Radix UI / Shadcn UI concepts (accessible, clean, and highly customizable).
- **State Management:** React Context or Zustand for fast, lightweight local state management.
- **Design System Style:** Modern Clean B2B Flat-Glassmorphism (High-density, low distraction, soft contrast, dark-mode first support).

---

## 2. Strict UX/UI Golden Rules for ERPs
1. **Keyboard-First Navigation (Speed):**
   - Every input form (like invoices or journal entries) must support complete keyboard navigation.
   - Use `Tab` and `Shift+Tab` logically. Implement custom `Enter` or `ArrowDown` keys to dynamically append a new line to transactional tables (e.g., adding a new journal item or invoice item) without forcing the user to reach for the mouse.
2. **Data-Density Balance:**
   - Use high-density grids (`py-1` or `py-1.5` table rows) to fit large tables on standard screens. 
   - Avoid massive white spaces. Use subtle borders (e.g., `border-slate-200` / `border-slate-800` in dark mode) to cleanly separate sections.
3. **Color Coding as Status:**
   - Never use colors randomly. Colors must represent functional state:
     * **Green (Emerald-500):** Approved / Posted / Paid / Stock Received.
     * **Orange (Amber-500):** Draft / Pending Approval / In Transit.
     * **Red (Rose-500):** Cancelled / Rejected / Overdue.
     * **Blue (Sky-500):** Active / In Progress.
4. **Instant Action & Micro-interactions:**
   - Provide instant optimistic UI updates on button clicks.
   - Use smooth, non-intrusive micro-animations (e.g., subtle scale-down on press, smooth height expansions for dropdowns).

---

## 3. Key Layouts & Screen Blueprints to Implement

### A. The Master Dashboard (The Command Center)
- **Visuals:** Top-level KPIs cards with sparkline charts (Cash Flow, AR, AP, Active Sales).
- **Features:** 
  - An **OMNI Search bar (Command+K or Ctrl+K menu)** that lets users search for *anything* instantly (e.g., typing "Inv-2026-005" opens the invoice, typing "Add Employee" opens the HR form).
  - High-performance grid showing "Tasks Requiring Your Approval".

### B. High-Density Transactional Form (e.g., The Invoice Builder)
- **Top Bar:** Document metadata (Status Badge, Invoice Number, Date, Currency) with a sticky "Approve/Post" primary action button.
- **Form Section:** Responsive 2-to-4 grid for partner selection, payment terms, and date picker.
- **Line Items Grid (Dynamic Table):**
  - Columns: Product/Account, Description, Quantity, Unit Price, Tax %, Line Total.
  - Line totals must compute instantly in the client state as the user types.
- **Bottom Sidebar/Section:** Summary calculations (Subtotal, Total Taxes, Grand Total) aligned cleanly to the right side.

### C. Shajarat Al-Hisabat (The Interactive Tree Chart of Accounts)
- **Visuals:** A collapsible, high-speed nested folder structure.
- **Interaction:**
  - Fast search filtering: Typing "Cash" instantly collapses non-matching branches and highlights "Cash at Banks".
  - Right-click or slide-over drawer to add a sub-account, edit account details, or view its ledger ledger card.

---

## 4. Specific Component Guidelines & Tailored Tailwind Theme
- **Fonts:** Clean sans-serif with excellent Arabic/English legibility (e.g., Inter for English, Cairo or IBM Plex Sans Arabic for Arabic).
- **Contrast:** High readability. Backgrounds: light mode (`bg-slate-50`), dark mode (`bg-zinc-950`). Card/Container surfaces: light mode (`bg-white`), dark mode (`bg-zinc-900`).
- **Input Fields:**
  - On focus: Active ring outline (`focus-visible:ring-2 focus-visible:ring-primary-500`).
  - Read-only or disabled fields must have clear visual indicators (`bg-slate-100 dark:bg-zinc-800 cursor-not-allowed`).

---

## 5. Coding Deliverables
Your task is to write modular, reusable, and type-safe React components implementing:
1. **The Global Command Palette (`<CommandMenu />`):** A Ctrl+K dialog utilizing `cmdk` or a custom keydown listener to search and jump to modules.
2. **The Dynamic Transaction Table Component (`<DynamicLedgerTable />`):** A reusable table allowing adding, removing, and tab-navigating rows of account/product lines with instant formula calculations.
3. **Modern Status Badges Component (`<StatusBadge status="..." />`):** Utilizing modern translucent color styling (e.g., `bg-emerald-500/10 text-emerald-500` for Posted).