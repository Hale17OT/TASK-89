import apiClient from "@/api/client";
import type {
  Order,
  OrderDetail,
  CreateOrderPayload,
  Payment,
  Refund,
  ReconciliationSummary,
} from "@/api/types/financial.types";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function listOrders(
  params?: Record<string, string | number | undefined>
): Promise<PaginatedResponse<Order>> {
  const response = await apiClient.get<PaginatedResponse<Order>>(
    "financials/orders/",
    { params }
  );
  return response.data;
}

export async function createOrder(
  data: CreateOrderPayload
): Promise<OrderDetail> {
  const response = await apiClient.post<OrderDetail>(
    "financials/orders/",
    data
  );
  return response.data;
}

export async function getOrder(id: string): Promise<OrderDetail> {
  const response = await apiClient.get<OrderDetail>(
    `financials/orders/${id}/`
  );
  return response.data;
}

export async function recordPayment(
  orderId: string,
  data: { amount: number; method: string; check_number?: string },
  idempotencyKey: string
): Promise<Payment> {
  const response = await apiClient.post<Payment>(
    `financials/orders/${orderId}/payments/`,
    data,
    { headers: { "Idempotency-Key": idempotencyKey } }
  );
  return response.data;
}

export async function voidOrder(orderId: string): Promise<OrderDetail> {
  const response = await apiClient.post<OrderDetail>(
    `financials/orders/${orderId}/void/`
  );
  return response.data;
}

export async function listRefunds(
  params?: Record<string, string | number | undefined>
): Promise<PaginatedResponse<Refund>> {
  const response = await apiClient.get<PaginatedResponse<Refund>>(
    "financials/refunds/",
    { params }
  );
  return response.data;
}

export async function createRefund(
  orderId: string,
  data: { amount: number; reason: string; original_payment_id: string }
): Promise<Refund> {
  const response = await apiClient.post<Refund>(
    `financials/orders/${orderId}/refunds/`,
    data
  );
  return response.data;
}

export async function approveRefund(refundId: string): Promise<Refund> {
  const response = await apiClient.post<Refund>(
    `financials/refunds/${refundId}/approve/`
  );
  return response.data;
}

export async function processRefund(refundId: string): Promise<Refund> {
  const response = await apiClient.post<Refund>(
    `financials/refunds/${refundId}/process/`
  );
  return response.data;
}

export async function listReconciliations(
  params?: Record<string, string | number | undefined>
): Promise<PaginatedResponse<ReconciliationSummary>> {
  const response = await apiClient.get<PaginatedResponse<ReconciliationSummary>>(
    "financials/reconciliation/",
    { params }
  );
  return response.data;
}

export async function getReconciliation(
  date: string
): Promise<ReconciliationSummary> {
  const response = await apiClient.get<ReconciliationSummary>(
    `financials/reconciliation/${date}/`
  );
  return response.data;
}

export async function downloadReconciliation(
  date: string,
  format: "csv" | "pdf"
): Promise<Blob> {
  const response = await apiClient.get(
    `financials/reconciliation/${date}/download/`,
    { params: { format }, responseType: "blob" }
  );
  return response.data;
}
