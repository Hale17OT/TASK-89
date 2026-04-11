import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { listAuditEntries, verifyAuditChain } from "@/api/endpoints/admin";
import type { AuditEntry } from "@/api/types/admin.types";
import { AdminNav } from "../components/AdminNav";

export default function AuditLogPage() {
  const [filters, setFilters] = useState({ event_type: "", from_date: "", to_date: "", page: 1 });
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [verifyResult, setVerifyResult] = useState<{ verified: boolean; broken_at_id?: number; total_checked: number } | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["audit-entries", filters],
    queryFn: () => listAuditEntries(filters),
  });

  const verifyMutation = useMutation({
    mutationFn: verifyAuditChain,
    onSuccess: (res) => {
      setVerifyResult({
        verified: res.is_valid,
        broken_at_id: res.broken_at_id ?? undefined,
        total_checked: res.total_checked,
      });
      toast.success(res.is_valid ? "Chain integrity verified" : "Chain integrity BROKEN");
    },
    onError: () => toast.error("Verification failed"),
  });

  const entries: AuditEntry[] = data?.results ?? [];
  const totalCount = data?.count ?? 0;

  const eventTypes = [
    "login_success", "login_failure", "logout", "create", "update", "break_glass",
    "consent_granted", "consent_revoked", "media_upload", "payment_posted", "refund_processed",
    "user_disabled", "password_change", "sudo_mode_enter",
  ];

  return (
    <div className="space-y-6">
      <AdminNav />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Audit Log</h1>
          <p className="text-muted-foreground">Tamper-evident activity log ({totalCount} entries)</p>
        </div>
        <button onClick={() => verifyMutation.mutate()} disabled={verifyMutation.isPending} className="rounded-md border px-4 py-2 text-sm hover:bg-muted disabled:opacity-50">
          {verifyMutation.isPending ? "Verifying..." : "Verify Chain Integrity"}
        </button>
      </div>

      {verifyResult && (
        <div className={`rounded-md border p-4 ${verifyResult.verified ? "border-green-500 bg-green-50 dark:bg-green-950" : "border-red-500 bg-red-50 dark:bg-red-950"}`}>
          <p className="font-medium">{verifyResult.verified ? "Chain integrity verified" : `Chain BROKEN at entry #${verifyResult.broken_at_id}`}</p>
          <p className="text-sm text-muted-foreground">{verifyResult.total_checked} entries checked</p>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={filters.event_type} onChange={(e) => setFilters(f => ({ ...f, event_type: e.target.value, page: 1 }))} className="rounded-md border bg-background px-3 py-2 text-sm">
          <option value="">All Event Types</option>
          {eventTypes.map(t => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
        </select>
        <input type="date" value={filters.from_date} onChange={(e) => setFilters(f => ({ ...f, from_date: e.target.value, page: 1 }))} className="rounded-md border bg-background px-3 py-2 text-sm" placeholder="From" />
        <input type="date" value={filters.to_date} onChange={(e) => setFilters(f => ({ ...f, to_date: e.target.value, page: 1 }))} className="rounded-md border bg-background px-3 py-2 text-sm" placeholder="To" />
      </div>

      {isLoading && <div className="space-y-3">{Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-10 animate-pulse rounded-md bg-muted" />)}</div>}

      {isError && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-center">
          <p className="text-destructive">Failed to load audit entries</p>
          <button onClick={() => refetch()} className="mt-2 text-sm underline">Retry</button>
        </div>
      )}

      {!isLoading && !isError && entries.length === 0 && (
        <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">No audit entries match your filters. Try adjusting the date range or filters.</div>
      )}

      {!isLoading && !isError && entries.length > 0 && (
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead><tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Timestamp</th>
              <th className="px-4 py-3 text-left font-medium">User</th>
              <th className="px-4 py-3 text-left font-medium">Action</th>
              <th className="px-4 py-3 text-left font-medium">Resource</th>
              <th className="px-4 py-3 text-left font-medium">IP</th>
            </tr></thead>
            <tbody>
              {entries.map((entry) => (
                <tr key={entry.id} className="border-b last:border-0">
                  <td colSpan={5} className="p-0">
                    <button onClick={() => setExpandedId(expandedId === entry.id ? null : entry.id)} className="flex w-full items-center px-4 py-3 text-left hover:bg-muted/30">
                      <span className="w-40 shrink-0 text-muted-foreground">{new Date(entry.created_at).toLocaleString()}</span>
                      <span className="w-28 shrink-0">{entry.username_snapshot}</span>
                      <span className="w-36 shrink-0"><span className="rounded-full bg-muted px-2 py-0.5 text-xs">{entry.event_type.replace(/_/g, " ")}</span></span>
                      <span className="flex-1 truncate text-muted-foreground">{entry.target_repr || entry.target_model}</span>
                      <span className="w-28 shrink-0 text-right text-muted-foreground text-xs">{expandedId === entry.id ? "▲" : "▼"}</span>
                    </button>
                    {expandedId === entry.id && (
                      <div className="border-t bg-muted/20 px-4 py-3">
                        <pre className="overflow-auto rounded-md bg-muted p-3 text-xs">{JSON.stringify(entry.extra_data, null, 2)}</pre>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalCount > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">Page {filters.page} of {Math.ceil(totalCount / 20)}</p>
          <div className="space-x-2">
            <button disabled={filters.page <= 1} onClick={() => setFilters(f => ({ ...f, page: f.page - 1 }))} className="rounded-md border px-3 py-1 text-sm disabled:opacity-50">Previous</button>
            <button disabled={filters.page * 20 >= totalCount} onClick={() => setFilters(f => ({ ...f, page: f.page + 1 }))} className="rounded-md border px-3 py-1 text-sm disabled:opacity-50">Next</button>
          </div>
        </div>
      )}
    </div>
  );
}
