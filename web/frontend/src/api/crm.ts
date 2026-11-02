import { get, post, put, del } from './client';
import type { PaginatedResponse } from '@/types';

// ────────────────────────── Types ──────────────────────────

export interface Customer {
  id: number;
  code?: string;
  name: string;
  nameAr?: string;
  phone?: string;
  mobile?: string;
  email?: string;
  address?: string;
  city?: string;
  region?: string;
  country?: string;
  postalCode?: string;
  website?: string;
  fax?: string;
  nationalId?: string;
  taxId?: string;
  customerType?: string;
  industry?: string;
  segmentId?: number;
  segmentName?: string;
  salespersonId?: number;
  parentId?: number;
  priceList?: string;
  currency?: string;
  notes?: string;
  birthdate?: string;
  gender?: string;
  creditLimit: number;
  currentBalance: number;
  balance: number;
  isActive: boolean;
  companyId?: number;
  lastInteractionAt?: string;
  createdAt?: string;
}

export interface CustomerContact {
  id: number;
  customerId: number;
  name: string;
  title?: string;
  department?: string;
  phone?: string;
  mobile?: string;
  email?: string;
  isPrimary: boolean;
  isActive: boolean;
  notes?: string;
}

export interface CustomerAddress {
  id: number;
  customerId: number;
  addressType?: string;
  addressLine1?: string;
  addressLine2?: string;
  city?: string;
  region?: string;
  country?: string;
  postalCode?: string;
  isPrimary: boolean;
}

export interface CustomerDetail extends Customer {
  contacts: CustomerContact[];
  addresses: CustomerAddress[];
  loyalty: { pointsBalance: number; totalPointsEarned: number; tier: string };
}

export interface Supplier {
  id: number;
  code?: string;
  name: string;
  nameAr?: string;
  contactPerson?: string;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  website?: string;
  fax?: string;
  taxId?: string;
  industry?: string;
  currency?: string;
  paymentTerms?: string;
  paymentTermId?: number;
  bankName?: string;
  bankAccount?: string;
  iban?: string;
  notes?: string;
  currentBalance: number;
  balance: number;
  isActive: boolean;
  companyId?: number;
  parentId?: number;
  createdAt?: string;
}

export interface Lead {
  id: number;
  leadName: string;
  company?: string;
  contactPerson?: string;
  phone?: string;
  email?: string;
  source?: string;
  status?: string;
  industry?: string;
  city?: string;
  expectedAmount: number;
  budget?: number;
  leadScore: number;
  assignedTo?: number;
  expectedCloseDate?: string;
  nextFollowUp?: string;
  tags?: string;
  notes?: string;
  isActive: boolean;
  convertedCustomerId?: number;
  convertedOpportunityId?: number;
  convertedAt?: string;
  lostReason?: string;
  wonAmount?: number;
  companyId?: number;
  createdAt?: string;
}

export interface OpportunityStage {
  id: number;
  name: string;
  nameAr?: string;
  position: number;
  probability: number;
  isWon: boolean;
  isLost: boolean;
  color?: string;
  isActive: boolean;
}

export interface Opportunity {
  id: number;
  name: string;
  customerId?: number;
  customerName?: string;
  leadId?: number;
  stageId?: number;
  stage?: string;
  stageName?: string;
  stageColor?: string;
  source?: string;
  probability: number;
  expectedAmount: number;
  expectedCloseDate?: string;
  assignedTo?: number;
  description?: string;
  status: string;
  wonAmount: number;
  closedDate?: string;
  wonLostReason?: string;
  companyId?: number;
  createdAt?: string;
}

export interface FollowUp {
  id: number;
  entityType?: string;
  entityId?: number;
  entityName?: string;
  type: string;
  subject?: string;
  description?: string;
  dueDate?: string;
  completedAt?: string;
  assignedTo?: number;
  reminderAt?: string;
  priority: string;
  status: string;
  createdBy?: number;
  createdAt?: string;
}

export interface Segment {
  id: number;
  name: string;
  nameAr?: string;
  description?: string;
  isActive: boolean;
  customerCount: number;
}

export interface LoyaltyData {
  customerId: number;
  pointsBalance: number;
  totalPointsEarned: number;
  tier: string;
}

export interface ActivityItem {
  type: string;
  id: number;
  title: string;
  amount: number | null;
  status: string;
  date: string | null;
}

