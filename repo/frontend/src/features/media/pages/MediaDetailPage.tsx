import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  AlertCircle,
  Download,
  Image as ImageIcon,
  UserPlus,
  AlertTriangle,
  Search,
  X,
} from "lucide-react";
import { getMedia, downloadMedia, attachMediaToPatient } from "@/api/endpoints/media";
import { searchPatients } from "@/api/endpoints/patients";
import { useAuth } from "@/contexts/AuthContext";
import { hasRole } from "@/lib/roles";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const originalityBanner: Record<
  string,
  { bg: string; text: string; label: string }
> = {
  original: {
    bg: "bg-green-50 border-green-200 dark:bg-green-950/50 dark:border-green-900",
    text: "text-green-800 dark:text-green-200",
    label: "Original Content",
  },
  reposted: {
    bg: "bg-blue-50 border-blue-200 dark:bg-blue-950/50 dark:border-blue-900",
    text: "text-blue-800 dark:text-blue-200",
    label: "Reposted Content — Authorization Required",
  },
  reposted_authorized: {
    bg: "bg-teal-50 border-teal-200 dark:bg-teal-950/50 dark:border-teal-900",
    text: "text-teal-800 dark:text-teal-200",
    label: "Reposted Content — Authorized with Citation",
  },
  disputed: {
    bg: "bg-red-50 border-red-200 dark:bg-red-950/50 dark:border-red-900",
    text: "text-red-800 dark:text-red-200",
    label: "Disputed Content",
  },
};

