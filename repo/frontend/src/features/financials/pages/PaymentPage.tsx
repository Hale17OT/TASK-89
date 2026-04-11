import { useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, ArrowLeft, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { getOrder, recordPayment } from "@/api/endpoints/financials";
import { format } from "date-fns";

const paymentSchema = z
  .object({
    payment_method: z.enum(["cash", "check"]),
    amount: z.coerce.number().min(0.01, "Amount must be greater than 0"),
    check_number: z.string().optional(),
  })
  .refine(
    (data) =>
      data.payment_method !== "check" ||
      (data.check_number && data.check_number.trim().length > 0),
    { message: "Check number is required for check payments", path: ["check_number"] }
  );

type PaymentFormValues = z.infer<typeof paymentSchema>;

export function PaymentPage() {
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

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<PaymentFormValues>({
    resolver: zodResolver(paymentSchema),
    defaultValues: {
      payment_method: "cash",
      amount: 0,
      check_number: "",
    },
  });

  const paymentMethod = watch("payment_method");
  const amount = watch("amount");

  const balanceDue = order
    ? parseFloat(order.total_amount) - parseFloat(order.amount_paid)
    : 0;

  const changeDue = useMemo(() => {
    if (paymentMethod !== "cash") return 0;
    const paid = Number(amount) || 0;
    return Math.max(0, paid - balanceDue);
  }, [paymentMethod, amount, balanceDue]);

  const mutation = useMutation({
    mutationFn: (data: PaymentFormValues) => {
      const idempotencyKey = crypto.randomUUID();
      return recordPayment(
        id!,
        {
          amount: data.amount,
          method: data.payment_method,
          check_number:
            data.payment_method === "check" ? data.check_number : undefined,
        },
        idempotencyKey
      );
    },
    onSuccess: () => {
      toast.success("Payment recorded successfully");
      queryClient.invalidateQueries({ queryKey: ["order", id] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      navigate(`/financials/${id}`);
    },
    onError: (err: Error) => {
      toast.error(`Failed to record payment: ${err.message}`);
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
        <h1 className="text-3xl font-bold tracking-tight">Record Payment</h1>
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
            <p className="text-xs text-muted-foreground">Paid</p>
            <p className="text-sm font-medium font-mono">
              ${parseFloat(order.amount_paid).toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Balance Due</p>
            <p className="text-sm font-bold font-mono text-primary">
              ${balanceDue.toFixed(2)}
            </p>
          </div>
        </div>
      </div>

      {/* Payment Form */}
      <form
        onSubmit={handleSubmit((data) => mutation.mutate(data))}
        className="space-y-6"
      >
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm space-y-6">
          {/* Payment Method */}
          <fieldset>
            <legend className="text-sm font-medium mb-3">
              Payment Method
            </legend>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  value="cash"
                  {...register("payment_method")}
                  className="h-4 w-4 border-border text-primary focus:ring-ring"
                />
                <span className="text-sm">Cash</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  value="check"
                  {...register("payment_method")}
                  className="h-4 w-4 border-border text-primary focus:ring-ring"
                />
                <span className="text-sm">Check</span>
              </label>
            </div>
          </fieldset>

          {/* Amount */}
          <div>
            <label
              htmlFor="amount"
              className="block text-sm font-medium mb-1.5"
            >
              Amount ($)
            </label>
            <input
              id="amount"
              type="number"
              step="0.01"
              min={0}
              {...register("amount")}
              className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm font-mono ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            {errors.amount && (
              <p className="mt-1 text-sm text-destructive">
                {errors.amount.message}
              </p>
            )}
          </div>

          {/* Check Number (conditional) */}
          {paymentMethod === "check" && (
            <div>
              <label
                htmlFor="check_number"
                className="block text-sm font-medium mb-1.5"
              >
                Check Number
              </label>
              <input
                id="check_number"
                type="text"
                {...register("check_number")}
                className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              {errors.check_number && (
                <p className="mt-1 text-sm text-destructive">
                  {errors.check_number.message}
                </p>
              )}
            </div>
          )}

          {/* Change Due (cash only) */}
          {paymentMethod === "cash" && changeDue > 0 && (
            <div className="rounded-md border border-green-300 bg-green-50 dark:bg-green-950/20 dark:border-green-700 px-4 py-3">
              <p className="text-sm text-green-800 dark:text-green-300">
                Change due:{" "}
                <span className="font-bold font-mono">
                  ${changeDue.toFixed(2)}
                </span>
              </p>
            </div>
          )}
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
            Record Payment
          </button>
        </div>
      </form>
    </div>
  );
}
