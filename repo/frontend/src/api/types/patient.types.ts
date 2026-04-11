export interface PatientMasked {
  id: string;
  mrn: string;
  name: string;
  date_of_birth: string;
  gender: string;
  is_active: boolean;
}

export interface PatientDetail {
  id: string;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  ssn: string;
  gender: string;
  phone: string;
  email: string;
  address: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PatientUnmasked {
  mrn: string;
  ssn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  phone: string;
  email: string;
  address: string;
}

export interface BreakGlassResponse {
  break_glass_log_id: string;
  patient: PatientDetail;
}

export interface CreatePatientPayload {
  mrn: string;
  ssn?: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  gender: string;
  phone?: string;
  email?: string;
  address?: string;
}

export interface CreatePatientResponse {
  id: string;
  mrn: string;
  name: string;
  gender: string;
  is_active: boolean;
  created_at: string;
}

export interface BreakGlassPayload {
  justification: string;
  justification_category: string;
}
