import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Eye,
  AlertCircle,
  Plus,
  Image as ImageIcon,
  FileText,
  User,
} from "lucide-react";
import { getPatient } from "@/api/endpoints/patients";
import { listConsents } from "@/api/endpoints/consents";
import { listMedia } from "@/api/endpoints/media";
import apiClient from "@/api/client";
import type { PatientDetail as PatientDetailType } from "@/api/types/patient.types";
import type { Consent } from "@/api/types/consent.types";
import type { MediaAsset } from "@/api/types/media.types";
import { useAuth } from "@/contexts/AuthContext";
import { hasRole } from "@/lib/roles";
import { cn } from "@/lib/utils";
import { BreakGlassModal } from "../components/BreakGlassModal";
import { ConsentCard } from "../components/ConsentCard";
import { ConsentCreateForm } from "../components/ConsentCreateForm";

type Tab = "demographics" | "consents" | "media";

export function PatientDetailPage() {
  const { patientId: id } = useParams<{ patientId: string }>();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<Tab>("demographics");
  const [breakGlassOpen, setBreakGlassOpen] = useState(false);
  const [unmaskedData, setUnmaskedData] = useState<PatientDetailType | null>(
    null
  );
  const [consentFormOpen, setConsentFormOpen] = useState(false);

  const patientQuery = useQuery({
    queryKey: ["patient", id],
    queryFn: () => getPatient(id!),
    enabled: !!id,
  });

  const consentsQuery = useQuery({
    queryKey: ["consents", id],
    queryFn: () => listConsents(id!),
    enabled: !!id && activeTab === "consents",
  });

  const mediaQuery = useQuery({
    queryKey: ["patient-media", id],
    queryFn: () => listMedia({ patient_id: id }),
    enabled: !!id && activeTab === "media",
  });

  // Record recent patient access for the active guest profile
  useEffect(() => {
    if (!patientQuery.isSuccess || !id) return;

    // Fetch guest profiles and find the active one, then POST
    apiClient
      .get<Array<{ id: string; is_active: boolean }>>("auth/guest-profiles/")
      .then((res) => {
        const activeProfile = res.data.find((p) => p.is_active);
        if (activeProfile) {
          apiClient
            .post(`auth/guest-profiles/${activeProfile.id}/recent-patients/`, {
              patient_id: id,
            })
            .catch(() => {
              // Silently ignore - this is a non-critical tracking call
            });
        }
      })
      .catch(() => {});
  }, [patientQuery.isSuccess, id]);

  const canEdit =
    user && hasRole(user.role, ["admin", "front_desk"]);

  if (patientQuery.isLoading) {
    return <PatientDetailSkeleton />;
  }

  if (patientQuery.isError) {
    return (
      <div className="space-y-6">
        <Link
          to="/patients"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Patients
        </Link>
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="font-medium text-destructive">
                Failed to load patient
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {patientQuery.error instanceof Error
                  ? patientQuery.error.message
                  : "An unexpected error occurred."}
              </p>
            </div>
            <button
              onClick={() => patientQuery.refetch()}
              className={cn(
                "rounded-md border border-destructive/50 px-3 py-1.5",
                "text-sm font-medium text-destructive hover:bg-destructive/10"
              )}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const patient = patientQuery.data;
  if (!patient) return null;

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "demographics", label: "Demographics", icon: User },
    { key: "consents", label: "Consents", icon: FileText },
    { key: "media", label: "Media", icon: ImageIcon },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/patients"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">
            {unmaskedData
              ? `${unmaskedData.first_name} ${unmaskedData.last_name}`
              : `${patient.first_name} ${patient.last_name}`}
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            MRN: {unmaskedData ? unmaskedData.mrn : patient.mrn}
          </p>
        </div>
        <span
          className={cn(
            "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
            patient.is_active
              ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
              : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
          )}
        >
          {patient.is_active ? "Active" : "Inactive"}
        </span>
      </div>

      {/* Tabs */}
      <div className="border-b border-border">
        <nav className="-mb-px flex gap-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  "inline-flex items-center gap-2 border-b-2 px-1 pb-3 text-sm font-medium transition-colors",
                  activeTab === tab.key
                    ? "border-primary text-foreground"
                    : "border-transparent text-muted-foreground hover:border-border hover:text-foreground"
                )}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === "demographics" && (
        <DemographicsTab
          patient={patient}
          unmaskedData={unmaskedData}
          canEdit={!!canEdit}
          onBreakGlass={() => setBreakGlassOpen(true)}
        />
      )}

      {activeTab === "consents" && (
        <ConsentsTab
          patientId={id!}
          consents={consentsQuery.data?.results}
          isLoading={consentsQuery.isLoading}
          isError={consentsQuery.isError}
          error={consentsQuery.error}
          onRetry={() => consentsQuery.refetch()}
          consentFormOpen={consentFormOpen}
          setConsentFormOpen={setConsentFormOpen}
        />
      )}

      {activeTab === "media" && (
        <MediaTab
          patientId={id!}
          media={mediaQuery.data?.results}
          isLoading={mediaQuery.isLoading}
          isError={mediaQuery.isError}
          error={mediaQuery.error}
          onRetry={() => mediaQuery.refetch()}
        />
      )}

      {/* Break Glass Modal */}
      <BreakGlassModal
        patientId={id!}
        open={breakGlassOpen}
        onClose={() => setBreakGlassOpen(false)}
        onSuccess={(data) => {
          setUnmaskedData(data.patient);
          setBreakGlassOpen(false);
        }}
      />
    </div>
  );
}

