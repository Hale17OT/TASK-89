import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  AlertCircle,
  Loader2,
  X,
  CheckCircle,
  Search,
  XCircle,
  Clock,
} from "lucide-react";
import { getInfringement, updateInfringement } from "@/api/endpoints/media";
import type { InfringementReport } from "@/api/types/media.types";
import { cn } from "@/lib/utils";

type TransitionAction = "investigating" | "resolved" | "dismissed";

const statusColors: Record<string, string> = {
  open: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
  investigating:
    "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  resolved:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  dismissed:
    "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
};

const statusIcons: Record<string, React.ElementType> = {
  open: Clock,
  investigating: Search,
  resolved: CheckCircle,
  dismissed: XCircle,
};

const ALLOWED_TRANSITIONS: Record<string, TransitionAction[]> = {
  open: ["investigating"],
  investigating: ["resolved", "dismissed"],
};

export function DisputeDetailPage() {
  const { reportId: id } = useParams<{ reportId: string }>();
  const queryClient = useQueryClient();
  const [transitionDialog, setTransitionDialog] = useState<TransitionAction | null>(null);
  const [transitionNotes, setTransitionNotes] = useState("");

  const { data: report, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["infringement", id],
    queryFn: () => getInfringement(id!),
    enabled: !!id,
  });

  const transitionMutation = useMutation({
    mutationFn: (data: { status: TransitionAction; notes: string }) =>
      updateInfringement(id!, { status: data.status, notes: data.notes }),
    onSuccess: () => {
      toast.success("Status updated successfully");
      setTransitionDialog(null);
      setTransitionNotes("");
      queryClient.invalidateQueries({ queryKey: ["infringement", id] });
    },
    onError: () => {
      toast.error("Failed to update status");
    },
  });

  if (isLoading) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <div className="flex items-center gap-4">
          <div className="h-9 w-9 animate-pulse rounded-md bg-muted" />
          <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
        <div className="h-32 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-3xl space-y-6">
        <Link
          to="/infringements"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Infringements
        </Link>
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="font-medium text-destructive">
                Failed to load infringement report
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
      </div>
    );
  }

  if (!report) return null;

  const allowedTransitions = ALLOWED_TRANSITIONS[report.status] ?? [];
  const StatusIcon = statusIcons[report.status] ?? Clock;

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/infringements"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">
            Infringement Report
          </h1>
          <p className="mt-1 font-mono text-sm text-muted-foreground">
            {report.id}
          </p>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium capitalize",
            statusColors[report.status] ?? ""
          )}
        >
          <StatusIcon className="h-3.5 w-3.5" />
          {report.status}
        </span>
      </div>

      {/* Report Summary Card */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <h2 className="font-semibold">Report Details</h2>
        </div>
        <div className="grid gap-px sm:grid-cols-2">
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <span className="text-sm text-muted-foreground">Status</span>
            <span className="text-sm font-medium capitalize">
              {report.status}
            </span>
          </div>
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <span className="text-sm text-muted-foreground">Created</span>
            <span className="text-sm font-medium">{report.created_at}</span>
          </div>
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <span className="text-sm text-muted-foreground">Reporter</span>
            <span className="text-sm font-medium">
              {report.reporter_name ?? "Anonymous"}
            </span>
          </div>
          {report.reference && (
            <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
              <span className="text-sm text-muted-foreground">
                Reference
              </span>
              {report.reference.startsWith("http://") || report.reference.startsWith("https://") ? (
                <a
                  href={report.reference}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                >
                  View
                </a>
              ) : (
                <span className="text-sm font-medium">
                  {report.reference}
                </span>
              )}
            </div>
          )}
        </div>
        <div className="border-t border-border px-4 py-3">
          <h3 className="mb-1 text-sm font-medium text-muted-foreground">
            Notes
          </h3>
          <p className="whitespace-pre-wrap text-sm">{report.notes}</p>
        </div>
      </div>

      {/* Dispute Timeline */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <h2 className="font-semibold">Timeline</h2>
        </div>
        <div className="p-4">
          <div className="relative space-y-4">
            {/* Opened event */}
            <TimelineEvent
              icon={Clock}
              label="Opened"
              timestamp={report.opened_at ?? report.created_at}
              status="open"
            />
            {/* Under Investigation */}
            {report.investigating_at && (
              <TimelineEvent
                icon={Search}
                label="Under Investigation"
                timestamp={report.investigating_at}
                status="investigating"
              />
            )}
            {/* Resolved */}
            {report.resolved_at && (
              <TimelineEvent
                icon={CheckCircle}
                label="Resolved"
                timestamp={report.resolved_at}
                status="resolved"
              />
            )}
            {/* Dismissed */}
            {report.dismissed_at && (
              <TimelineEvent
                icon={XCircle}
                label="Dismissed"
                timestamp={report.dismissed_at}
                status="dismissed"
              />
            )}
          </div>
        </div>
      </div>

      {/* Transition Actions */}
      {allowedTransitions.length > 0 && (
        <div className="flex items-center gap-3">
          {allowedTransitions.map((action) => (
            <button
              key={action}
              onClick={() => setTransitionDialog(action)}
              className={cn(
                "inline-flex items-center gap-2 rounded-md px-4 py-2",
                "text-sm font-medium shadow",
                action === "resolved"
                  ? "bg-green-600 text-white hover:bg-green-700"
                  : action === "investigating"
                  ? "bg-blue-600 text-white hover:bg-blue-700"
                  : "border border-border bg-background hover:bg-accent"
              )}
            >
              {action === "investigating" && <Search className="h-4 w-4" />}
              {action === "resolved" && <CheckCircle className="h-4 w-4" />}
              {action === "dismissed" && <XCircle className="h-4 w-4" />}
              {action.charAt(0).toUpperCase() + action.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* Transition Confirmation Dialog */}
      {transitionDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() =>
              !transitionMutation.isPending && setTransitionDialog(null)
            }
          />
          <div className="relative z-50 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <div className="flex items-start justify-between">
              <h2 className="text-lg font-semibold capitalize">
                {transitionDialog} Report
              </h2>
              <button
                onClick={() => setTransitionDialog(null)}
                disabled={transitionMutation.isPending}
                className="rounded-md p-1 hover:bg-accent"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Are you sure you want to change the status to{" "}
              <strong className="capitalize">{transitionDialog}</strong>?
            </p>

            <div className="mt-4 space-y-2">
              <label className="text-sm font-medium">
                Notes
                <span className="ml-1 text-destructive">*</span>
              </label>
              <textarea
                value={transitionNotes}
                onChange={(e) => setTransitionNotes(e.target.value)}
                placeholder="Add notes about this status change..."
                rows={3}
                className={cn(
                  "flex w-full rounded-md border border-input bg-background px-3 py-2",
                  "text-sm placeholder:text-muted-foreground resize-none",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                )}
                disabled={transitionMutation.isPending}
              />
            </div>

            <div className="mt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setTransitionDialog(null)}
                disabled={transitionMutation.isPending}
                className={cn(
                  "inline-flex items-center justify-center rounded-md border border-border px-4 py-2",
                  "text-sm font-medium hover:bg-accent",
                  "disabled:pointer-events-none disabled:opacity-50"
                )}
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  transitionMutation.mutate({
                    status: transitionDialog,
                    notes: transitionNotes,
                  })
                }
                disabled={
                  transitionMutation.isPending ||
                  transitionNotes.trim().length === 0
                }
                className={cn(
                  "inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2",
                  "text-sm font-medium text-primary-foreground shadow",
                  "hover:bg-primary/90",
                  "disabled:pointer-events-none disabled:opacity-50"
                )}
              >
                {transitionMutation.isPending && (
                  <Loader2 className="h-4 w-4 animate-spin" />
                )}
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function TimelineEvent({
  icon: Icon,
  label,
  timestamp,
  status,
}: {
  icon: React.ElementType;
  label: string;
  timestamp: string;
  status: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          status === "open"
            ? "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"
            : status === "investigating"
            ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
            : status === "resolved"
            ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
            : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
        )}
      >
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 pt-0.5">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{timestamp}</p>
      </div>
    </div>
  );
}
