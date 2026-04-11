import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Plus,
  AlertCircle,
  AlertTriangle,
  Search,
} from "lucide-react";
import { listInfringements } from "@/api/endpoints/media";
import { cn } from "@/lib/utils";

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "open", label: "Open" },
  { value: "investigating", label: "Investigating" },
  { value: "resolved", label: "Resolved" },
  { value: "dismissed", label: "Dismissed" },
] as const;

const statusColors: Record<string, string> = {
  open: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  investigating:
    "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  resolved:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  dismissed:
    "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

export function InfringementListPage() {
  const [statusFilter, setStatusFilter] = useState("");

  const params: Record<string, string | number | undefined> = {};
  if (statusFilter) params.status = statusFilter;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["infringements", params],
    queryFn: () => listInfringements(params),
  });

  const infringements = data?.results ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Infringements</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage and track content infringement reports.
          </p>
        </div>
        <Link
          to="/infringements/new"
          className={cn(
            "inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2",
            "text-sm font-medium text-primary-foreground shadow",
            "hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          )}
        >
          <Plus className="h-4 w-4" />
          Report Infringement
        </Link>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className={cn(
            "flex h-10 rounded-md border border-input bg-background px-3 py-2",
            "text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          )}
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {isLoading && <SkeletonTable />}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="font-medium text-destructive">
                Failed to load infringements
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {error instanceof Error
                  ? error.message
                  : "An unexpected error occurred."}
              </p>
            </div>
            <button
              onClick={() => refetch()}
              className={cn(
                "rounded-md border border-destructive/50 px-3 py-1.5",
                "text-sm font-medium text-destructive hover:bg-destructive/10"
              )}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && infringements.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card p-12 text-center">
          <AlertTriangle className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="font-medium text-muted-foreground">
            No infringement reports found.
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {statusFilter
              ? "Try adjusting your filter."
              : "No reports have been filed yet."}
          </p>
        </div>
      )}

      {/* Table */}
      {!isLoading && !isError && infringements.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  ID
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Date
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Reporter
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Notes
                </th>
              </tr>
            </thead>
            <tbody>
              {infringements.map((report) => (
                <tr
                  key={report.id}
                  className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-sm">
                    <Link
                      to={`/infringements/${report.id}`}
                      className="text-primary underline-offset-4 hover:underline"
                    >
                      {report.id.slice(0, 8)}...
                    </Link>
                  </td>
                  <td className="px-4 py-3">{report.created_at}</td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                        statusColors[report.status] ?? ""
                      )}
                    >
                      {report.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {report.reporter_name ?? "Anonymous"}
                  </td>
                  <td className="max-w-xs truncate px-4 py-3 text-muted-foreground">
                    {report.notes}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SkeletonTable() {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50">
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              ID
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Date
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Status
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Reporter
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Notes
            </th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 5 }).map((_, i) => (
            <tr key={i} className="border-b border-border last:border-0">
              <td className="px-4 py-3">
                <div className="h-4 w-16 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-24 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-20 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-28 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-40 animate-pulse rounded bg-muted" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
