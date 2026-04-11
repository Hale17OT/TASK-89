import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, ArrowLeft, AlertCircle, Info } from "lucide-react";
import { toast } from "sonner";
import { getOrder, createRefund } from "@/api/endpoints/financials";

const refundSchema = z.object({
  amount: z.coerce.number().min(0.01, "Amount must be greater than 0"),
  reason: z.string().min(1, "Reason is required"),
  original_payment_id: z.string().min(1, "You must select a payment to refund"),
});

type RefundFormValues = z.infer<typeof refundSchema>;

export function RefundPage() {
  const { orderId: id } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    data: order,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["order", id],
    queryFn: () => getOrder(id!),
    enabled: !!id,
  });

  const maxRefund = order ? parseFloat(order.amount_paid) : 0;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RefundFormValues>({
    resolver: zodResolver(refundSchema),
    defaultValues: {
      amount: 0,
      reason: "",
      original_payment_id: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: RefundFormValues) => {
      if (data.amount > maxRefund) {
        return Promise.reject(
          new Error(`Amount cannot exceed $${maxRefund.toFixed(2)}`)
        );
      }
      return createRefund(id!, {
        amount: data.amount,
        reason: data.reason,
        original_payment_id: data.original_payment_id,
      });
    },
    onSuccess: () => {
      toast.success("Refund request submitted successfully");
      queryClient.invalidateQueries({ queryKey: ["order", id] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      navigate(`/financials/${id}`);
    },
    onError: (err: Error) => {
      toast.error(`Failed to submit refund: ${err.message}`);
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Loading order...</span>
      </div>
    );
  }

  if (isError || !order) {
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to={`/financials/${id}`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Record Refund</h1>
      </div>

      {/* Banner */}
      <div className="flex items-center gap-3 rounded-lg border border-blue-300 bg-blue-50 dark:bg-blue-950/20 dark:border-blue-700 px-4 py-3">
        <Info className="h-5 w-5 text-blue-600 shrink-0" />
        <p className="text-sm text-blue-800 dark:text-blue-300">
          Refunds create compensating entries. Original records are never
          deleted.
        </p>
      </div>

      {/* Order Summary (read-only) */}
      <div className="rounded-lg border border-border bg-muted/50 p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">
          Order Summary
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-xs text-muted-foreground">Order</p>
            <p className="text-sm font-medium">{order.order_number}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total</p>
            <p className="text-sm font-medium font-mono">
              ${parseFloat(order.total_amount).toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Amount Paid</p>
            <p className="text-sm font-medium font-mono">
              ${parseFloat(order.amount_paid).toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Max Refund</p>
            <p className="text-sm font-bold font-mono text-primary">
              ${maxRefund.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Refund Form */}
      <form
        onSubmit={handleSubmit((data) => mutation.mutate(data))}
        className="space-y-6"
      >
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm space-y-6">
          {/* Payment to Refund */}
          <div>
            <label
              htmlFor="original_payment_id"
              className="block text-sm font-medium mb-1.5"
            >
              Payment to Refund
            </label>
            <select
              id="original_payment_id"
              {...register("original_payment_id")}
              className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Select a payment...</option>
              {order.payments &&
                order.payments.map((payment) => (
                  <option key={payment.id} value={payment.id}>
                    ${parseFloat(payment.amount).toFixed(2)} - {payment.payment_method} (
                    {payment.posted_at
                      ? new Date(payment.posted_at).toLocaleDateString()
                      : "N/A"}
                    )
                  </option>
                ))}
            </select>
            {errors.original_payment_id && (
              <p className="mt-1 text-sm text-destructive">
                {errors.original_payment_id.message}
              </p>
            )}
          </div>

          {/* Amount */}
          <div>
            <label
              htmlFor="amount"
              className="block text-sm font-medium mb-1.5"
            >
              Refund Amount ($)
            </label>
            <input
              id="amount"
              type="number"
              step="0.01"
              min={0}
              max={maxRefund}
              {...register("amount")}
              className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            {errors.amount && (
              <p className="mt-1 text-sm text-destructive">
                {errors.amount.message}
              </p>
            )}
            <p className="mt-1 text-xs text-muted-foreground">
              Maximum: ${maxRefund.toFixed(2)}
            </p>
          </div>

          {/* Reason */}
          <div>
            <label
              htmlFor="reason"
              className="block text-sm font-medium mb-1.5"
            >
              Reason
            </label>
            <textarea
              id="reason"
              rows={4}
              {...register("reason")}
              placeholder="Describe the reason for this refund..."
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
            />
            {errors.reason && (
              <p className="mt-1 text-sm text-destructive">
                {errors.reason.message}
              </p>
            )}
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutation.isPending && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
            Submit Refund
          </button>
        </div>
      </form>
    </div>
  );
}
