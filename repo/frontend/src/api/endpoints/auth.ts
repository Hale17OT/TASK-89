import apiClient from "@/api/client";
import type {
  LoginRequest,
  LoginResponse,
  SessionInfo,
  SessionRefreshResponse,
  ChangePasswordRequest,
  User,
} from "@/api/types/auth.types";

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>("auth/login/", data);
  return response.data;
}

export async function logout(): Promise<void> {
  await apiClient.post("auth/logout/");
}

export async function getSession(): Promise<SessionInfo> {
  const response = await apiClient.get<SessionInfo>("auth/session/");
  return response.data;
}

export async function refreshSession(): Promise<SessionRefreshResponse> {
  const response = await apiClient.post<SessionRefreshResponse>("auth/session/refresh/");
  return response.data;
}

export async function changePassword(
  data: ChangePasswordRequest
): Promise<{ detail: string }> {
  const response = await apiClient.post<{ detail: string }>(
    "auth/change-password/",
    data
  );
  return response.data;
}