// -- Demographics Tab --
function DemographicsTab({
  patient,
  unmaskedData,
  canEdit,
  onBreakGlass,
}: {
  patient: PatientDetailType;
  unmaskedData: PatientDetailType | null;
  canEdit: boolean;
  onBreakGlass: () => void;
}) {
  const displayData = unmaskedData ?? patient;
  const isMasked = !unmaskedData;

  const fields = [
    { label: "MRN", value: displayData.mrn, masked: isMasked },
    { label: "SSN", value: displayData.ssn || "---", masked: isMasked },
    { label: "First Name", value: displayData.first_name, masked: isMasked },
    { label: "Last Name", value: displayData.last_name, masked: isMasked },
    { label: "Date of Birth", value: displayData.date_of_birth, masked: isMasked },
    { label: "Gender", value: displayData.gender },
    { label: "Phone", value: displayData.phone || "---", masked: isMasked },
    { label: "Email", value: displayData.email || "---", masked: isMasked },
    { label: "Address", value: displayData.address || "---", masked: isMasked },
  ];

  return (
    <div className="space-y-4">
      {!unmaskedData && (
        <div className="flex items-center justify-between rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-950/50">
          <p className="text-sm text-yellow-800 dark:text-yellow-200">
            Patient data is masked. Use Break-Glass to view unmasked records.
          </p>
          <button
            onClick={onBreakGlass}
            className={cn(
              "inline-flex items-center gap-2 rounded-md bg-yellow-600 px-3 py-1.5",
              "text-sm font-medium text-white",
              "hover:bg-yellow-700"
            )}
          >
            <Eye className="h-4 w-4" />
            Break Glass
          </button>
        </div>
      )}

      <div className="rounded-lg border border-border bg-card">
        <div className="grid gap-px sm:grid-cols-2">
          {fields.map((field) => (
            <div
              key={field.label}
              className="flex items-center justify-between border-b border-border px-4 py-3 last:border-0 sm:last:border-b"
            >
              <span className="text-sm text-muted-foreground">
                {field.label}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{field.value}</span>
                {"masked" in field && field.masked && (
                  <button
                    onClick={onBreakGlass}
                    className="rounded p-0.5 text-muted-foreground hover:text-foreground"
                    title="View unmasked"
                  >
                    <Eye className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {canEdit && (
        <div className="flex justify-end">
          <Link
            to={`/patients/${patient.id}/update`}
            className={cn(
              "inline-flex items-center rounded-md border border-border px-4 py-2",
              "text-sm font-medium hover:bg-accent"
            )}
          >
            Edit Patient
          </Link>
        </div>
      )}
    </div>
  );
}

// -- Consents Tab --
function ConsentsTab({
  patientId,
  consents,
  isLoading,
  isError,
  error,
  onRetry,
  consentFormOpen,
  setConsentFormOpen,
}: {
  patientId: string;
  consents: Consent[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  onRetry: () => void;
  consentFormOpen: boolean;
  setConsentFormOpen: (open: boolean) => void;
}) {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Consents</h2>
        <button
          onClick={() => setConsentFormOpen(true)}
          className={cn(
            "inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5",
            "text-sm font-medium text-primary-foreground shadow",
            "hover:bg-primary/90"
          )}
        >
          <Plus className="h-4 w-4" />
          Create Consent
        </button>
      </div>

      {isLoading && (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-32 animate-pulse rounded-lg border border-border bg-muted"
            />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="font-medium text-destructive">
                Failed to load consents
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {error instanceof Error
                  ? error.message
                  : "An unexpected error occurred."}
              </p>
            </div>
            <button
              onClick={onRetry}
              className={cn(
                "rounded-md border border-destructive/50 px-3 py-1.5",
                "text-sm font-medium text-destructive hover:bg-destructive/10"
              )}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {!isLoading && !isError && consents && consents.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card p-12 text-center">
          <FileText className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="font-medium text-muted-foreground">
            No consents found.
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Create a consent record to get started.
          </p>
        </div>
      )}

      {!isLoading && !isError && consents && consents.length > 0 && (
        <div className="space-y-3">
          {consents.map((consent) => (
            <ConsentCard
              key={consent.id}
              consent={consent}
              patientId={patientId}
            />
          ))}
        </div>
      )}

      <ConsentCreateForm
        patientId={patientId}
        open={consentFormOpen}
        onClose={() => setConsentFormOpen(false)}
      />
    </div>
  );
}

// -- Media Tab --
function MediaTab({
  patientId,
  media,
  isLoading,
  isError,
  error,
  onRetry,
}: {
  patientId: string;
  media: MediaAsset[] | undefined;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  onRetry: () => void;
}) {
  const originalityColors: Record<string, string> = {
    original:
      "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    reposted:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    disputed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Media Assets</h2>
        <Link
          to="/media/upload"
          className={cn(
            "inline-flex items-center gap-2 rounded-md bg-primary px-3 py-1.5",
            "text-sm font-medium text-primary-foreground shadow",
            "hover:bg-primary/90"
          )}
        >
          <Plus className="h-4 w-4" />
          Upload Media
        </Link>
      </div>

      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-48 animate-pulse rounded-lg border border-border bg-muted"
            />
          ))}
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="font-medium text-destructive">
                Failed to load media
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {error instanceof Error
                  ? error.message
                  : "An unexpected error occurred."}
              </p>
            </div>
            <button
              onClick={onRetry}
              className={cn(
                "rounded-md border border-destructive/50 px-3 py-1.5",
                "text-sm font-medium text-destructive hover:bg-destructive/10"
              )}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {!isLoading && !isError && media && media.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card p-12 text-center">
          <ImageIcon className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="font-medium text-muted-foreground">
            No media assets found.
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload media files to attach to this patient.
          </p>
        </div>
      )}

      {!isLoading && !isError && media && media.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {media.map((asset) => (
            <Link
              key={asset.id}
              to={`/media/${asset.id}`}
              className="group rounded-lg border border-border bg-card p-4 transition-colors hover:bg-accent/50"
            >
              <div className="flex h-24 items-center justify-center rounded-md bg-muted">
                <ImageIcon className="h-8 w-8 text-muted-foreground/50" />
              </div>
              <div className="mt-3 space-y-1">
                <p className="truncate text-sm font-medium group-hover:text-primary">
                  {asset.original_filename}
                </p>
                <div className="flex items-center justify-between">
                  <span
                    className={cn(
                      "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium capitalize",
                      originalityColors[asset.originality_status] ?? ""
                    )}
                  >
                    {asset.originality_status}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {asset.created_at}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function PatientDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <div className="h-9 w-9 animate-pulse rounded-md bg-muted" />
        <div className="flex-1 space-y-2">
          <div className="h-8 w-48 animate-pulse rounded bg-muted" />
          <div className="h-4 w-32 animate-pulse rounded bg-muted" />
        </div>
      </div>
      <div className="h-10 w-full animate-pulse rounded bg-muted" />
      <div className="h-64 animate-pulse rounded-lg border border-border bg-muted" />
    </div>
  );
}
