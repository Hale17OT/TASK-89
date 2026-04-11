import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, Loader2, AlertCircle, Inbox } from "lucide-react";
import { cn } from "@/lib/utils";
import { listSubscriptions } from "@/api/endpoints/reports";
import type { ReportSubscription } from "@/api/types/report.types";

const SCHEDULE_BADGE: Record<string, string> = {
  daily: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  weekly: "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
};

const FORMAT_BADGE: Record<string, string> = {
  pdf: "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300",
  excel: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  image: "bg-amber-100 text-amber-700 dark:bg-amber-900 dark:text-amber-300",
};

export function SubscriptionListPage() {
  const {
    data: response,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["subscriptions"],
    queryFn: listSubscriptions,
  });

  const subscriptions = response?.results ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">
          Report Subscriptions
        </h1>
        <div className="flex items-center gap-2">
          <Link
            to="/reports/outbox"
            className="inline-flex items-center gap-2 rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent"
          >
            <Inbox className="h-4 w-4" />
            View Outbox
          </Link>
          <Link
            to="/reports/new"
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Plus className="h-4 w-4" />
            New Subscription
          </Link>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">
            Loading subscriptions...
          </span>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-destructive" />
          <p className="mt-2 text-sm text-destructive">
            Failed to load subscriptions:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* Empty */}
      {!isLoading &&
        !isError &&
        subscriptions &&
        subscriptions.length === 0 && (
          <div className="rounded-lg border border-border bg-card p-12 text-center">
            <Inbox className="mx-auto h-10 w-10 text-muted-foreground" />
            <p className="mt-3 text-muted-foreground">
              No subscriptions found.
            </p>
          </div>
        )}

      {/* Grid */}
      {!isLoading &&
        !isError &&
        subscriptions &&
        subscriptions.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {subscriptions.map((sub: ReportSubscription) => (
              <div
                key={sub.id}
                className="rounded-lg border border-border bg-card p-5 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="flex items-start justify-between">
                  <h3 className="text-sm font-semibold truncate pr-2">
                    {sub.name}
                  </h3>
                  <span
                    className={cn(
                      "shrink-0 inline-block rounded-full px-2 py-0.5 text-xs font-medium",
                      sub.is_active
                        ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
                        : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                    )}
                  >
                    {sub.is_active ? "Active" : "Paused"}
                  </span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {sub.report_type}
                </p>
                <div className="mt-3 flex items-center gap-2">
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                      SCHEDULE_BADGE[sub.schedule] ??
                        "bg-muted text-muted-foreground"
                    )}
                  >
                    {sub.schedule}
                  </span>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-xs font-medium uppercase",
                      FORMAT_BADGE[sub.output_format] ??
                        "bg-muted text-muted-foreground"
                    )}
                  >
                    {sub.output_format}
                  </span>
                </div>
                <p className="mt-2 text-xs text-muted-foreground">
                  Run time: {sub.run_time}
                </p>
              </div>
            ))}
          </div>
        )}
    </div>
  );
}
