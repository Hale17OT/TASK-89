import { useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  ArrowLeft,
  Loader2,
  Camera,
  Upload,
  X,
  Image as ImageIcon,
} from "lucide-react";
import { createInfringement } from "@/api/endpoints/media";
import { cn } from "@/lib/utils";
import html2canvas from "html2canvas";

export function InfringementCreatePage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [screenshotBlob, setScreenshotBlob] = useState<Blob | null>(null);
  const [screenshotPreview, setScreenshotPreview] = useState<string | null>(
    null
  );
  const [referenceUrl, setReferenceUrl] = useState("");
  const [notes, setNotes] = useState("");
  const [isCapturing, setIsCapturing] = useState(false);

  const notesCount = notes.length;
  const hasEvidence = screenshotBlob !== null || referenceUrl.trim().length > 0;
  const canSubmit = notes.length >= 50 && hasEvidence;

  const mutation = useMutation({
    mutationFn: (formData: FormData) => createInfringement(formData),
    onSuccess: (data) => {
      toast.success("Infringement report submitted");
      navigate(`/infringements/${data.id}`);
    },
    onError: () => {
      toast.error("Failed to submit infringement report");
    },
  });

  const captureScreenshot = async () => {
    setIsCapturing(true);
    try {
      const canvas = await html2canvas(document.body);
      canvas.toBlob((blob) => {
        if (blob) {
          setScreenshotBlob(blob);
          setScreenshotPreview(URL.createObjectURL(blob));
        }
        setIsCapturing(false);
      });
    } catch {
      toast.error("Failed to capture screenshot");
      setIsCapturing(false);
    }
  };

  const handleFileUpload = (file: File) => {
    setScreenshotBlob(file);
    if (file.type.startsWith("image/")) {
      setScreenshotPreview(URL.createObjectURL(file));
    } else {
      setScreenshotPreview(null);
    }
  };

  const clearScreenshot = () => {
    if (screenshotPreview) {
      URL.revokeObjectURL(screenshotPreview);
    }
    setScreenshotBlob(null);
    setScreenshotPreview(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit || mutation.isPending) return;

    const formData = new FormData();
    if (screenshotBlob) {
      formData.append(
        "screenshot",
        screenshotBlob,
        screenshotBlob instanceof File ? screenshotBlob.name : "screenshot.png"
      );
    }
    formData.append("notes", notes);
    if (referenceUrl) formData.append("reference", referenceUrl);

    mutation.mutate(formData);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/infringements"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Report Infringement
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Submit an infringement report with evidence.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Screenshot Section */}
        <div className="rounded-lg border border-border bg-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Evidence Screenshot</h2>

          {!screenshotBlob ? (
            <div className="space-y-3">
              <button
                type="button"
                onClick={captureScreenshot}
                disabled={isCapturing}
                className={cn(
                  "inline-flex w-full items-center justify-center gap-2 rounded-md border-2 border-dashed border-border p-6",
                  "text-sm font-medium transition-colors",
                  "hover:border-primary/50 hover:bg-accent/50",
                  "disabled:pointer-events-none disabled:opacity-50"
                )}
              >
                {isCapturing ? (
                  <Loader2 className="h-5 w-5 animate-spin" />
                ) : (
                  <Camera className="h-5 w-5" />
                )}
                {isCapturing ? "Capturing..." : "Capture Screenshot"}
              </button>

              <div className="text-center text-xs text-muted-foreground">
                or
              </div>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className={cn(
                  "inline-flex w-full items-center justify-center gap-2 rounded-md border border-border p-4",
                  "text-sm font-medium hover:bg-accent"
                )}
              >
                <Upload className="h-4 w-4" />
                Upload Screenshot File
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFileUpload(f);
                }}
                className="hidden"
              />
            </div>
          ) : (
            <div className="space-y-3">
              <div className="relative rounded-md border border-border overflow-hidden">
                {screenshotPreview ? (
                  <img
                    src={screenshotPreview}
                    alt="Screenshot preview"
                    className="mx-auto max-h-48 object-contain"
                  />
                ) : (
                  <div className="flex h-24 items-center justify-center bg-muted">
                    <ImageIcon className="h-8 w-8 text-muted-foreground/50" />
                  </div>
                )}
                <button
                  type="button"
                  onClick={clearScreenshot}
                  className="absolute right-2 top-2 rounded-full bg-background/80 p-1 hover:bg-background"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
              <p className="text-xs text-muted-foreground">
                Screenshot attached.{" "}
                {screenshotBlob instanceof File && screenshotBlob.name}
              </p>
            </div>
          )}
        </div>

        {/* Reference */}
        <div className="rounded-lg border border-border bg-card p-6 space-y-2">
          <label className="text-sm font-medium">
            URL or Reference (optional)
          </label>
          <input
            type="text"
            value={referenceUrl}
            onChange={(e) => setReferenceUrl(e.target.value)}
            placeholder="URL, file path, or document reference number"
            className={cn(
              "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
              "text-sm placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            )}
            disabled={mutation.isPending}
          />
        </div>

        {/* Notes */}
        <div className="rounded-lg border border-border bg-card p-6 space-y-2">
          <label className="text-sm font-medium">
            Notes
            <span className="ml-1 text-destructive">*</span>
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Describe the infringement in detail (minimum 50 characters)..."
            rows={6}
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
                notesCount < 50
                  ? "text-muted-foreground"
                  : "text-green-600 dark:text-green-400"
              )}
            >
              {notesCount}/50 min
            </span>
          </div>
        </div>

        {/* Validation hint */}
        {!hasEvidence && (
          <p className="text-sm text-destructive">
            At least one of screenshot or reference URL must be provided.
          </p>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Link
            to="/infringements"
            className={cn(
              "inline-flex items-center justify-center rounded-md border border-border px-4 py-2",
              "text-sm font-medium hover:bg-accent"
            )}
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={!canSubmit || mutation.isPending}
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
            Submit Report
          </button>
        </div>
      </form>
    </div>
  );
}
