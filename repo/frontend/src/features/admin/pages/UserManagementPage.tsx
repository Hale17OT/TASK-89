import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { listUsers, createUser, disableUser, enableUser } from "@/api/endpoints/admin";
import type { UserInfo } from "@/api/types/admin.types";
import { SudoModeModal } from "../components/SudoModeModal";
import { AdminNav } from "../components/AdminNav";

export default function UserManagementPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [sudoAction, setSudoAction] = useState<{ userId: string; action: "disable" } | null>(null);
  const [newUser, setNewUser] = useState({ username: "", full_name: "", role: "front_desk", password: "" });

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["users"],
    queryFn: () => listUsers({}),
  });

  const createMutation = useMutation({
    mutationFn: (d: typeof newUser) => createUser(d),
    onSuccess: () => {
      toast.success("User created");
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setShowCreate(false);
      setNewUser({ username: "", full_name: "", role: "front_desk", password: "" });
    },
    onError: () => toast.error("Failed to create user"),
  });

  const disableMutation = useMutation({
    mutationFn: (id: string) => disableUser(id, { confirm: true }),
    onSuccess: () => {
      toast.success("User disabled");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: () => toast.error("Failed to disable user"),
  });

  const enableMutation = useMutation({
    mutationFn: (id: string) => enableUser(id),
    onSuccess: () => {
      toast.success("User enabled");
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: () => toast.error("Failed to enable user"),
  });

  const users: UserInfo[] = data?.results ?? [];

  return (
    <div className="space-y-6">
      <AdminNav />
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">User Management</h1>
          <p className="text-muted-foreground">Manage clinic staff accounts</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
          Create User
        </button>
      </div>

      {isLoading && (
        <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 animate-pulse rounded-md bg-muted" />)}</div>
      )}

      {isError && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-center">
          <p className="text-destructive">Failed to load users</p>
          <button onClick={() => refetch()} className="mt-2 text-sm underline">Retry</button>
        </div>
      )}

      {!isLoading && !isError && users.length === 0 && (
        <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">No users found.</div>
      )}

      {!isLoading && !isError && users.length > 0 && (
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead><tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Username</th>
              <th className="px-4 py-3 text-left font-medium">Full Name</th>
              <th className="px-4 py-3 text-left font-medium">Role</th>
              <th className="px-4 py-3 text-left font-medium">Status</th>
              <th className="px-4 py-3 text-left font-medium">Last Login</th>
              <th className="px-4 py-3 text-right font-medium">Actions</th>
            </tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{u.username}</td>
                  <td className="px-4 py-3">{u.full_name || "—"}</td>
                  <td className="px-4 py-3"><span className="rounded-full bg-muted px-2 py-1 text-xs">{u.role}</span></td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-1 text-xs ${u.is_active ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200" : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200"}`}>
                      {u.is_active ? "Active" : "Disabled"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{u.last_login ? new Date(u.last_login).toLocaleDateString() : "Never"}</td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {u.is_active ? (
                      <button onClick={() => setSudoAction({ userId: u.id, action: "disable" })} className="text-xs text-destructive hover:underline">Disable</button>
                    ) : (
                      <button onClick={() => enableMutation.mutate(u.id)} className="text-xs text-primary hover:underline">Enable</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create User Dialog */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
            <h2 className="mb-4 text-lg font-semibold">Create User</h2>
            <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(newUser); }} className="space-y-4">
              <div><label className="mb-1 block text-sm font-medium">Username</label><input value={newUser.username} onChange={(e) => setNewUser(p => ({ ...p, username: e.target.value }))} required className="w-full rounded-md border bg-background px-3 py-2 text-sm" /></div>
              <div><label className="mb-1 block text-sm font-medium">Full Name</label><input value={newUser.full_name} onChange={(e) => setNewUser(p => ({ ...p, full_name: e.target.value }))} className="w-full rounded-md border bg-background px-3 py-2 text-sm" /></div>
              <div><label className="mb-1 block text-sm font-medium">Role</label><select value={newUser.role} onChange={(e) => setNewUser(p => ({ ...p, role: e.target.value }))} className="w-full rounded-md border bg-background px-3 py-2 text-sm">
                <option value="front_desk">Front Desk</option><option value="clinician">Clinician</option><option value="compliance">Compliance</option><option value="admin">Admin</option>
              </select></div>
              <div><label className="mb-1 block text-sm font-medium">Password</label><input type="password" value={newUser.password} onChange={(e) => setNewUser(p => ({ ...p, password: e.target.value }))} required minLength={12} className="w-full rounded-md border bg-background px-3 py-2 text-sm" /></div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowCreate(false)} className="rounded-md border px-4 py-2 text-sm">Cancel</button>
                <button type="submit" disabled={createMutation.isPending} className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50">
                  {createMutation.isPending ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Sudo Mode for Disable */}
      {sudoAction && (
        <SudoModeModal
          open={true}
          actionClass="user_disable"
          onAuthenticated={() => { disableMutation.mutate(sudoAction.userId); setSudoAction(null); }}
          onClose={() => setSudoAction(null)}
        />
      )}
    </div>
  );
}
