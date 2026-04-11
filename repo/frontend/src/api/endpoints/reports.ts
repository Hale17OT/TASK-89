import apiClient from "@/api/client";
import type {
  ReportSubscription,
  OutboxItem,
  DashboardStats,
} from "@/api/types/report.types";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function listSubscriptions(): Promise<PaginatedResponse<ReportSubscription>> {
  const response = await apiClient.get<PaginatedResponse<ReportSubscription>>(
    "reports/subscriptions/"
  );
  return response.data;
}

export async function createSubscription(
  data: Partial<ReportSubscription>
): Promise<ReportSubscription> {
  const response = await apiClient.post<ReportSubscription>(
    "reports/subscriptions/",
    data
  );
  return response.data;
}

export async function getSubscription(
  id: string
): Promise<ReportSubscription> {
  const response = await apiClient.get<ReportSubscription>(
    `reports/subscriptions/${id}/`
  );
  return response.data;
}

export async function updateSubscription(
  id: string,
  data: Partial<ReportSubscription>
): Promise<ReportSubscription> {
  const response = await apiClient.patch<ReportSubscription>(
    `reports/subscriptions/${id}/`,
    data
  );
  return response.data;
}

export async function deleteSubscription(id: string): Promise<void> {
  await apiClient.delete(`reports/subscriptions/${id}/`);
}

export async function runSubscriptionNow(
  id: string
): Promise<{ message: string; outbox_item: OutboxItem }> {
  const response = await apiClient.post<{ message: string; outbox_item: OutboxItem }>(
    `reports/subscriptions/${id}/run-now/`
  );
  return response.data;
}

export async function listOutbox(
  params?: Record<string, string | number | undefined>
): Promise<PaginatedResponse<OutboxItem>> {
  const response = await apiClient.get<PaginatedResponse<OutboxItem>>(
    "reports/outbox/",
    { params }
  );
  return response.data;
}

export async function getOutboxItem(id: string): Promise<OutboxItem> {
  const response = await apiClient.get<OutboxItem>(`reports/outbox/${id}/`);
  return response.data;
}

export async function retryOutboxItem(
  id: string
): Promise<{ detail: string }> {
  const response = await apiClient.post<{ detail: string }>(
    `reports/outbox/${id}/retry/`
  );
  return response.data;
}

export async function acknowledgeOutboxItem(
  id: string
): Promise<{ detail: string }> {
  const response = await apiClient.post<{ detail: string }>(
    `reports/outbox/${id}/acknowledge/`
  );
  return response.data;
}

export async function getDashboard(): Promise<DashboardStats> {
  const response = await apiClient.get<DashboardStats>(
    "reports/dashboard/"
  );
  return response.data;
}
