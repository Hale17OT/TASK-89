import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Users,
  Image,
  AlertTriangle,
  DollarSign,
  BarChart3,
  Plus,
  Upload,
  FileText,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { getRoleLabel, hasRole } from "@/lib/roles";
import { cn } from "@/lib/utils";
import apiClient from "@/api/client";

interface DashboardData {
  patients?: number;
  media?: number;
  open_infringements?: number;
  open_orders?: number;
  reports?: number;
}

async function fetchDashboardCounts(): Promise<DashboardData> {
  // Fetch counts from individual endpoints; errors yield zero counts
  const results: DashboardData = {};
  try {
    const patients = await apiClient.get("patients/", { params: { q: "" } });
    results.patients = patients.data?.count ?? 0;
  } catch { results.patients = 0; }
  try {
    const media = await apiClient.get("media/", { params: { page_size: 1 } });
    results.media = media.data?.count ?? 0;
  } catch { results.media = 0; }
  try {
    const orders = await apiClient.get("financials/orders/", { params: { status: "open", page_size: 1 } });
    results.open_orders = orders.data?.count ?? 0;
  } catch { results.open_orders = 0; }
  return results;
}

interface StatCard {
  label: string;
  value: string;
  icon: React.ElementType;
  description: string;
  to?: string;
}

export function DashboardPage() {
  const { user } = useAuth();

  const { data: counts } = useQuery({
    queryKey: ["dashboard-counts"],
    queryFn: fetchDashboardCounts,
    staleTime: 30_000,
  });

  const roleGreeting = user
    ? `Welcome back, ${user.full_name || user.username}`
    : "Welcome to MedRights";

  const roleSubtitle = user
    ? `You are logged in as ${getRoleLabel(user.role)}`
    : "";

  const statCards: StatCard[] = [];

  if (user && hasRole(user.role, ["front_desk", "clinician", "admin"])) {
    statCards.push(
      {
        label: "Patients",
        value: counts?.patients !== undefined ? String(counts.patients) : "--",
        icon: Users,
        description: "Active patient records",
        to: "/patients",
      },
      {
        label: "Media Files",
        value: counts?.media !== undefined ? String(counts.media) : "--",
        icon: Image,
        description: "Uploaded media assets",
        to: "/media",
      }
    );
  }

  if (user && hasRole(user.role, ["compliance", "admin"])) {
    statCards.push({
      label: "Open Infringements",
      value: counts?.open_infringements !== undefined ? String(counts.open_infringements) : "--",
      icon: AlertTriangle,
      description: "Pending compliance reviews",
      to: "/infringements",
    });
  }

  if (user && hasRole(user.role, ["front_desk", "admin"])) {
    statCards.push({
      label: "Open Orders",
      value: counts?.open_orders !== undefined ? String(counts.open_orders) : "--",
      icon: DollarSign,
      description: "Awaiting payment",
      to: "/financials",
    });
  }

  statCards.push({
    label: "Reports",
    value: "--",
    icon: BarChart3,
    description: "Scheduled report subscriptions",
    to: "/reports",
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">{roleGreeting}</h1>
        {roleSubtitle && (
          <p className="mt-1 text-muted-foreground">{roleSubtitle}</p>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          const Wrapper = card.to ? Link : "div";
          const wrapperProps = card.to ? { to: card.to } : {};
          return (
            <Wrapper
              key={card.label}
              {...(wrapperProps as any)}
              className="rounded-lg border border-border bg-card p-6 shadow-sm transition-colors hover:bg-accent/50"
            >
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-muted-foreground">
                  {card.label}
                </p>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </div>
              <div className="mt-2">
                <p className="text-2xl font-bold">{card.value}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  {card.description}
                </p>
              </div>
            </Wrapper>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-semibold">Quick Actions</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {user && hasRole(user.role, ["front_desk", "clinician", "admin"]) && (
            <>
              <QuickAction
                icon={Plus}
                label="Register Patient"
                description="Add a new patient record"
                to="/patients/new"
              />
              <QuickAction
                icon={Upload}
                label="Upload Media"
                description="Upload patient media files"
                to="/media/upload"
              />
            </>
          )}
          {user && hasRole(user.role, ["front_desk", "admin"]) && (
            <QuickAction
              icon={DollarSign}
              label="Create Order"
              description="New payable order"
              to="/financials/new"
            />
          )}
          <QuickAction
            icon={FileText}
            label="View Reports"
            description="Report subscriptions and outbox"
            to="/reports"
          />
        </div>
      </div>
    </div>
  );
}

function QuickAction({
  icon: Icon,
  label,
  description,
  to,
}: {
  icon: React.ElementType;
  label: string;
  description: string;
  to: string;
}) {
  return (
    <Link
      to={to}
      className={cn(
        "flex items-center gap-3 rounded-lg border border-border p-4 text-left transition-colors",
        "hover:bg-accent hover:text-accent-foreground"
      )}
    >
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-primary/10">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <div>
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>
    </Link>
  );
}
