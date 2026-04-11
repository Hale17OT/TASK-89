import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, X, ShieldAlert } from "lucide-react";
import { breakGlass } from "@/api/endpoints/patients";
import type { BreakGlassResponse, BreakGlassPayload } from "@/api/types/patient.types";
import { cn } from "@/lib/utils";

const JUSTIFICATION_CATEGORIES = [
  { value: "emergency", label: "Emergency" },
  { value: "treatment", label: "Treatment" },
  { value: "legal", label: "Legal" },
  { value: "admin", label: "Administrative" },
  { value: "other", label: "Other" },
] as const;

const breakGlassSchema = z.object({
  justification_category: z.string().min(1, "Category is required"),
  justification: z
    .string()
    .min(20, "Justification must be at least 20 characters"),
});

type BreakGlassFormData = z.infer<typeof breakGlassSchema>;

interface BreakGlassModalProps {
  patientId: string;
  open: boolean;
  onClose: () => void;
  onSuccess: (data: BreakGlassResponse) => void;
}

export function BreakGlassModal({
  patientId,
  open,
  onClose,
  onSuccess,
}: BreakGlassModalProps) {
  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<BreakGlassFormData>({
    resolver: zodResolver(breakGlassSchema),
    defaultValues: {
      justification_category: "",
      justification: "",
    },
  });

  const justificationValue = watch("justification");
  const charCount = justificationValue?.length ?? 0;

  const mutation = useMutation({
    mutationFn: (payload: BreakGlassPayload) =>
      breakGlass(patientId, payload),
    onSuccess: (data) => {
      toast.success("Break-glass access granted. This action has been logged.");
      reset();
      onSuccess(data);
    },
    onError: () => {
      toast.error("Failed to perform break-glass access.");
    },
  });

  const onSubmit = (data: BreakGlassFormData) => {
    mutation.mutate(data);
  };

  const handleClose = () => {
    if (!mutation.isPending) {
      reset();
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50"
        onClick={handleClose}
      />

      {/* Dialog */}
      <div className="relative z-50 w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-lg">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-destructive/10">
              <ShieldAlert className="h-5 w-5 text-destructive" />
            </div>
            <div>
              <h2 className="text-lg font-semibold">Break-Glass Access</h2>
              <p className="text-sm text-muted-foreground">
                This action will be audited and logged.
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={mutation.isPending}
            className="rounded-md p-1 hover:bg-accent"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Warning */}
        <div className="mt-4 rounded-md border border-yellow-200 bg-yellow-50 p-3 dark:border-yellow-900 dark:bg-yellow-950/50">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            You are requesting access to protected health information. A
            justification is required and this access will be recorded in the
            audit log.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Justification Category
              <span className="ml-1 text-destructive">*</span>
            </label>
            <select
              {...register("justification_category")}
              className={cn(
                "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
                "text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:cursor-not-allowed disabled:opacity-50"
              )}
              disabled={mutation.isPending}
            >
              <option value="">Select a category</option>
              {JUSTIFICATION_CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
            {errors.justification_category && (
              <p className="text-sm text-destructive">
                {errors.justification_category.message}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">
              Justification
              <span className="ml-1 text-destructive">*</span>
            </label>
            <textarea
              {...register("justification")}
              placeholder="Describe why you need access to this patient's unmasked data..."
              rows={4}
              className={cn(
                "flex w-full rounded-md border border-input bg-background px-3 py-2",
                "text-sm placeholder:text-muted-foreground resize-none",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:cursor-not-allowed disabled:opacity-50"
              )}
              disabled={mutation.isPending}
            />
            <div className="flex justify-between">
              {errors.justification ? (
                <p className="text-sm text-destructive">
                  {errors.justification.message}
                </p>
              ) : (
                <span />
              )}
              <span
                className={cn(
                  "text-xs",
                  charCount < 20
                    ? "text-muted-foreground"
                    : "text-green-600 dark:text-green-400"
                )}
              >
                {charCount}/20 min
              </span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={handleClose}
              disabled={mutation.isPending}
              className={cn(
                "inline-flex items-center justify-center rounded-md border border-border px-4 py-2",
                "text-sm font-medium hover:bg-accent",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className={cn(
                "inline-flex items-center justify-center gap-2 rounded-md bg-destructive px-4 py-2",
                "text-sm font-medium text-destructive-foreground shadow",
                "hover:bg-destructive/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              {mutation.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Confirm Access
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