export interface CrmDashboardData {
  totalCustomers: number;
  totalLeads: number;
  openOpportunities: number;
  pipelineValue: number;
  wonValue: number;
  leadsByStatus: { status: string; count: number }[];
  upcomingFollowups: FollowUp[];
}

export interface PipelineFunnelItem {
  stageId: number;
  name: string;
  nameAr?: string;
  color?: string;
  count: number;
  value: number;
  isWon: boolean;
  isLost: boolean;
}

export interface LeadsBySourceItem {
  source: string;
  count: number;
}

export interface CustomersBySegmentItem {
  segmentId: number;
  name: string;
  nameAr?: string;
  customerCount: number;
  totalSales: number;
}

export interface TopCustomerItem {
  customerId: number;
  name: string;
  totalSales: number;
}

export interface CustomerTreeNode extends Customer {
  children?: CustomerTreeNode[];
}

export interface SupplierTreeNode extends Supplier {
  children?: SupplierTreeNode[];
}

// ────────────────────────── Segments ──────────────────────────

export async function getSegments() {
  return await get<PaginatedResponse<Segment>>('/crm/segments');
}

export async function createSegment(data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>('/crm/segments', data);
}

export async function updateSegment(id: number, data: Record<string, unknown>) {
  return await put<{ message: string }>(`/crm/segments/${id}`, data);
}

export async function deleteSegment(id: number) {
  return await del<{ message: string }>(`/crm/segments/${id}`);
}

// ────────────────────────── Customers ──────────────────────────

export async function getCustomers(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<Customer>>('/crm/customers', params);
}

export async function getCustomersTree(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<CustomerTreeNode>>('/crm/customers/tree', params);
}

export async function getCustomer(id: number | string) {
  return await get<CustomerDetail>(`/crm/customers/${id}`);
}

export async function createCustomer(data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>('/crm/customers', data);
}

export async function updateCustomer(id: number | string, data: Omit<Partial<Customer>, 'parentId'> & { parentId?: number | null }) {
  return await put<{ message: string }>(`/crm/customers/${id}`, data);
}

export async function deleteCustomer(id: number | string) {
  return await del<{ message: string }>(`/crm/customers/${id}`);
}

export async function createCustomerContact(customerId: number | string, data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>(`/crm/customers/${customerId}/contacts`, data);
}

export async function updateCustomerContact(contactId: number, data: Record<string, unknown>) {
  return await put<{ message: string }>(`/crm/contacts/${contactId}`, data);
}

export async function deleteCustomerContact(contactId: number) {
  return await del<{ message: string }>(`/crm/contacts/${contactId}`);
}

export async function createCustomerAddress(customerId: number | string, data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>(`/crm/customers/${customerId}/addresses`, data);
}

export async function updateCustomerAddress(addressId: number, data: Record<string, unknown>) {
  return await put<{ message: string }>(`/crm/addresses/${addressId}`, data);
}

export async function deleteCustomerAddress(addressId: number) {
  return await del<{ message: string }>(`/crm/addresses/${addressId}`);
}

export async function getCustomerActivities(customerId: number | string) {
  return await get<{ items: ActivityItem[] }>(`/crm/customers/${customerId}/activities`);
}

export async function getCustomerLoyalty(customerId: number | string) {
  return await get<LoyaltyData>(`/crm/customers/${customerId}/loyalty`);
}

export interface LoyaltyCustomerRow {
  customerId: number;
  customerName: string;
  customerNameAr?: string;
  customerPhone?: string;
  pointsBalance: number;
  totalPointsEarned: number;
  tier: string;
}

export async function getLoyaltyList(params: { search?: string; page?: number; pageSize?: number } = {}) {
  return await get<PaginatedResponse<LoyaltyCustomerRow>>('/crm/loyalty', {
    search: params.search,
    page: params.page || 1,
    page_size: params.pageSize || 50,
  });
}

export async function adjustCustomerLoyalty(customerId: number | string, points: number) {
  return await post<{ message: string; pointsBalance: number }>(`/crm/customers/${customerId}/loyalty/adjust`, { points });
}

// ────────────────────────── Suppliers ──────────────────────────

export async function getSuppliers(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<Supplier>>('/crm/suppliers', params);
}

export async function getSuppliersTree(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<SupplierTreeNode>>('/crm/suppliers/tree', params);
}

export async function getSupplier(id: number | string) {
  return await get<Supplier>(`/crm/suppliers/${id}`);
}

