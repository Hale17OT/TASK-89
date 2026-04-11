export interface Order {
  id: string;
  order_number: string;
  patient_id: string;
  status:
    | "open"
    | "paid"
    | "partial"
    | "closed_unpaid"
    | "voided"
    | "refunded";
  total_amount: string;
  amount_paid: string;
  auto_close_at: string | null;
  created_at: string;
  time_remaining_seconds?: number;
}

export interface OrderDetail extends Order {
  line_items: OrderLineItem[];
  payments: Payment[];
  refunds: Refund[];
}

export interface OrderLineItem {
  id: string;
  description: string;
  quantity: number;
  unit_price: string;
  line_total: string;
}

export interface Payment {
  id: string;
  amount: string;
  payment_method: "cash" | "check";
  check_number?: string;
  posted_at: string;
  is_compensating: boolean;
}

export interface Refund {
  id: string;
  amount: string;
  reason: string;
  status: "pending" | "approved" | "completed" | "denied";
  created_at: string;
}

export interface CreateOrderPayload {
  patient_id: string;
  line_items: { description: string; quantity: number; unit_price: number }[];
  notes?: string;
}

export interface ReconciliationSummary {
  reconciliation_date: string;
  total_orders: number;
  total_revenue: string;
  total_payments: string;
  total_refunds: string;
  discrepancy: string;
}
