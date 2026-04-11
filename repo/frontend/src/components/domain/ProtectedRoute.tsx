import { Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { hasRole, type Role } from "@/lib/roles";
import { ForbiddenPage } from "@/pages/ForbiddenPage";

interface ProtectedRouteProps {
  allowedRoles: Role[] | "all";
  children?: React.ReactNode;
}

export function ProtectedRoute({ allowedRoles, children }: ProtectedRouteProps) {
  const { user } = useAuth();

  if (!user || !hasRole(user.role, allowedRoles)) {
    return <ForbiddenPage />;
  }

  return children ? <>{children}</> : <Outlet />;
}
