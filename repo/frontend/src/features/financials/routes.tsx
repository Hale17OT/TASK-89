import { Routes, Route } from "react-router-dom";
import { OrderListPage } from "./pages/OrderListPage";
import { OrderCreatePage } from "./pages/OrderCreatePage";
import { OrderDetailPage } from "./pages/OrderDetailPage";
import { PaymentPage } from "./pages/PaymentPage";
import { RefundPage } from "./pages/RefundPage";
import { ReconciliationPage } from "./pages/ReconciliationPage";

export default function FinancialRoutes() {
  return (
    <Routes>
      <Route index element={<OrderListPage />} />
      <Route path="new" element={<OrderCreatePage />} />
      <Route path=":orderId" element={<OrderDetailPage />} />
      <Route path=":orderId/pay" element={<PaymentPage />} />
      <Route path=":orderId/refund" element={<RefundPage />} />
      <Route path="reconciliation" element={<ReconciliationPage />} />
    </Routes>
  );
}