export async function createSupplier(data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>('/crm/suppliers', data);
}

export async function updateSupplier(id: number | string, data: Omit<Partial<Supplier>, 'parentId'> & { parentId?: number | null }) {
  return await put<{ message: string }>(`/crm/suppliers/${id}`, data);
}

export async function deleteSupplier(id: number | string) {
  return await del<{ message: string }>(`/crm/suppliers/${id}`);
}

// ────────────────────────── Leads ──────────────────────────

export async function getLeads(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<Lead>>('/crm/leads', params);
}

export async function getLead(id: number | string) {
  return await get<Lead & { followups?: FollowUp[] }>(`/crm/leads/${id}`);
}

export async function createLead(data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>('/crm/leads', data);
}

export async function updateLead(id: number | string, data: Partial<Lead>) {
  return await put<{ message: string }>(`/crm/leads/${id}`, data);
}

export async function deleteLead(id: number | string) {
  return await del<{ message: string }>(`/crm/leads/${id}`);
}

export async function convertLead(id: number | string, data: Record<string, unknown>) {
  return await post<{ message: string; customerId: number; opportunityId?: number }>(`/crm/leads/${id}/convert`, data);
}

// ────────────────────────── Opportunity Stages ──────────────────────────

export async function getOpportunityStages() {
  return await get<PaginatedResponse<OpportunityStage>>('/crm/opportunity-stages');
}

export async function createOpportunityStage(data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>('/crm/opportunity-stages', data);
}

export async function updateOpportunityStage(id: number, data: Record<string, unknown>) {
  return await put<{ message: string }>(`/crm/opportunity-stages/${id}`, data);
}

export async function deleteOpportunityStage(id: number) {
  return await del<{ message: string }>(`/crm/opportunity-stages/${id}`);
}

// ────────────────────────── Opportunities ──────────────────────────

export async function getOpportunities(params?: Record<string, unknown>) {
  return await get<{ items: Opportunity[] }>('/crm/opportunities', params);
}

export async function getOpportunity(id: number | string) {
  return await get<Opportunity>(`/crm/opportunities/${id}`);
}

export async function createOpportunity(data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>('/crm/opportunities', data);
}

export async function updateOpportunity(id: number, data: Partial<Opportunity>) {
  return await put<{ message: string }>(`/crm/opportunities/${id}`, data);
}

export async function deleteOpportunity(id: number) {
  return await del<{ message: string }>(`/crm/opportunities/${id}`);
}

export async function moveOpportunity(id: number, stageId: number) {
  return await post<{ message: string; status: string }>(`/crm/opportunities/${id}/move`, { stageId });
}

export async function closeOpportunity(id: number, data: Record<string, unknown>) {
  return await post<{ message: string; id: number }>(`/crm/opportunities/${id}/close`, data);
}

// ────────────────────────── Follow-ups ──────────────────────────

export async function getFollowups(params?: Record<string, unknown>) {
  return await get<{ items: FollowUp[] }>('/crm/follow-ups', params);
}

export async function getFollowup(id: number) {
  return await get<FollowUp>(`/crm/follow-ups/${id}`);
}

export async function createFollowup(data: Record<string, unknown>) {
  return await post<{ id: number; message: string }>('/crm/follow-ups', data);
}

export async function updateFollowup(id: number, data: Record<string, unknown>) {
  return await put<{ message: string }>(`/crm/follow-ups/${id}`, data);
}

export async function completeFollowup(id: number) {
  return await post<{ message: string }>(`/crm/follow-ups/${id}/complete`, {});
}

export async function deleteFollowup(id: number) {
  return await del<{ message: string }>(`/crm/follow-ups/${id}`);
}

// ────────────────────────── Dashboard & Reports ──────────────────────────

export async function getCrmDashboard() {
  return await get<CrmDashboardData>('/crm/dashboard');
}

export async function getLeadsBySource() {
  return await get<{ items: LeadsBySourceItem[] }>('/crm/reports/leads-by-source');
}

export async function getPipelineFunnel() {
  return await get<{ items: PipelineFunnelItem[] }>('/crm/reports/pipeline-funnel');
}

export async function getCustomersBySegment() {
  return await get<{ items: CustomersBySegmentItem[] }>('/crm/reports/customers-by-segment');
}

export async function getTopCustomers(limit = 10) {
  return await get<{ items: TopCustomerItem[] }>('/crm/reports/top-customers', { limit });
}
