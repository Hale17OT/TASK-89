import apiClient from "@/api/client";
import type {
  Consent,
  CreateConsentPayload,
  RevokeConsentPayload,
} from "@/api/types/consent.types";

export async function listConsents(
  patientId: string
): Promise<{ results: Consent[] }> {
  const response = await apiClient.get<{ results: Consent[] }>(
    `patients/${patientId}/consents/`
  );
  return response.data;
}

export async function createConsent(
  patientId: string,
  data: CreateConsentPayload
): Promise<Consent> {
  const response = await apiClient.post<Consent>(
    `patients/${patientId}/consents/`,
    data
  );
  return response.data;
}

export async function getConsent(
  patientId: string,
  consentId: string
): Promise<Consent> {
  const response = await apiClient.get<Consent>(
    `patients/${patientId}/consents/${consentId}/`
  );
  return response.data;
}

export async function revokeConsent(
  patientId: string,
  consentId: string,
  data: RevokeConsentPayload
): Promise<Consent> {
  const response = await apiClient.post<Consent>(
    `patients/${patientId}/consents/${consentId}/revoke/`,
    data
  );
  return response.data;
}
