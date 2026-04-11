import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Loader2,
  AlertCircle,
  Inbox,
  Download,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getReconciliation,
  downloadReconciliation,
} from "@/api/endpoints/financials";
import { format } from "date-fns";

export function ReconciliationPage() {
  const [selectedDate, setSelectedDate] = useState(
    format(new Date(), "yyyy-MM-dd")
  );
  const [exportMenuOpen, setExportMenuOpen] = useState(false);

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["reconciliation", selectedDate],
    queryFn: () => getReconciliation(selectedDate),
    enabled: !!selectedDate,
  });

  async function handleExport(fmt: "csv" | "pdf") {
    setExportMenuOpen(false);
    try {
      const blob = await downloadReconciliation(selectedDate, fmt);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `reconciliation-${selectedDate}.${fmt}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Error handled silently - download fails gracefully
    }
  }

  const cards = data
    ? [
        {
          label: "Total Orders",
          value: data.total_orders.toString(),
          color: "text-foreground",
        },
        {
          label: "Total Payments",
          value: `$${parseFloat(data.total_payments).toFixed(2)}`,
          color: "text-green-600",
        },
        {
          label: "Total Refunds",
          value: `$${parseFloat(data.total_refunds).toFixed(2)}`,
          color: "text-red-600",
        },
        {
          label: "Net Revenue",
          value: `$${parseFloat(data.total_revenue).toFixed(2)}`,
          color: "text-primary",
        },
        {
          label: "Discrepancy",
          value: `$${parseFloat(data.discrepancy).toFixed(2)}`,
          color:
            parseFloat(data.discrepancy) !== 0
              ? "text-destructive font-bold"
              : "text-green-600",
        },
      ]
    : [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Reconciliation</h1>
        <div className="relative">
          <button
            type="button"
            onClick={() => setExportMenuOpen((prev) => !prev)}
            disabled={!data}
            className="inline-flex items-center gap-2 rounded-md border border-border bg-background px-4 py-2 text-sm font-medium shadow-sm hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download className="h-4 w-4" />
            Export
            <ChevronDown className="h-3 w-3" />
          </button>
          {exportMenuOpen && (
            <div className="absolute right-0 z-10 mt-1 w-32 rounded-md border border-border bg-popover shadow-md">
              <button
                type="button"
                onClick={() => handleExport("csv")}
                className="block w-full px-4 py-2 text-left text-sm hover:bg-accent"
              >
                CSV
              </button>
              <button
                type="button"
                onClick={() => handleExport("pdf")}
                className="block w-full px-4 py-2 text-left text-sm hover:bg-accent"
              >
                PDF
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Date Picker */}
      <div className="flex items-center gap-4">
        <label
          htmlFor="recon-date"
          className="text-sm font-medium text-foreground"
        >
          Date:
        </label>
        <input
          id="recon-date"
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        />
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          <span className="ml-3 text-muted-foreground">
            Loading reconciliation data...
          </span>
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6 text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-destructive" />
          <p className="mt-2 text-sm text-destructive">
            Failed to load reconciliation:{" "}
            {error instanceof Error ? error.message : "Unknown error"}
          </p>
        </div>
      )}

      {/* Empty */}
      {!isLoading && !isError && !data && (
        <div className="rounded-lg border border-border bg-card p-12 text-center">
          <Inbox className="mx-auto h-10 w-10 text-muted-foreground" />
          <p className="mt-3 text-muted-foreground">
            No reconciliation data for this date.
          </p>
        </div>
      )}

      {/* Summary Cards */}
      {!isLoading && !isError && data && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {cards.map((card) => (
            <div
              key={card.label}
              className="rounded-lg border border-border bg-card p-6 shadow-sm"
            >
              <p className="text-sm text-muted-foreground">{card.label}</p>
              <p className={cn("mt-1 text-2xl font-bold font-mono", card.color)}>
                {card.value}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
