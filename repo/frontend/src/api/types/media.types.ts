export interface MediaAsset {
  id: string;
  original_filename: string;
  originality_status: "original" | "reposted" | "reposted_authorized" | "disputed";
  pixel_hash: string;
  watermark_burned: boolean;
  patient_id?: string;
  created_at: string;
}

export interface MediaDetail extends MediaAsset {
  mime_type: string;
  file_size_bytes: number;
  watermark_settings: Record<string, unknown>;
  evidence_metadata: Record<string, unknown>;
  repost_authorized: boolean | null;
}

export interface WatermarkConfig {
  clinic_name: string;
  date_stamp: boolean;
  opacity: number;
}

export interface Citation {
  id: string;
  media_asset_id: string;
  citation_text: string;
  authorization_file_path: string;
  approved_by_id: string | null;
  approved_at: string | null;
  created_at: string;
}

export interface InfringementReport {
  id: string;
  status: "open" | "investigating" | "resolved" | "dismissed";
  notes: string;
  reference?: string;
  created_at: string;
  opened_at: string;
  investigating_at: string | null;
  resolved_at: string | null;
  dismissed_at: string | null;
  reporter_name?: string;
}
