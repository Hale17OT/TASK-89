import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, Loader2, AlertCircle, Inbox } from "lucide-react";
import { cn } from "@/lib/utils";
import { listOrders } from "@/api/endpoints/financials";
import type { Order } from "@/api/types/financial.types";
import { CountdownTimer } from "@/features/financials/components/CountdownTimer";
import { format } from "date-fns";

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "open", label: "Open" },
  { value: "paid", label: "Paid" },
  { value: "partial", label: "Partial" },
  { value: "closed_unpaid", label: "Closed Unpaid" },
  { value: "voided", label: "Voided" },
  { value: "refunded", label: "Refunded" },
] as const;

const STATUS_BADGE: Record<string, string> = {
  open: "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300",
  paid: "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300",
  partial:
    "bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300",
  closed_unpaid: "bg-zinc-100 text-zinc-800 dark:bg-zinc-800 dark:text-zinc-300",
  voided: "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300",
  refunded:
    "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300",
};

export function OrderListPage() {
  const [statusFilter, setStatusFilter] = useState("");

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["orders", statusFilter],
    queryFn: () =>
      listOrders(statusFilter ? { status: statusFilter } : undefined),
  });

  const orders = data?.results ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Orders</h1>
        <Link
          to="/financials/new"
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Plus className="h-4 w-4" />
          Create Order
        </Link>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-4">
        <label
          htmlFor="status-filter"
          className="text-sm font-medium text-foreground"
        >
          Status:
        </label>
        <select
          id="status-filter"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">Loading orders...</span>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-destructive" />
          <p className="mt-2 text-sm text-destructive">
            Failed to load orders:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && orders.length === 0 && (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <Inbox className="mx-auto h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-muted-foreground">No orders found.</p>
        </div>
      )}

      {/* Table */}
      {!isLoading && !isError && orders.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Order #
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Date
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Patient
                </th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                  Amount
                </th>
                <th className="px-4 py-3 text-center font-medium text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Time Remaining
                </th>
              </tr>
            </thead>
            <tbody>
              {orders.map((order: Order) => (
                <tr
                  key={order.id}
                  className="border-b border-border last:border-b-0 hover:bg-muted/30 transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link
                      to={`/financials/${order.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {order.order_number}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {format(new Date(order.created_at), "MMM d, yyyy HH:mm")}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {order.patient_id}
                  </td>
                  <td className="px-4 py-3 text-right font-mono">
                    ${parseFloat(order.total_amount).toFixed(2)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <span
                      className={cn(
                        "inline-block rounded-full px-2.5 py-0.5 text-xs font-medium capitalize",
                        STATUS_BADGE[order.status] ?? "bg-muted text-muted-foreground"
                      )}
                    >
                      {order.status.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 min-w-[180px]">
                    {order.status === "open" &&
                    order.time_remaining_seconds != null &&
                    order.time_remaining_seconds > 0 ? (
                      <CountdownTimer
                        totalSeconds={1800}
                        remainingSeconds={order.time_remaining_seconds}
                      />
                    ) : order.status === "open" ? (
                      <span className="text-xs text-red-500 font-medium">
                        Expired
                      </span>
                    ) : (
                      <span className="text-xs text-muted-foreground">--</span>
                    )}
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
