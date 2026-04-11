import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";

const adminLinks = [
  { to: "/admin/users", label: "Users" },
  { to: "/admin/throttling", label: "Throttling" },
  { to: "/admin/export", label: "Bulk Export" },
  { to: "/admin/audit-log", label: "Audit Log" },
  { to: "/admin/policies", label: "Policies" },
];

export function AdminNav() {
  const { pathname } = useLocation();

  return (
    <nav className="flex gap-1 rounded-lg border bg-muted p-1">
      {adminLinks.map((link) => (
        <Link
          key={link.to}
          to={link.to}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
            pathname.startsWith(link.to)
              ? "bg-background text-foreground shadow-sm"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
