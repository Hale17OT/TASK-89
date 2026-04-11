import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  Image,
  AlertTriangle,
  DollarSign,
  BarChart3,
  Settings,
  FileSearch,
  Shield,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { hasRole, type Role } from "@/lib/roles";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  to: string;
  icon: React.ElementType;
  roles: Role[] | "all";
}

const navItems: NavItem[] = [
  {
    label: "Dashboard",
    to: "/dashboard",
    icon: LayoutDashboard,
    roles: "all",
  },
  {
    label: "Patients",
    to: "/patients",
    icon: Users,
    roles: ["front_desk", "clinician", "admin"],
  },
  {
    label: "Media",
    to: "/media",
    icon: Image,
    roles: ["front_desk", "clinician", "admin"],
  },
  {
    label: "Infringements",
    to: "/infringements",
    icon: AlertTriangle,
    roles: ["compliance", "admin"],
  },
  {
    label: "Financials",
    to: "/financials",
    icon: DollarSign,
    roles: ["front_desk", "admin"],
  },
  {
    label: "Reports",
    to: "/reports",
    icon: BarChart3,
    roles: ["compliance", "admin"],
  },
  {
    label: "Admin",
    to: "/admin",
    icon: Settings,
    roles: ["admin"],
  },
  {
    label: "Audit",
    to: "/audit",
    icon: FileSearch,
    roles: ["compliance", "admin"],
  },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const { user } = useAuth();

  const visibleItems = navItems.filter((item) =>
    hasRole(user?.role, item.roles)
  );

  return (
    <aside className={cn("flex h-full w-64 flex-col border-r border-border bg-muted", className)}>
      {/* Brand */}
      <div className="flex h-16 items-center gap-2 border-b border-border px-6">
        <Shield className="h-6 w-6 text-primary" />
        <span className="text-lg font-semibold tracking-tight">MedRights</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 overflow-y-auto p-4">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="border-t border-border p-4">
        <p className="text-xs text-muted-foreground">
          MedRights v0.1.0
        </p>
      </div>
    </aside>
  );
}
