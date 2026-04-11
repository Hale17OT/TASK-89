import { Routes, Route } from "react-router-dom";
import { SubscriptionListPage } from "./pages/SubscriptionListPage";
import { SubscriptionCreatePage } from "./pages/SubscriptionCreatePage";
import { OutboxDashboardPage } from "./pages/OutboxDashboardPage";

export default function ReportRoutes() {
  return (
    <Routes>
      <Route index element={<SubscriptionListPage />} />
      <Route path="new" element={<SubscriptionCreatePage />} />
      <Route path="outbox" element={<OutboxDashboardPage />} />
    </Routes>
  );
}
