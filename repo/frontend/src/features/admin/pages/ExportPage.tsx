import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Download, Loader2, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import apiClient from "@/api/client";
import { SudoModeModal } from "../components/SudoModeModal";
import { AdminNav } from "../components/AdminNav";

type ExportType = "patients" | "media" | "financials";

const EXPORT_OPTIONS: { type: ExportType; label: string; description: string }[] = [
  { type: "patients", label: "Patient Records", description: "Export all active patient records (masked identifiers)" },
  { type: "media", label: "Media Assets", description: "Export media metadata including originality status and hashes" },
  { type: "financials", label: "Financial Records", description: "Export all orders, payments, and reconciliation data" },
];

async function runExport(type: ExportType): Promise<Blob> {
  const response = await apiClient.post(`export/${type}/`, { confirm: true }, { responseType: "blob" });
  return response.data as Blob;
}

export default function ExportPage() {
  const [confirmTarget, setConfirmTarget] = useState<ExportType | null>(null);
  const [sudoTarget, setSudoTarget] = useState<ExportType | null>(null);

  const exportMutation = useMutation({
    mutationFn: (type: ExportType) => runExport(type),
    onSuccess: (blob, type) => {
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `medrights-export-${type}-${new Date().toISOString().split("T")[0]}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success(`${type} export downloaded`);
    },
    onError: (err: Error) => toast.error(`Export failed: ${err.message}`),
  });

  const handleExport = (type: ExportType) => {
    setConfirmTarget(type);
  };

  const handleConfirm = () => {
    if (confirmTarget) {
      setSudoTarget(confirmTarget);
      setConfirmTarget(null);
    }
  };

  return (
    <div className="space-y-6">
      <AdminNav />
      <div>
        <h1 className="text-2xl font-bold">Bulk Export</h1>
        <p className="text-muted-foreground">Export clinic data as CSV files. Requires administrator re-authentication.</p>
      </div>

      <div className="rounded-md border border-amber-500/50 bg-amber-50 p-4 dark:bg-amber-950">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-4 w-4 text-amber-600" />
          <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
            Bulk exports require sudo-mode authentication and are fully audited.
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {EXPORT_OPTIONS.map((opt) => (
          <div key={opt.type} className="rounded-lg border bg-card p-6 shadow-sm">
            <h3 className="font-semibold">{opt.label}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{opt.description}</p>
            <button
              onClick={() => handleExport(opt.type)}
              disabled={exportMutation.isPending}
              className="mt-4 inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {exportMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Download className="h-4 w-4" />
              )}
              Export CSV
            </button>
          </div>
        ))}
      </div>

      {/* Confirmation dialog */}
      {confirmTarget !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
            <h2 className="mb-2 text-lg font-semibold">Confirm Export</h2>
            <p className="mb-4 text-sm text-muted-foreground">
              Are you sure you want to export {confirmTarget}? This action is audited.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setConfirmTarget(null)}
                className="rounded-md border px-4 py-2 text-sm"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
              >
                Continue
              </button>
            </div>
          </div>
        </div>
      )}

      {sudoTarget !== null && (
        <SudoModeModal
          open={true}
          actionClass="bulk_export"
          onAuthenticated={() => {
            exportMutation.mutate(sudoTarget);
            setSudoTarget(null);
          }}
          onClose={() => setSudoTarget(null)}
        />
      )}
    </div>
  );
}
