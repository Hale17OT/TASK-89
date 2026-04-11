import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { listWorkstations, unblockWorkstation } from "@/api/endpoints/admin";
import type { WorkstationBlacklist } from "@/api/types/admin.types";
import { SudoModeModal } from "../components/SudoModeModal";
import { AdminNav } from "../components/AdminNav";

export default function ThrottlingPage() {
  const queryClient = useQueryClient();
  const [sudoTarget, setSudoTarget] = useState<number | null>(null);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["workstations"],
    queryFn: () => listWorkstations({}),
  });

  const unblockMutation = useMutation({
    mutationFn: (id: number) => unblockWorkstation(id),
    onSuccess: () => {
      toast.success("Workstation unblocked");
      queryClient.invalidateQueries({ queryKey: ["workstations"] });
    },
    onError: () => toast.error("Failed to unblock workstation"),
  });

  const workstations: WorkstationBlacklist[] = data ?? [];

  return (
    <div className="space-y-6">
      <AdminNav />
      <div>
        <h1 className="text-2xl font-bold">Throttling & Blacklist</h1>
        <p className="text-muted-foreground">Manage workstation rate limiting and blacklist</p>
      </div>

      <div className="rounded-md border border-amber-500/50 bg-amber-50 p-4 dark:bg-amber-950">
        <p className="text-sm font-medium">Throttle Rules</p>
        <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
          <li>5 failed logins per 10 minutes per workstation triggers lockout</li>
          <li>3 lockouts within 24 hours triggers automatic blacklisting</li>
          <li>Blacklisted workstations cannot access any API endpoint</li>
        </ul>
      </div>

      {isLoading && <div className="space-y-3">{Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-12 animate-pulse rounded-md bg-muted" />)}</div>}

      {isError && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-center">
          <p className="text-destructive">Failed to load workstations</p>
          <button onClick={() => refetch()} className="mt-2 text-sm underline">Retry</button>
        </div>
      )}

      {!isLoading && !isError && workstations.length === 0 && (
        <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">No blacklisted workstations. The system is operating normally.</div>
      )}

      {!isLoading && !isError && workstations.length > 0 && (
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead><tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">IP Address</th>
              <th className="px-4 py-3 text-left font-medium">Workstation ID</th>
              <th className="px-4 py-3 text-left font-medium">Blacklisted At</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr></thead>
            <tbody>
              {workstations.map((ws) => (
                <tr key={ws.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3 font-mono text-sm">{ws.client_ip}</td>
                  <td className="px-4 py-3 font-mono text-xs truncate max-w-[200px]">{ws.workstation_id}</td>
                  <td className="px-4 py-3 text-muted-foreground">{ws.blacklisted_at ? new Date(ws.blacklisted_at).toLocaleString() : "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-1 text-xs ${ws.is_active ? "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200" : "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"}`}>
                      {ws.is_active ? "Blacklisted" : "Cleared"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    {ws.is_active && (
                      <button onClick={() => setSudoTarget(ws.id)} className="rounded-md border border-destructive/50 px-3 py-1 text-xs text-destructive hover:bg-destructive/10">
                        Unblock
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {sudoTarget !== null && (
        <SudoModeModal
          open={true}
          actionClass="workstation_unblock"
          onAuthenticated={() => { unblockMutation.mutate(sudoTarget); setSudoTarget(null); }}
          onClose={() => setSudoTarget(null)}
        />
      )}
    </div>
  );
}
