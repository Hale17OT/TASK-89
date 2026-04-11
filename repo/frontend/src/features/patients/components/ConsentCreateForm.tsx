import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, X } from "lucide-react";
import { createConsent } from "@/api/endpoints/consents";
import type {
  CreateConsentPayload,
  ConsentScopePayload,
} from "@/api/types/consent.types";
import { cn } from "@/lib/utils";

const CONSENT_PURPOSES = [
  "Treatment",
  "Payment",
  "Healthcare Operations",
  "Research",
  "Marketing",
  "Fundraising",
  "Disclosure to Family",
  "Directory Listing",
  "Other",
] as const;

const SCOPE_OPTIONS: {
  label: string;
  scope_type: ConsentScopePayload["scope_type"];
  scope_value: string;
}[] = [
  { label: "Media Capture & Storage", scope_type: "media_use", scope_value: "capture_storage" },
  { label: "Internal Clinical Use", scope_type: "media_use", scope_value: "internal_clinical" },
  { label: "Educational Use", scope_type: "media_use", scope_value: "educational" },
  { label: "Marketing Use", scope_type: "media_use", scope_value: "marketing" },
  { label: "Research Use", scope_type: "action", scope_value: "research" },
  { label: "Data Sharing with Third Party", scope_type: "action", scope_value: "data_sharing" },
];

const consentSchema = z
  .object({
    purpose: z.string().min(1, "Purpose is required"),
    effective_date: z.string().min(1, "Effective date is required"),
    expiration_date: z.string().optional(),
    physical_copy_on_file: z.boolean(),
  })
  .refine(
    (data) => {
      if (data.expiration_date && data.effective_date) {
        return new Date(data.expiration_date) > new Date(data.effective_date);
      }
      return true;
    },
    {
      message: "Expiration date must be after effective date",
      path: ["expiration_date"],
    }
  );

type ConsentFormData = z.infer<typeof consentSchema>;

interface ConsentCreateFormProps {
  patientId: string;
  open: boolean;
  onClose: () => void;
}

export function ConsentCreateForm({
  patientId,
  open,
  onClose,
}: ConsentCreateFormProps) {
  const queryClient = useQueryClient();
  const [selectedScopes, setSelectedScopes] = useState<Set<number>>(new Set());

  const toggleScope = (index: number) => {
    setSelectedScopes((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ConsentFormData>({
    resolver: zodResolver(consentSchema),
    defaultValues: {
      purpose: "",
      effective_date: "",
      expiration_date: "",
      physical_copy_on_file: false,
    },
  });

  const mutation = useMutation({
    mutationFn: (data: CreateConsentPayload) =>
      createConsent(patientId, data),
    onSuccess: () => {
      toast.success("Consent created successfully");
      reset();
      setSelectedScopes(new Set());
      onClose();
      queryClient.invalidateQueries({
        queryKey: ["consents", patientId],
      });
    },
    onError: () => {
      toast.error("Failed to create consent");
    },
  });

  const onSubmit = (data: ConsentFormData) => {
    const scopes: ConsentScopePayload[] = Array.from(selectedScopes).map(
      (i) => ({
        scope_type: SCOPE_OPTIONS[i].scope_type,
        scope_value: SCOPE_OPTIONS[i].scope_value,
      })
    );

    const payload: CreateConsentPayload = {
      purpose: data.purpose,
      effective_date: data.effective_date,
      physical_copy_on_file: data.physical_copy_on_file,
      ...(data.expiration_date ? { expiration_date: data.expiration_date } : {}),
      ...(scopes.length > 0 ? { scopes } : {}),
    };
    mutation.mutate(payload);
  };

  const handleClose = () => {
    if (!mutation.isPending) {
      reset();
      setSelectedScopes(new Set());
      onClose();
    }
  };

  if (!open) return null;

  const inputCn = cn(
    "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
    "text-sm placeholder:text-muted-foreground",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    "disabled:cursor-not-allowed disabled:opacity-50"
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/50" onClick={handleClose} />
      <div className="relative z-50 w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-lg">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">Create Consent</h2>
            <p className="text-sm text-muted-foreground">
              Record a new consent for this patient.
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={mutation.isPending}
            className="rounded-md p-1 hover:bg-accent"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">
              Purpose
              <span className="ml-1 text-destructive">*</span>
            </label>
            <select
              {...register("purpose")}
              className={inputCn}
              disabled={mutation.isPending}
            >
              <option value="">Select purpose</option>
              {CONSENT_PURPOSES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
            {errors.purpose && (
              <p className="text-sm text-destructive">
                {errors.purpose.message}
              </p>
            )}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium">
                Effective Date
                <span className="ml-1 text-destructive">*</span>
              </label>
              <input
                type="date"
                {...register("effective_date")}
                className={inputCn}
                disabled={mutation.isPending}
              />
              {errors.effective_date && (
                <p className="text-sm text-destructive">
                  {errors.effective_date.message}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Expiration Date</label>
              <input
                type="date"
                {...register("expiration_date")}
                className={inputCn}
                disabled={mutation.isPending}
              />
              {errors.expiration_date && (
                <p className="text-sm text-destructive">
                  {errors.expiration_date.message}
                </p>
              )}
            </div>
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              {...register("physical_copy_on_file")}
              className="h-4 w-4 rounded border-input"
              disabled={mutation.isPending}
            />
            <span className="text-sm">Physical copy on file</span>
          </label>

          {/* Consent Scopes */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Consent Scopes</label>
            <p className="text-xs text-muted-foreground">
              Select the scopes this consent covers.
            </p>
            <div className="grid gap-2 sm:grid-cols-2">
              {SCOPE_OPTIONS.map((option, index) => (
                <label key={index} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedScopes.has(index)}
                    onChange={() => toggleScope(index)}
                    className="h-4 w-4 rounded border-input"
                    disabled={mutation.isPending}
                  />
                  <span className="text-sm">{option.label}</span>
                </label>
              ))}
            </div>
          </div>

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
                "inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2",
                "text-sm font-medium text-primary-foreground shadow",
                "hover:bg-primary/90",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              {mutation.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Create Consent
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
