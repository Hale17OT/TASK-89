import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Loader2,
  AlertCircle,
  Inbox,
  RefreshCw,
  Download,
  CheckCircle,
  RotateCcw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import apiClient from "@/api/client";
import {
  getDashboard,
  retryOutboxItem,
  acknowledgeOutboxItem,
} from "@/api/endpoints/reports";
import type { OutboxItem } from "@/api/types/report.types";
import { format } from "date-fns";

const STATUS_BADGE: Record<string, string> = {
  queued: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300",
  generating: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  delivered:
    "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  failed: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  stalled:
    "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
};

const SUMMARY_COLORS: Record<string, string> = {
  queued: "border-zinc-300 bg-zinc-50 text-zinc-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300",
  generating: "border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-700 dark:bg-blue-900 dark:text-blue-300",
  delivered: "border-green-300 bg-green-50 text-green-700 dark:border-green-700 dark:bg-green-900 dark:text-green-300",
  failed: "border-red-300 bg-red-50 text-red-700 dark:border-red-700 dark:bg-red-900 dark:text-red-300",
  stalled: "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-900 dark:text-amber-300",
};

export function OutboxDashboardPage() {
  const [autoRefresh, setAutoRefresh] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["outbox-dashboard"],
    queryFn: getDashboard,
    refetchInterval: autoRefresh ? 30000 : false,
  });

  const retryMutation = useMutation({
    mutationFn: retryOutboxItem,
    onSuccess: () => {
      toast.success("Retry initiated");
      queryClient.invalidateQueries({ queryKey: ["outbox-dashboard"] });
    },
    onError: (err: Error) => {
      toast.error(`Retry failed: ${err.message}`);
    },
  });

  const ackMutation = useMutation({
    mutationFn: acknowledgeOutboxItem,
    onSuccess: () => {
      toast.success("Item acknowledged");
      queryClient.invalidateQueries({ queryKey: ["outbox-dashboard"] });
    },
    onError: (err: Error) => {
      toast.error(`Acknowledge failed: ${err.message}`);
    },
  });

  const summary = data
    ? [
        { key: "queued", label: "Queued", count: data.queued },
        { key: "generating", label: "Generating", count: data.generating },
        { key: "delivered", label: "Delivered", count: data.delivered },
        { key: "failed", label: "Failed", count: data.failed },
        { key: "stalled", label: "Stalled", count: data.stalled },
      ]
    : [];

  const items = data?.recent ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Report Outbox</h1>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="h-4 w-4 rounded border-input text-primary focus:ring-ring"
            />
            <span className="text-sm text-muted-foreground">
              Auto-refresh (30s)
            </span>
          </label>
          {autoRefresh && (
            <RefreshCw className="h-4 w-4 animate-spin text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">
            Loading dashboard...
          </span>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-destructive" />
          <p className="mt-2 text-sm text-destructive">
            Failed to load dashboard:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* Summary Bar */}
      {!isLoading && !isError && data && (
        <>
          <div className="flex flex-wrap gap-3">
            {summary.map((s) => (
              <div
                key={s.key}
                className={cn(
                  "rounded-lg border px-4 py-3 min-w-[120px]",
                  SUMMARY_COLORS[s.key]
                )}
              >
                <p className="text-2xl font-bold">{s.count}</p>
                <p className="text-xs font-medium capitalize">{s.label}</p>
              </div>
            ))}
          </div>

          {/* Empty */}
          {items.length === 0 && (
            <div className="rounded-lg border border-border bg-card p-12 text-center">
              <Inbox className="mx-auto h-10 w-10 text-muted-foreground" />
              <p className="mt-3 text-muted-foreground">
                No recent outbox items.
              </p>
            </div>
          )}

          {/* Table */}
          {items.length > 0 && (
            <div className="overflow-x-auto rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Report
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Generated
                    </th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">
                      Format
                    </th>
                    <th className="px-4 py-3 text-center font-medium text-muted-foreground">
                      Status
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item: OutboxItem) => (
                    <tr
                      key={item.id}
                      className="border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors"
                    >
                      <td className="px-4 py-3 font-medium">
                        {item.report_name}
                        {item.last_error && (
                          <p className="mt-0.5 text-xs text-destructive truncate max-w-[300px]">
                            {item.last_error}
                          </p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {format(
                          new Date(item.generated_at),
                          "MMM d, yyyy HH:mm"
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className="uppercase text-xs font-medium text-muted-foreground">
                          {item.file_format}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={cn(
                            "inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
                            STATUS_BADGE[item.status] ??
                              "bg-muted text-muted-foreground"
                          )}
                        >
                          {item.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {item.status === "delivered" && (
                            <button
                              type="button"
                              className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium hover:bg-accent"
                              onClick={async () => {
                                try {
                                  const response = await apiClient.get(
                                    `reports/outbox/${item.id}/download/`,
                                    { responseType: "blob" },
                                  );
                                  const url = URL.createObjectURL(response.data);
                                  const a = document.createElement("a");
                                  a.href = url;
                                  a.download = `${item.report_name}.${item.file_format}`;
                                  a.click();
                                  URL.revokeObjectURL(url);
                                } catch {
                                  toast.error("Download failed");
                                }
                              }}
                            >
                              <Download className="h-3 w-3" />
                              Download
                            </button>
                          )}
                          {(item.status === "failed" ||
                            item.status === "stalled") && (
                            <button
                              type="button"
                              disabled={retryMutation.isPending}
                              onClick={() => retryMutation.mutate(item.id)}
                              className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium hover:bg-accent disabled:opacity-50"
                            >
                              {retryMutation.isPending ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <RotateCcw className="h-3 w-3" />
                              )}
                              Retry
                            </button>
                          )}
                          {item.status === "stalled" && (
                            <button
                              type="button"
                              disabled={ackMutation.isPending}
                              onClick={() => ackMutation.mutate(item.id)}
                              className="inline-flex items-center gap-1 rounded-md border border-border px-2 py-1 text-xs font-medium hover:bg-accent disabled:opacity-50"
                            >
                              {ackMutation.isPending ? (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              ) : (
                                <CheckCircle className="h-3 w-3" />
                              )}
                              Acknowledge
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