export function MediaDetailPage() {
  const { mediaId: id } = useParams<{ mediaId: string }>();
  const { user } = useAuth();

  const { data: media, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["media", id],
    queryFn: () => getMedia(id!),
    enabled: !!id,
  });

  const queryClient = useQueryClient();
  const [showAttachDialog, setShowAttachDialog] = useState(false);
  const [patientSearch, setPatientSearch] = useState("");
  const [patientResults, setPatientResults] = useState<{ id: string; display_name: string }[]>([]);
  const [searchingPatients, setSearchingPatients] = useState(false);

  const attachMutation = useMutation({
    mutationFn: ({ mediaId, patientId }: { mediaId: string; patientId: string }) =>
      attachMediaToPatient(mediaId, patientId),
    onSuccess: () => {
      toast.success("Media attached to patient");
      setShowAttachDialog(false);
      setPatientSearch("");
      setPatientResults([]);
      queryClient.invalidateQueries({ queryKey: ["media", id] });
    },
    onError: () => {
      toast.error("Failed to attach media to patient");
    },
  });

  const handlePatientSearch = async (query: string) => {
    setPatientSearch(query);
    if (query.length < 2) {
      setPatientResults([]);
      return;
    }
    setSearchingPatients(true);
    try {
      const results = await searchPatients(query);
      setPatientResults(
        results.map((p) => ({ id: p.id, display_name: p.name || p.id }))
      );
    } catch {
      setPatientResults([]);
    } finally {
      setSearchingPatients(false);
    }
  };

  const handleAttachPatient = (patientId: string) => {
    if (!id) return;
    attachMutation.mutate({ mediaId: id, patientId });
  };

  const handleDownload = async () => {
    if (!id || !media) return;
    try {
      const blob = await downloadMedia(id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = media.original_filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Failed to download file");
    }
  };

  const canAttachPatient = user && hasRole(user.role, ["front_desk", "clinician", "admin"]);

  if (isLoading) {
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="flex items-center gap-4">
          <div className="h-9 w-9 animate-pulse rounded-md bg-muted" />
          <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-12 animate-pulse rounded-lg bg-muted" />
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
        <div className="h-48 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <Link
          to="/media"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Media Library
        </Link>
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
              onClick={() => refetch()}
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

  if (!media) return null;

  const banner = originalityBanner[media.originality_status];
  const needsRepostAuth =
    media.originality_status === "reposted" && !media.repost_authorized;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/media"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">
            {media.original_filename}
          </h1>
        </div>
        <button
          onClick={handleDownload}
          className={cn(
            "inline-flex items-center gap-2 rounded-md border border-border px-4 py-2",
            "text-sm font-medium hover:bg-accent"
          )}
        >
          <Download className="h-4 w-4" />
          Download
        </button>
      </div>

      {/* Originality Banner */}
      {banner && (
        <div className={cn("rounded-lg border p-4", banner.bg)}>
          <p className={cn("text-center font-semibold", banner.text)}>
            {banner.label}
          </p>
        </div>
      )}

      {/* Repost Authorization Warning */}
      {needsRepostAuth && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-950/50">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-yellow-600 dark:text-yellow-400" />
            <div className="flex-1">
              <p className="font-medium text-yellow-800 dark:text-yellow-200">
                Repost Authorization Required
              </p>
              <p className="mt-1 text-sm text-yellow-700 dark:text-yellow-300">
                This content has been identified as reposted. Authorization with
                proper citation is required.
              </p>
            </div>
            <Link
              to={`/media/${id}/repost`}
              className={cn(
                "inline-flex items-center rounded-md bg-yellow-600 px-3 py-1.5",
                "text-sm font-medium text-white hover:bg-yellow-700"
              )}
            >
              Authorize Repost
            </Link>
          </div>
        </div>
      )}

      {/* Image Viewer */}
      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex min-h-[300px] items-center justify-center rounded-md bg-muted">
          {media.mime_type.startsWith("image/") ? (
            <img
              src={`/api/v1/media/${media.id}/download/`}
              alt={media.original_filename}
              className="max-h-[500px] max-w-full object-contain"
            />
          ) : (
            <div className="text-center">
              <ImageIcon className="mx-auto h-16 w-16 text-muted-foreground/40" />
              <p className="mt-2 text-sm text-muted-foreground">
                Preview not available for {media.mime_type}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Metadata Card */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-4 py-3">
          <h2 className="font-semibold">Metadata</h2>
        </div>
        <div className="grid gap-px sm:grid-cols-2">
          <MetadataRow label="Filename" value={media.original_filename} />
          <MetadataRow label="MIME Type" value={media.mime_type} />
          <MetadataRow
            label="File Size"
            value={formatBytes(media.file_size_bytes)}
          />
          <MetadataRow label="Pixel Hash" value={media.pixel_hash} mono />
          <MetadataRow
            label="Watermarked"
            value={media.watermark_burned ? "Yes" : "No"}
          />
          <MetadataRow
            label="Originality"
            value={media.originality_status}
          />
          <MetadataRow label="Uploaded" value={media.created_at} />
          {media.patient_id && (
            <MetadataRow label="Patient ID" value={media.patient_id} />
          )}
        </div>
        {media.evidence_metadata &&
          Object.keys(media.evidence_metadata).length > 0 && (
            <div className="border-t border-border px-4 py-3">
              <h3 className="mb-2 text-sm font-medium text-muted-foreground">
                Evidence Metadata
              </h3>
              <pre className="rounded-md bg-muted p-3 text-xs overflow-auto">
                {JSON.stringify(media.evidence_metadata, null, 2)}
              </pre>
            </div>
          )}
      </div>

      {/* Clinician action */}
      {canAttachPatient && !media.patient_id && (
        <div className="flex justify-end">
          <button
            onClick={() => setShowAttachDialog(true)}
            className={cn(
              "inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2",
              "text-sm font-medium text-primary-foreground shadow",
              "hover:bg-primary/90"
            )}
          >
            <UserPlus className="h-4 w-4" />
            Attach to Patient
          </button>
        </div>
      )}

      {/* Attach to Patient Dialog */}
      {showAttachDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-lg font-semibold">Attach to Patient</h3>
              <button
                onClick={() => {
                  setShowAttachDialog(false);
                  setPatientSearch("");
                  setPatientResults([]);
                }}
                className="rounded-md p-1 hover:bg-accent"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="relative mb-4">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search patients..."
                value={patientSearch}
                onChange={(e) => handlePatientSearch(e.target.value)}
                className={cn(
                  "w-full rounded-md border border-border bg-background py-2 pl-9 pr-3",
                  "text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                )}
                autoFocus
              />
            </div>
            <div className="max-h-60 overflow-y-auto">
              {searchingPatients && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  Searching...
                </p>
              )}
              {!searchingPatients && patientSearch.length >= 2 && patientResults.length === 0 && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No patients found
                </p>
              )}
              {patientResults.map((p) => (
                <button
                  key={p.id}
                  onClick={() => handleAttachPatient(p.id)}
                  disabled={attachMutation.isPending}
                  className={cn(
                    "w-full rounded-md px-3 py-2 text-left text-sm hover:bg-accent",
                    "flex items-center justify-between"
                  )}
                >
                  <span>{p.display_name}</span>
                  <span className="text-xs text-muted-foreground">
                    {p.id.slice(0, 8)}...
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MetadataRow({
  label,
  value,
  mono,
}: {
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="flex items-center justify-between border-b border-border px-4 py-2.5 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span
        className={cn(
          "text-sm font-medium capitalize",
          mono && "font-mono text-xs"
        )}
      >
        {value}
      </span>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}
