export interface User {
  id: string;
  username: string;
  role: string;
  full_name: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  user: User;
  idle_timeout_seconds: number;
  absolute_session_limit: number;
}

export interface SessionInfo {
  user: User;
  idle_remaining_seconds: number;
  absolute_remaining_seconds: number;
}

export interface SessionRefreshResponse {
  idle_remaining_seconds: number;
  absolute_remaining_seconds: number;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}
