export interface UserInfo {
  id: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
  date_joined: string;
  last_login: string | null;
}

export interface AuditEntry {
  id: number;
  event_type: string;
  username_snapshot: string;
  target_model: string;
  target_id: string;
  target_repr: string;
  extra_data: any;
  created_at: string;
}

export interface WorkstationBlacklist {
  id: number;
  client_ip: string;
  workstation_id: string;
  lockout_count: number;
  first_lockout_at: string;
  blacklisted_at: string | null;
  is_active: boolean;
  released_by_username: string | null;
  released_at: string | null;
}
