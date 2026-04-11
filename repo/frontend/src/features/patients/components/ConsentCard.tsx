import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, X, FileText, AlertTriangle } from "lucide-react";
import { revokeConsent } from "@/api/endpoints/consents";
import type { Consent } from "@/api/types/consent.types";
import { cn } from "@/lib/utils";

interface ConsentCardProps {
  consent: Consent;
  patientId: string;
}

const statusStyles: Record<Consent["status"], string> = {
  active:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  expired:
    "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  revoked: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

export function ConsentCard({ consent, patientId }: ConsentCardProps) {
  const [physicalAckDialogOpen, setPhysicalAckDialogOpen] = useState(false);
  const [physicalAcknowledged, setPhysicalAcknowledged] = useState(false);
  const queryClient = useQueryClient();

  const revokeMutation = useMutation({
    mutationFn: (payload: {
      reason?: string;
      physical_copy_warning_acknowledged?: boolean;
    }) =>
      revokeConsent(patientId, consent.id, {
        reason: payload.reason,
        physical_copy_warning_acknowledged:
          payload.physical_copy_warning_acknowledged,
      }),
    onSuccess: () => {
      toast.success("Consent revoked successfully");
      setPhysicalAckDialogOpen(false);
      setPhysicalAcknowledged(false);
      queryClient.invalidateQueries({
        queryKey: ["consents", patientId],
      });
    },
    onError: () => {
      toast.error("Failed to revoke consent");
    },
  });

  const handleOneClickRevoke = () => {
    if (consent.physical_copy_on_file) {
      // Physical copy requires acknowledgment before revoking
      setPhysicalAckDialogOpen(true);
    } else {
      // One-click: revoke immediately
      revokeMutation.mutate({});
    }
  };

  return (
    <>
      <div className="rounded-lg border border-border bg-card p-4 space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <h3 className="font-medium">{consent.purpose}</h3>
          </div>
          <span
            className={cn(
              "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
              statusStyles[consent.status]
            )}
          >
            {consent.status}
          </span>
        </div>

        <div className="grid gap-2 text-sm sm:grid-cols-2">
          <div>
            <span className="text-muted-foreground">Effective: </span>
            <span>{consent.effective_date}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Expires: </span>
            <span>{consent.expiration_date ?? "No expiration"}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Granted: </span>
            <span>{consent.granted_at}</span>
          </div>
          {consent.is_revoked && consent.revoked_at && (
            <div>
              <span className="text-muted-foreground">Revoked: </span>
              <span>{consent.revoked_at}</span>
            </div>
          )}
        </div>

        {consent.physical_copy_on_file && (
          <div className="flex items-center gap-2 rounded-md border border-yellow-200 bg-yellow-50 px-3 py-2 dark:border-yellow-900 dark:bg-yellow-950/50">
            <AlertTriangle className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
            <span className="text-xs text-yellow-800 dark:text-yellow-200">
              Physical copy on file. Ensure physical copies are destroyed upon
              revocation.
            </span>
          </div>
        )}

        {consent.status === "active" && (
          <div className="flex justify-end">
            <button
              onClick={handleOneClickRevoke}
              disabled={revokeMutation.isPending}
              className={cn(
                "inline-flex items-center gap-2 rounded-md border border-destructive/50 px-3 py-1.5",
                "text-sm font-medium text-destructive",
                "hover:bg-destructive/10",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              {revokeMutation.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Revoke
            </button>
          </div>
        )}
      </div>

      {/* Physical copy acknowledgment dialog — only for consents with physical copies */}
      {physicalAckDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="fixed inset-0 bg-black/50"
            onClick={() =>
              !revokeMutation.isPending && setPhysicalAckDialogOpen(false)
            }
          />
          <div className="relative z-50 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <div className="flex items-start justify-between">
              <h2 className="text-lg font-semibold">Confirm Revocation</h2>
              <button
                onClick={() => setPhysicalAckDialogOpen(false)}
                disabled={revokeMutation.isPending}
                className="rounded-md p-1 hover:bg-accent"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              A physical copy of this consent is on file. Please confirm that
              physical copies will be destroyed.
            </p>

            <div className="mt-4">
              <label className="flex items-start gap-2">
                <input
                  type="checkbox"
                  checked={physicalAcknowledged}
                  onChange={(e) => setPhysicalAcknowledged(e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-input"
                  disabled={revokeMutation.isPending}
                />
                <span className="text-sm text-muted-foreground">
                  I acknowledge that physical copies of this consent exist and
                  must be destroyed.
                </span>
              </label>
            </div>

            <div className="mt-4 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setPhysicalAckDialogOpen(false)}
                disabled={revokeMutation.isPending}
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
                  revokeMutation.mutate({
                    physical_copy_warning_acknowledged: true,
                  })
                }
                disabled={revokeMutation.isPending || !physicalAcknowledged}
                className={cn(
                  "inline-flex items-center justify-center gap-2 rounded-md bg-destructive px-4 py-2",
                  "text-sm font-medium text-destructive-foreground shadow",
                  "hover:bg-destructive/90",
                  "disabled:pointer-events-none disabled:opacity-50"
                )}
              >
                {revokeMutation.isPending && (
                  <Loader2 className="h-4 w-4 animate-spin" />
                )}
                Revoke Consent
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
