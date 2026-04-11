import { useState, useRef } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  Loader2,
  Upload,
  X,
  Image as ImageIcon,
  AlertCircle,
} from "lucide-react";
import { getMedia, authorizeRepost } from "@/api/endpoints/media";
import { cn } from "@/lib/utils";

export function RepostFlowPage() {
  const { mediaId: id } = useParams<{ mediaId: string }>();
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [citation, setCitation] = useState("");
  const [authFile, setAuthFile] = useState<File | null>(null);

  const mediaQuery = useQuery({
    queryKey: ["media", id],
    queryFn: () => getMedia(id!),
    enabled: !!id,
  });

  const mutation = useMutation({
    mutationFn: (formData: FormData) => authorizeRepost(id!, formData),
    onSuccess: () => {
      toast.success("Repost authorized successfully");
      navigate(`/media/${id}`);
    },
    onError: () => {
      toast.error("Failed to authorize repost");
    },
  });

  const charCount = citation.length;
  const canSubmit =
    citation.length >= 20 && authFile !== null && !mutation.isPending;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    const formData = new FormData();
    formData.append("citation_text", citation);
    formData.append("authorization_file", authFile!);

    mutation.mutate(formData);
  };

  if (mediaQuery.isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <div className="flex items-center gap-4">
          <div className="h-9 w-9 animate-pulse rounded-md bg-muted" />
          <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (mediaQuery.isError) {
    return (
      <div className="mx-auto max-w-2xl space-y-6">
        <Link
          to="/media"
          className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Media
        </Link>
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="font-medium text-destructive">
              Failed to load media
            </p>
          </div>
        </div>
      </div>
    );
  }

  const media = mediaQuery.data;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to={`/media/${id}`}
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Authorize Repost
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Provide citation and authorization for reposted content.
          </p>
        </div>
      </div>

      {/* Original Media Thumbnail */}
      {media && (
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-4">
            <div className="flex h-20 w-20 items-center justify-center rounded-md bg-muted">
              <ImageIcon className="h-8 w-8 text-muted-foreground/40" />
            </div>
            <div>
              <p className="font-medium">{media.original_filename}</p>
              <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                Reposted
              </span>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Citation */}
        <div className="rounded-lg border border-border bg-card p-6 space-y-2">
          <label className="text-sm font-medium">
            Citation
            <span className="ml-1 text-destructive">*</span>
          </label>
          <textarea
            value={citation}
            onChange={(e) => setCitation(e.target.value)}
            placeholder="Provide proper citation for the original source of this content (minimum 20 characters)..."
            rows={5}
            className={cn(
              "flex w-full rounded-md border border-input bg-background px-3 py-2",
              "text-sm placeholder:text-muted-foreground resize-none",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              "disabled:cursor-not-allowed disabled:opacity-50"
            )}
            disabled={mutation.isPending}
          />
          <div className="flex justify-end">
            <span
              className={cn(
                "text-xs",
                charCount < 20
                  ? "text-muted-foreground"
                  : "text-green-600 dark:text-green-400"
              )}
            >
              {charCount}/20 min
            </span>
          </div>
        </div>

        {/* Authorization File Upload */}
        <div className="rounded-lg border border-border bg-card p-6 space-y-2">
          <label className="text-sm font-medium">
            Authorization Document
            <span className="ml-1 text-destructive">*</span>
          </label>
          {!authFile ? (
            <div
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-border p-8",
                "hover:border-primary/50 hover:bg-accent/50 transition-colors"
              )}
            >
              <Upload className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-sm font-medium">
                Click to upload authorization document
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                PDF, JPEG, or PNG
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,image/*"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setAuthFile(f);
                }}
                className="hidden"
              />
            </div>
          ) : (
            <div className="flex items-center justify-between rounded-md border border-border p-3">
              <div className="flex items-center gap-2">
                <Upload className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">{authFile.name}</span>
                <span className="text-xs text-muted-foreground">
                  ({(authFile.size / 1024).toFixed(1)} KB)
                </span>
              </div>
              <button
                type="button"
                onClick={() => setAuthFile(null)}
                className="rounded-md p-1 hover:bg-accent"
                disabled={mutation.isPending}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Link
            to={`/media/${id}`}
            className={cn(
              "inline-flex items-center justify-center rounded-md border border-border px-4 py-2",
              "text-sm font-medium hover:bg-accent"
            )}
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={!canSubmit}
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2",
              "text-sm font-medium text-primary-foreground shadow",
              "hover:bg-primary/90",
              "disabled:pointer-events-none disabled:opacity-50"
            )}
          >
            {mutation.isPending && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
            Submit Authorization
          </button>
        </div>
      </form>
    </div>
  );
}
