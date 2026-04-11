import { lazy, Suspense } from "react";
import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "@/components/layout/AppShell";
import { RequireAuth } from "@/components/domain/RequireAuth";
import { ProtectedRoute } from "@/components/domain/ProtectedRoute";
import { ErrorBoundary } from "@/components/feedback/ErrorBoundary";
import { LoginPage } from "@/features/auth/pages/LoginPage";
import { DashboardPage } from "@/features/dashboard/pages/DashboardPage";
import { NotFoundPage } from "@/pages/NotFoundPage";

// Lazy-loaded feature modules
const PatientRoutes = lazy(() => import("@/features/patients/routes"));
const MediaRoutes = lazy(() => import("@/features/media/routes"));
const InfringementRoutes = lazy(() => import("@/features/infringements/routes"));
const FinancialRoutes = lazy(() => import("@/features/financials/routes"));
const ReportRoutes = lazy(() => import("@/features/reports/routes"));
const AdminRoutes = lazy(() => import("@/features/admin/routes"));
const AuditLogPage = lazy(() => import("@/features/admin/pages/AuditLogPage"));

function PageSkeleton() {
  return (
    <div className="space-y-4 p-6">
      <div className="h-8 w-48 animate-pulse rounded-md bg-muted" />
      <div className="h-64 animate-pulse rounded-md bg-muted" />
    </div>
  );
}

function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<PageSkeleton />}>{children}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/",
    element: <RequireAuth />,
    errorElement: (
      <ErrorBoundary>
        <div />
      </ErrorBoundary>
    ),
    children: [
      {
        element: <AppShell />,
        children: [
          {
            index: true,
            element: <Navigate to="/dashboard" replace />,
          },
          {
            path: "dashboard",
            element: <DashboardPage />,
          },
          {
            path: "patients/*",
            element: (
              <ProtectedRoute allowedRoles={["front_desk", "clinician", "admin"]}>
                <SuspenseWrapper>
                  <PatientRoutes />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: "media/*",
            element: (
              <ProtectedRoute allowedRoles={["front_desk", "clinician", "admin"]}>
                <SuspenseWrapper>
                  <MediaRoutes />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: "infringements/*",
            element: (
              <ProtectedRoute allowedRoles={["compliance", "admin"]}>
                <SuspenseWrapper>
                  <InfringementRoutes />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: "financials/*",
            element: (
              <ProtectedRoute allowedRoles={["front_desk", "admin"]}>
                <SuspenseWrapper>
                  <FinancialRoutes />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: "reports/*",
            element: (
              <ProtectedRoute allowedRoles={["compliance", "admin"]}>
                <SuspenseWrapper>
                  <ReportRoutes />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: "admin/*",
            element: (
              <ProtectedRoute allowedRoles={["admin"]}>
                <SuspenseWrapper>
                  <AdminRoutes />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: "audit",
            element: (
              <ProtectedRoute allowedRoles={["compliance", "admin"]}>
                <SuspenseWrapper>
                  <AuditLogPage />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
        ],
      },
    ],
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
