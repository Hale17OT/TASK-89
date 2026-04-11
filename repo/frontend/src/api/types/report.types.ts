export interface ReportSubscription {
  id: string;
  name: string;
  report_type: string;
  schedule: "daily" | "weekly";
  output_format: "pdf" | "excel" | "image";
  is_active: boolean;
  run_time: string;
  created_at: string;
}

export interface OutboxItem {
  id: string;
  report_name: string;
  status: "queued" | "generating" | "delivered" | "failed" | "stalled";
  file_format: string;
  retry_count: number;
  last_error: string;
  generated_at: string;
  delivered_at: string | null;
}

export interface DashboardStats {
  queued: number;
  generating: number;
  delivered: number;
  failed: number;
  stalled: number;
  recent: OutboxItem[];
}
