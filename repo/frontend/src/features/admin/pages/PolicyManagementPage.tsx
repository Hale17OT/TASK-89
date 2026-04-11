import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import apiClient from "@/api/client";
import { AdminNav } from "../components/AdminNav";

interface SystemPolicy {
  key: string;
  value: unknown;
  description: string;
  updated_by: string | null;
  updated_at: string | null;
}

async function fetchPolicies(): Promise<SystemPolicy[]> {
  const response = await apiClient.get<SystemPolicy[]>("policies/");
  return response.data;
}

async function updatePolicy(
  key: string,
  value: unknown
): Promise<SystemPolicy> {
  const response = await apiClient.patch<SystemPolicy>(`policies/${key}/`, {
    value,
    confirm: true,
  });
  return response.data;
}

export default function PolicyManagementPage() {
  const queryClient = useQueryClient();
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");

  const { data: policies, isLoading, isError, refetch } = useQuery({
    queryKey: ["policies"],
    queryFn: fetchPolicies,
  });

  const saveMutation = useMutation({
    mutationFn: ({ key, value }: { key: string; value: unknown }) =>
      updatePolicy(key, value),
    onSuccess: () => {
      toast.success("Policy updated");
      queryClient.invalidateQueries({ queryKey: ["policies"] });
      setEditingKey(null);
      setEditValue("");
    },
    onError: () => toast.error("Failed to update policy"),
  });

  const startEdit = (policy: SystemPolicy) => {
    setEditingKey(policy.key);
    setEditValue(
      typeof policy.value === "string"
        ? policy.value
        : JSON.stringify(policy.value)
    );
  };

  const handleSave = (key: string) => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(editValue);
    } catch {
      // Treat as raw string if not valid JSON
      parsed = editValue;
    }
    saveMutation.mutate({ key, value: parsed });
  };

  return (
    <div className="space-y-6">
      <AdminNav />
      <div>
        <h1 className="text-2xl font-bold">Policy Management</h1>
        <p className="text-muted-foreground">
          View and update system-wide configuration policies.
        </p>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 animate-pulse rounded-md bg-muted" />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-center">
          <p className="text-destructive">Failed to load policies</p>
          <button
            onClick={() => refetch()}
            className="mt-2 text-sm underline"
          >
            Retry
          </button>
        </div>
      )}

      {!isLoading && !isError && policies && policies.length === 0 && (
        <div className="rounded-md border border-dashed p-8 text-center text-muted-foreground">
          No policies configured. Run the seed command to create defaults.
        </div>
      )}

      {!isLoading && !isError && policies && policies.length > 0 && (
        <div className="rounded-md border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Key</th>
                <th className="px-4 py-3 text-left font-medium">
                  Description
                </th>
                <th className="px-4 py-3 text-left font-medium">Value</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {policies.map((p) => (
                <tr
                  key={p.key}
                  className="border-b last:border-0 hover:bg-muted/30"
                >
                  <td className="px-4 py-3 font-mono text-xs">{p.key}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {p.description}
                  </td>
                  <td className="px-4 py-3">
                    {editingKey === p.key ? (
                      <input
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="w-full rounded-md border bg-background px-2 py-1 text-sm font-mono"
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleSave(p.key);
                          if (e.key === "Escape") {
                            setEditingKey(null);
                            setEditValue("");
                          }
                        }}
                        autoFocus
                      />
                    ) : (
                      <span className="font-mono text-xs">
                        {typeof p.value === "string"
                          ? p.value
                          : JSON.stringify(p.value)}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right space-x-2">
                    {editingKey === p.key ? (
                      <>
                        <button
                          onClick={() => handleSave(p.key)}
                          disabled={saveMutation.isPending}
                          className="text-xs text-primary hover:underline disabled:opacity-50"
                        >
                          {saveMutation.isPending ? "Saving..." : "Save"}
                        </button>
                        <button
                          onClick={() => {
                            setEditingKey(null);
                            setEditValue("");
                          }}
                          className="text-xs text-muted-foreground hover:underline"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => startEdit(p)}
                        className="text-xs text-primary hover:underline"
                      >
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
