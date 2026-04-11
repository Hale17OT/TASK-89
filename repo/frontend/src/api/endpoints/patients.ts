import apiClient from "@/api/client";
import type {
  PatientMasked,
  PatientDetail,
  CreatePatientPayload,
  CreatePatientResponse,
  BreakGlassPayload,
  BreakGlassResponse,
} from "@/api/types/patient.types";

export async function searchPatients(
  q: string
): Promise<PatientMasked[]> {
  const response = await apiClient.get<PatientMasked[]>(
    "patients/",
    { params: { q } }
  );
  return response.data;
}

export async function createPatient(
  data: CreatePatientPayload
): Promise<CreatePatientResponse> {
  const response = await apiClient.post<CreatePatientResponse>("patients/create/", data);
  return response.data;
}

export async function getPatient(id: string): Promise<PatientDetail> {
  const response = await apiClient.get<PatientDetail>(`patients/${id}/`);
  return response.data;
}

export async function updatePatient(
  id: string,
  data: Partial<CreatePatientPayload>
): Promise<PatientDetail> {
  const response = await apiClient.patch<PatientDetail>(
    `patients/${id}/update/`,
    data
  );
  return response.data;
}

export async function breakGlass(
  id: string,
  payload: BreakGlassPayload
): Promise<BreakGlassResponse> {
  const response = await apiClient.post<BreakGlassResponse>(
    `patients/${id}/break-glass/`,
    payload
  );
  return response.data;
}
