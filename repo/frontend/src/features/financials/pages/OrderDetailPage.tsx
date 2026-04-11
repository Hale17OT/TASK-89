import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
  CreditCard,
  RotateCcw,
  AlertTriangle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getOrder } from "@/api/endpoints/financials";
import type { Payment, Refund } from "@/api/types/financial.types";
import { CountdownTimer } from "@/features/financials/components/CountdownTimer";
import { format } from "date-fns";

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

interface TransactionEntry {
  id: string;
  type: "payment" | "refund";
  amount: string;
  date: string;
  detail: string;
  isCompensating: boolean;
}

export function OrderDetailPage() {
  const { orderId } = useParams<{ orderId: string }>();

  const { data: order, isLoading, isError, error } = useQuery({
    queryKey: ["order", orderId],
    queryFn: () => getOrder(orderId!),
    enabled: !!orderId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading order...</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
        <AlertCircle className="mx-auto h-8 w-8 text-destructive" />
        <p className="mt-2 text-sm text-destructive">
          Failed to load order:{" "}
          {error instanceof Error ? error.message : "Unknown error"}
        </p>
      </div>
    );
  }

  if (!order) return null;

  // Build chronological transaction history
  const transactions: TransactionEntry[] = [
    ...order.payments.map(
      (p: Payment): TransactionEntry => ({
        id: p.id,
        type: "payment",
        amount: p.amount,
        date: p.posted_at,
        detail: p.is_compensating
          ? `Compensating entry (${p.payment_method})`
          : `${p.payment_method === "check" ? `Check #${p.check_number}` : "Cash"}`,
        isCompensating: p.is_compensating,
      })
    ),
    ...order.refunds.map(
      (r: Refund): TransactionEntry => ({
        id: r.id,
        type: "refund",
        amount: `-${r.amount}`,
        date: r.created_at,
        detail: `${r.reason} (${r.status})`,
        isCompensating: false,
      })
    ),
  ].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const hasCompensating = order.payments.some(
    (p: Payment) => p.is_compensating
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/financials"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">
          Order {order.order_number}
        </h1>
      </div>

      {/* Compensating entries banner */}
      {hasCompensating && (
        <div className="flex items-center gap-3 rounded-lg border border-amber-300 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-700 px-4 py-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
          <p className="text-sm text-amber-800 dark:text-amber-300">
            This order contains compensating entries. Original records have been
            preserved, and corrections were applied as new entries.
          </p>
        </div>
      )}

      {/* Order Summary Card */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm space-y-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">Status</p>
            <span
              className={cn(
                "inline-block rounded-full px-3 py-1 text-sm font-medium capitalize",
                STATUS_BADGE[order.status] ?? "bg-muted text-muted-foreground"
              )}
            >
              {order.status.replace("_", " ")}
            </span>
          </div>
          <div className="text-right space-y-1">
            <p className="text-sm text-muted-foreground">Total</p>
            <p className="text-2xl font-bold font-mono">
              ${parseFloat(order.total_amount).toFixed(2)}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-xs text-muted-foreground">Patient</p>
            <p className="text-sm font-medium">{order.patient_id}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Amount Paid</p>
            <p className="text-sm font-medium font-mono">
              ${parseFloat(order.amount_paid).toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Created</p>
            <p className="text-sm font-medium">
              {format(new Date(order.created_at), "MMM d, yyyy HH:mm")}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Balance Due</p>
            <p className="text-sm font-medium font-mono">
              $
              {(
                parseFloat(order.total_amount) -
                parseFloat(order.amount_paid)
              ).toFixed(2)}
            </p>
          </div>
        </div>

        {/* Countdown for open orders */}
        {order.status === "open" &&
          order.time_remaining_seconds != null &&
          order.time_remaining_seconds > 0 && (
            <div className="border-t border-border pt-4">
              <p className="mb-2 text-xs font-medium text-muted-foreground">
                Time Remaining
              </p>
              <CountdownTimer
                totalSeconds={1800}
                remainingSeconds={order.time_remaining_seconds}
              />
            </div>
          )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        {order.status === "open" && (
          <Link
            to={`/financials/${order.id}/pay`}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <CreditCard className="h-4 w-4" />
            Record Payment
          </Link>
        )}
        {order.status === "paid" && (
          <Link
            to={`/financials/${order.id}/refund`}
            className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-4 py-2 text-sm font-medium text-foreground shadow-sm hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <RotateCcw className="h-4 w-4" />
            Record Refund
          </Link>
        )}
      </div>

      {/* Line Items */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold">Line Items</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-6 py-3 text-left font-medium text-muted-foreground">
                  Description
                </th>
                <th className="px-6 py-3 text-right font-medium text-muted-foreground">
                  Qty
                </th>
                <th className="px-6 py-3 text-right font-medium text-muted-foreground">
                  Unit Price
                </th>
                <th className="px-6 py-3 text-right font-medium text-muted-foreground">
                  Total
                </th>
              </tr>
            </thead>
            <tbody>
              {order.line_items.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-border last:border-b-0"
                >
                  <td className="px-6 py-3">{item.description}</td>
                  <td className="px-6 py-3 text-right">{item.quantity}</td>
                  <td className="px-6 py-3 text-right font-mono">
                    ${parseFloat(item.unit_price).toFixed(2)}
                  </td>
                  <td className="px-6 py-3 text-right font-mono font-medium">
                    ${parseFloat(item.line_total).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction History */}
      <div className="rounded-lg border border-border bg-card shadow-sm">
        <div className="px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold">Transaction History</h2>
        </div>
        {transactions.length === 0 ? (
          <div className="px-6 py-8 text-center text-sm text-muted-foreground">
            No transactions recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="px-6 py-3 text-left font-medium text-muted-foreground">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left font-medium text-muted-foreground">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left font-medium text-muted-foreground">
                    Detail
                  </th>
                  <th className="px-6 py-3 text-right font-medium text-muted-foreground">
                    Amount
                  </th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((t) => (
                  <tr
                    key={`${t.type}-${t.id}`}
                    className={cn(
                      "border-b border-border last:border-b-0",
                      t.isCompensating && "bg-amber-50/50 dark:bg-amber-950/10"
                    )}
                  >
                    <td className="px-6 py-3 text-muted-foreground">
                      {format(new Date(t.date), "MMM d, yyyy HH:mm")}
                    </td>
                    <td className="px-6 py-3">
                      <span
                        className={cn(
                          "inline-block rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                          t.type === "payment"
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
                            : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                        )}
                      >
                        {t.type}
                      </span>
                      {t.isCompensating && (
                        <span className="ml-2 inline-block rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900 dark:text-amber-300">
                          Compensating
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-3">{t.detail}</td>
                    <td className="px-6 py-3 text-right font-mono font-medium">
                      {t.type === "refund" ? (
                        <span className="text-red-600">{t.amount}</span>
                      ) : (
                        <span className="text-green-600">
                          +${parseFloat(t.amount).toFixed(2)}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
