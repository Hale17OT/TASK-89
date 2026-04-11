import { useState, useCallback, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { Loader2, ShieldAlert, X } from "lucide-react";
import { toast } from "sonner";
import { acquireSudo } from "@/api/endpoints/admin";

interface SudoModeModalProps {
  open: boolean;
  onClose: () => void;
  actionClass: string;
  onAuthenticated: () => void;
}

const SUDO_WINDOW_MS = 5 * 60 * 1000; // 5 minutes

// Module-level cache for sudo window
let sudoExpiresAt: number | null = null;

export function isSudoActive(): boolean {
  return sudoExpiresAt != null && Date.now() < sudoExpiresAt;
}

export function SudoModeModal({
  open,
  onClose,
  actionClass,
  onAuthenticated,
}: SudoModeModalProps) {
  const [password, setPassword] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (open) {
      setPassword("");
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  const mutation = useMutation({
    mutationFn: () => acquireSudo(password, actionClass),
    onSuccess: () => {
      sudoExpiresAt = Date.now() + SUDO_WINDOW_MS;
      toast.success("Re-authentication successful");
      onClose();
      onAuthenticated();
    },
    onError: (err: Error) => {
      toast.error(`Authentication failed: ${err.message}`);
    },
  });

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (!password.trim()) return;
      mutation.mutate();
    },
    [password, mutation]
  );

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Re-authentication required"
        className="relative z-10 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>

        {/* Banner */}
        <div className="flex items-center gap-3 rounded-md border border-amber-300 bg-amber-50 dark:bg-amber-950/20 dark:border-amber-700 px-4 py-3 mb-6">
          <ShieldAlert className="h-5 w-5 text-amber-600 shrink-0" />
          <p className="text-sm text-amber-800 dark:text-amber-300">
            This action requires re-authentication.
          </p>
        </div>

        <h2 className="text-lg font-semibold mb-4">Confirm Identity</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="sudo-password"
              className="block text-sm font-medium mb-1.5"
            >
              Password
            </label>
            <input
              ref={inputRef}
              id="sudo-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Enter your password..."
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending || !password.trim()}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {mutation.isPending && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Authenticate
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
