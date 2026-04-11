import apiClient from "@/api/client";
import type {
  MediaAsset,
  MediaDetail,
  WatermarkConfig,
  Citation,
  InfringementReport,
} from "@/api/types/media.types";

export async function uploadMedia(
  formData: FormData
): Promise<MediaDetail> {
  const response = await apiClient.post<MediaDetail>("media/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function listMedia(
  params?: Record<string, string | number | undefined>
): Promise<{ results: MediaAsset[]; count: number }> {
  const response = await apiClient.get<{
    results: MediaAsset[];
    count: number;
  }>("media/", { params });
  return response.data;
}

export async function getMedia(id: string): Promise<MediaDetail> {
  const response = await apiClient.get<MediaDetail>(`media/${id}/`);
  return response.data;
}

export async function downloadMedia(id: string): Promise<Blob> {
  const response = await apiClient.get(`media/${id}/download/`, {
    responseType: "blob",
  });
  return response.data as Blob;
}

export async function applyWatermark(
  id: string,
  config: WatermarkConfig
): Promise<MediaDetail> {
  const response = await apiClient.post<MediaDetail>(
    `media/${id}/watermark/`,
    config
  );
  return response.data;
}

export async function authorizeRepost(
  id: string,
  formData: FormData
): Promise<Citation> {
  const response = await apiClient.post<Citation>(
    `media/${id}/repost/authorize/`,
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}

export async function attachMediaToPatient(
  mediaId: string,
  patientId: string
): Promise<MediaDetail> {
  const response = await apiClient.post<MediaDetail>(
    `media/${mediaId}/attach-patient/`,
    { patient_id: patientId }
  );
  return response.data;
}

export async function listInfringements(
  params?: Record<string, string | number | undefined>
): Promise<{ results: InfringementReport[]; count: number }> {
  const response = await apiClient.get<{
    results: InfringementReport[];
    count: number;
  }>("media/infringement/", { params });
  return response.data;
}

export async function createInfringement(
  formData: FormData
): Promise<InfringementReport> {
  const response = await apiClient.post<InfringementReport>(
    "media/infringement/",
    formData,
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return response.data;
}

export async function getInfringement(
  id: string
): Promise<InfringementReport> {
  const response = await apiClient.get<InfringementReport>(
    `media/infringement/${id}/`
  );
  return response.data;
}

export async function updateInfringement(
  id: string,
  data: Partial<InfringementReport>
): Promise<InfringementReport> {
  const response = await apiClient.patch<InfringementReport>(
    `media/infringement/${id}/`,
    data
  );
  return response.data;
}
