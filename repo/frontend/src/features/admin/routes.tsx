import { Routes, Route, Navigate } from "react-router-dom";
import UserManagementPage from "./pages/UserManagementPage";
import AuditLogPage from "./pages/AuditLogPage";
import ThrottlingPage from "./pages/ThrottlingPage";
import ExportPage from "./pages/ExportPage";
import PolicyManagementPage from "./pages/PolicyManagementPage";

export default function AdminRoutes() {
  return (
    <Routes>
      <Route index element={<Navigate to="users" replace />} />
      <Route path="users" element={<UserManagementPage />} />
      <Route path="audit-log" element={<AuditLogPage />} />
      <Route path="throttling" element={<ThrottlingPage />} />
      <Route path="export" element={<ExportPage />} />
      <Route path="policies" element={<PolicyManagementPage />} />
    </Routes>
  );
}
