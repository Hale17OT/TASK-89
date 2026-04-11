import { Routes, Route } from "react-router-dom";
import { InfringementListPage } from "./pages/InfringementListPage";
import { InfringementCreatePage } from "./pages/InfringementCreatePage";
import { DisputeDetailPage } from "./pages/DisputeDetailPage";

export default function InfringementRoutes() {
  return (
    <Routes>
      <Route index element={<InfringementListPage />} />
      <Route path="new" element={<InfringementCreatePage />} />
      <Route path=":reportId" element={<DisputeDetailPage />} />
    </Routes>
  );
}
