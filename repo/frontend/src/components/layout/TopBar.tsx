import { useState, useEffect, useRef } from "react";
import { LogOut, Moon, Sun, User as UserIcon, ChevronDown, Plus } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/components/domain/ThemeProvider";
import { getRoleLabel } from "@/lib/roles";
import { cn } from "@/lib/utils";
import apiClient from "@/api/client";

interface GuestProfile {
  id: string;
  display_name: string;
  is_active: boolean;
  created_at: string;
}

interface RecentPatient {
  id: number;
  patient_id: string;
  accessed_at: string;
}

export function TopBar() {
  const { user, logout } = useAuth();
  const { theme, setTheme, resolvedTheme } = useTheme();

  const [profiles, setProfiles] = useState<GuestProfile[]>([]);
  const [recentPatients, setRecentPatients] = useState<RecentPatient[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [newProfileName, setNewProfileName] = useState("");
  const [creating, setCreating] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const activeProfile = profiles.find((p) => p.is_active);

  const fetchRecentPatients = (profileId: string) => {
    apiClient
      .get<RecentPatient[]>(`auth/guest-profiles/${profileId}/recent-patients/`)
      .then((res) => setRecentPatients(res.data))
      .catch(() => setRecentPatients([]));
  };

  useEffect(() => {
    if (user) {
      apiClient
        .get<GuestProfile[]>("auth/guest-profiles/")
        .then((res) => {
          setProfiles(res.data);
          const active = res.data.find((p) => p.is_active);
          if (active) {
            fetchRecentPatients(active.id);
          }
        })
        .catch(() => {});
    }
  }, [user]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleActivate = async (profileId: string) => {
    try {
      await apiClient.post(`auth/guest-profiles/${profileId}/activate/`);
      setProfiles((prev) =>
        prev.map((p) => ({ ...p, is_active: p.id === profileId }))
      );
      fetchRecentPatients(profileId);
      setDropdownOpen(false);
    } catch {
      // silently ignore
    }
  };

  const handleCreate = async () => {
    if (!newProfileName.trim()) return;
    setCreating(true);
    try {
      const res = await apiClient.post<GuestProfile>("auth/guest-profiles/", {
        display_name: newProfileName.trim(),
      });
      setProfiles((prev) => [res.data, ...prev]);
      setNewProfileName("");
    } catch {
      // silently ignore
    } finally {
      setCreating(false);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  const toggleTheme = () => {
    setTheme(resolvedTheme === "dark" ? "light" : "dark");
  };

  return (
    <header className="flex h-16 items-center justify-between border-b border-border bg-background px-6">
      {/* Left side - Guest switcher */}
      <div className="relative flex items-center gap-2" ref={dropdownRef}>
        {user && profiles.length === 0 ? (
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground"
          >
            <Plus className="h-4 w-4" />
            Create Profile
          </button>
        ) : (
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="inline-flex items-center gap-2 rounded-md border border-input bg-background px-3 py-1.5 text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground"
          >
            <UserIcon className="h-4 w-4" />
            <span>{activeProfile?.display_name ?? "Select Profile"}</span>
            <ChevronDown className="h-3 w-3" />
          </button>
        )}

        {dropdownOpen && (
          <div className="absolute left-0 top-full z-50 mt-1 w-64 rounded-md border border-border bg-card shadow-lg">
            <div className="max-h-48 overflow-y-auto p-1">
              {profiles.map((profile) => (
                <button
                  key={profile.id}
                  onClick={() => handleActivate(profile.id)}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-sm px-3 py-2 text-sm",
                    profile.is_active
                      ? "bg-primary/10 font-medium text-primary"
                      : "hover:bg-accent"
                  )}
                >
                  <UserIcon className="h-3.5 w-3.5" />
                  {profile.display_name}
                  {profile.is_active && (
                    <span className="ml-auto text-xs text-primary">Active</span>
                  )}
                </button>
              ))}
            </div>
            {recentPatients.length > 0 && (
              <div className="border-t border-border p-2">
                <p className="px-1 py-1 text-xs font-medium text-muted-foreground uppercase tracking-wide">
                  Recent Patients
                </p>
                <div className="max-h-24 overflow-y-auto">
                  {recentPatients.map((rp) => (
                    <a
                      key={rp.patient_id}
                      href={`/patients/${rp.patient_id}`}
                      className="block rounded-sm px-3 py-1.5 text-xs text-muted-foreground hover:bg-accent hover:text-foreground truncate"
                    >
                      {rp.patient_id}
                    </a>
                  ))}
                </div>
              </div>
            )}
            <div className="border-t border-border p-2">
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={newProfileName}
                  onChange={(e) => setNewProfileName(e.target.value)}
                  placeholder="New profile name"
                  className="flex h-8 w-full rounded-md border border-input bg-background px-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleCreate();
                  }}
                />
                <button
                  onClick={handleCreate}
                  disabled={creating || !newProfileName.trim()}
                  className="inline-flex h-8 items-center justify-center rounded-md bg-primary px-2 text-xs font-medium text-primary-foreground shadow hover:bg-primary/90 disabled:opacity-50"
                >
                  <Plus className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Right side - User info & actions */}
      <div className="flex items-center gap-4">
        {/* Theme toggle */}
        <button
          onClick={toggleTheme}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background text-sm font-medium shadow-sm hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          aria-label="Toggle theme"
        >
          {resolvedTheme === "dark" ? (
            <Sun className="h-4 w-4" />
          ) : (
            <Moon className="h-4 w-4" />
          )}
        </button>

        {/* User info */}
        {user && (
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-primary-foreground">
                <UserIcon className="h-4 w-4" />
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium leading-none">
                  {user.full_name}
                </span>
                <span
                  className={cn(
                    "mt-1 inline-flex w-fit items-center rounded-full px-2 py-0.5 text-xs font-medium",
                    "bg-secondary text-secondary-foreground"
                  )}
                >
                  {getRoleLabel(user.role)}
                </span>
              </div>
            </div>

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-input bg-background text-sm font-medium shadow-sm hover:bg-destructive hover:text-destructive-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Log out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
