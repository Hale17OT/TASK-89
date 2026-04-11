export interface Consent {
  id: string;
  purpose: string;
  status: "active" | "expired" | "revoked";
  effective_date: string;
  expiration_date: string | null;
  is_revoked: boolean;
  revoked_at: string | null;
  physical_copy_on_file: boolean;
  granted_at: string;
}

export interface ConsentScopePayload {
  scope_type: "data_field" | "action" | "media_use" | "third_party";
  scope_value: string;
}

export interface CreateConsentPayload {
  purpose: string;
  effective_date: string;
  expiration_date?: string;
  physical_copy_on_file: boolean;
  scopes?: ConsentScopePayload[];
}

export interface RevokeConsentPayload {
  reason?: string;
  physical_copy_warning_acknowledged?: boolean;
}
