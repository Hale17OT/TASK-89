import apiClient from "@/api/client";
import type {
  UserInfo,
  AuditEntry,
  WorkstationBlacklist,
} from "@/api/types/admin.types";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ---- Users ----

export async function listUsers(
  params?: Record<string, string | number | undefined>
): Promise<PaginatedResponse<UserInfo>> {
  const response = await apiClient.get<PaginatedResponse<UserInfo>>(
    "users/",
    { params }
  );
  return response.data;
}

export async function createUser(
  data: Partial<UserInfo> & { password: string }
): Promise<UserInfo> {
  const response = await apiClient.post<UserInfo>("users/", data);
  return response.data;
}

export async function getUser(id: string): Promise<UserInfo> {
  const response = await apiClient.get<UserInfo>(`users/${id}/`);
  return response.data;
}

export async function updateUser(
  id: string,
  data: Partial<UserInfo>
): Promise<UserInfo> {
  const response = await apiClient.patch<UserInfo>(
    `users/${id}/`,
    data
  );
  return response.data;
}

export async function disableUser(
  id: string,
  body?: Record<string, unknown>
): Promise<UserInfo> {
  const response = await apiClient.post<UserInfo>(
    `users/${id}/disable/`,
    body ?? {}
  );
  return response.data;
}

export async function enableUser(id: string): Promise<UserInfo> {
  const response = await apiClient.post<UserInfo>(
    `users/${id}/enable/`
  );
  return response.data;
}

// ---- Workstation Blacklist ----

export async function listWorkstations(
  params?: Record<string, string | number | undefined>
): Promise<WorkstationBlacklist[]> {
  const response = await apiClient.get<WorkstationBlacklist[]>(
    "workstations/",
    { params }
  );
  return response.data;
}

export async function unblockWorkstation(
  id: number
): Promise<{ detail: string }> {
  const response = await apiClient.post<{ detail: string }>(
    `workstations/${id}/unblock/`
  );
  return response.data;
}

// ---- Audit ----

export async function listAuditEntries(
  params?: Record<string, string | number | undefined>
): Promise<PaginatedResponse<AuditEntry>> {
  const response = await apiClient.get<PaginatedResponse<AuditEntry>>(
    "audit/entries/",
    { params }
  );
  return response.data;
}

export async function getAuditEntry(id: number): Promise<AuditEntry> {
  const response = await apiClient.get<AuditEntry>(`audit/entries/${id}/`);
  return response.data;
}

export async function verifyAuditChain(): Promise<{
  is_valid: boolean;
  broken_at_id: number | null;
  total_checked: number;
}> {
  const response = await apiClient.post<{
    is_valid: boolean;
    broken_at_id: number | null;
    total_checked: number;
  }>("audit/verify-chain/");
  return response.data;
}

export async function purgeAudit(
  beforeDate: string
): Promise<{ message: string; deleted_count: number; archive_file?: string }> {
  const response = await apiClient.post<{
    message: string;
    deleted_count: number;
    archive_file?: string;
  }>("audit/purge/", { before_date: beforeDate, confirm: true });
  return response.data;
}

// ---- Sudo ----

export async function acquireSudo(
  password: string,
  actionClass: string
): Promise<{ action_class: string; expires_at: string; expires_in_seconds: number }> {
  const response = await apiClient.post<{
    action_class: string;
    expires_at: string;
    expires_in_seconds: number;
  }>("sudo/acquire/", { password, action_class: actionClass });
  return response.data;
}

export async function getSudoStatus(): Promise<{
  active_sudo_actions: Array<{
    action_class: string;
    expires_in_seconds: number;
  }>;
}> {
  const response = await apiClient.get<{
    active_sudo_actions: Array<{
      action_class: string;
      expires_in_seconds: number;
    }>;
  }>("sudo/status/");
  return response.data;
}

export async function releaseSudo(): Promise<void> {
  await apiClient.delete("sudo/release/");
}
