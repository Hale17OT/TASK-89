import { useState, useRef, useCallback } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { ArrowLeft, Upload, X, Loader2, Image as ImageIcon } from "lucide-react";
import { uploadMedia, applyWatermark } from "@/api/endpoints/media";
import { cn } from "@/lib/utils";

export function MediaUploadPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [clinicName, setClinicName] = useState("");
  const [dateStamp, setDateStamp] = useState(true);
  const [opacity, setOpacity] = useState(35);
  const [patientId, setPatientId] = useState("");
  const [isDragging, setIsDragging] = useState(false);

  const handleFile = useCallback((f: File) => {
    setFile(f);
    if (f.type.startsWith("image/")) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    } else {
      setPreview(null);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const f = e.dataTransfer.files[0];
      if (f) handleFile(f);
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const removeFile = () => {
    setFile(null);
    if (preview) {
      URL.revokeObjectURL(preview);
      setPreview(null);
    }
  };

  const mutation = useMutation({
    mutationFn: async (formData: FormData) => {
      const asset = await uploadMedia(formData);

      // If watermark was configured, trigger the watermark burn
      const watermarkConfig = {
        clinic_name: clinicName,
        date_stamp: dateStamp,
        opacity: opacity / 100,
      };
      if (clinicName || dateStamp) {
        try {
          await applyWatermark(asset.id, watermarkConfig);
        } catch {
          toast.error("Media uploaded but watermark application failed");
        }
      }

      return asset;
    },
    onSuccess: (data) => {
      toast.success("Media uploaded successfully");
      navigate(`/media/${data.id}`);
    },
    onError: () => {
      toast.error("Failed to upload media");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);
    const watermarkConfig = {
      clinic_name: clinicName,
      date_stamp: dateStamp,
      opacity: opacity / 100,
    };
    formData.append("watermark_config", JSON.stringify(watermarkConfig));
    if (patientId) formData.append("patient_id", patientId);

    mutation.mutate(formData);
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/media"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Upload Media</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload an image file with optional watermark configuration.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Dropzone */}
        {!file ? (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors",
              isDragging
                ? "border-primary bg-primary/5"
                : "border-border hover:border-primary/50 hover:bg-accent/50"
            )}
          >
            <Upload className="mb-4 h-10 w-10 text-muted-foreground" />
            <p className="text-sm font-medium">
              Drag and drop a file here, or click to browse
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Supported formats: JPEG, PNG
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/jpeg,image/png,.jpg,.jpeg,.png"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) handleFile(f);
              }}
              className="hidden"
            />
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <ImageIcon className="h-5 w-5 text-muted-foreground" />
                <div>
                  <p className="text-sm font-medium">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={removeFile}
                className="rounded-md p-1 hover:bg-accent"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Preview with watermark overlay */}
            {preview && (
              <div className="relative mt-4 overflow-hidden rounded-md bg-muted">
                <img
                  src={preview}
                  alt="Preview"
                  className="mx-auto max-h-80 object-contain"
                />
                {/* Watermark preview overlay */}
                {clinicName && (
                  <div
                    className="pointer-events-none absolute inset-0 flex items-center justify-center"
                    style={{ opacity: opacity / 100 }}
                  >
                    <div className="rotate-[-30deg] select-none text-center">
                      <p className="whitespace-nowrap text-3xl font-bold text-white drop-shadow-lg">
                        {clinicName}
                      </p>
                      {dateStamp && (
                        <p className="mt-1 text-sm text-white drop-shadow-lg">
                          {new Date().toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Watermark Controls */}
        <div className="rounded-lg border border-border bg-card p-6 space-y-4">
          <h2 className="text-lg font-semibold">Watermark Settings</h2>

          <div className="space-y-2">
            <label className="text-sm font-medium">Clinic Name</label>
            <input
              type="text"
              value={clinicName}
              onChange={(e) => setClinicName(e.target.value)}
              placeholder="Enter clinic name for watermark"
              className={cn(
                "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
                "text-sm placeholder:text-muted-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              )}
              disabled={mutation.isPending}
            />
          </div>

          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={dateStamp}
              onChange={(e) => setDateStamp(e.target.checked)}
              className="h-4 w-4 rounded border-input"
              disabled={mutation.isPending}
            />
            <span className="text-sm">Include date stamp</span>
          </label>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">
                Opacity: {opacity}%
              </label>
            </div>
            <input
              type="range"
              min={5}
              max={100}
              value={opacity}
              onChange={(e) => setOpacity(Number(e.target.value))}
              className="w-full accent-primary"
              disabled={mutation.isPending}
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>5%</span>
              <span>100%</span>
            </div>
          </div>
        </div>

        {/* Patient Selector */}
        <div className="rounded-lg border border-border bg-card p-6 space-y-2">
          <label className="text-sm font-medium">
            Patient ID (optional)
          </label>
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Enter patient ID to associate this media"
            className={cn(
              "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
              "text-sm placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            )}
            disabled={mutation.isPending}
          />
        </div>

        {/* Upload result banner */}
        {mutation.isSuccess && mutation.data && (
          <div
            className={cn(
              "rounded-lg border p-4 text-center",
              mutation.data.originality_status === "original"
                ? "border-green-200 bg-green-50 text-green-800 dark:border-green-900 dark:bg-green-950/50 dark:text-green-200"
                : "border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-900 dark:bg-blue-950/50 dark:text-blue-200"
            )}
          >
            <p className="font-medium capitalize">
              Originality: {mutation.data.originality_status}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3">
          <Link
            to="/media"
            className={cn(
              "inline-flex items-center justify-center rounded-md border border-border px-4 py-2",
              "text-sm font-medium hover:bg-accent"
            )}
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={!file || mutation.isPending}
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
            Upload Media
          </button>
        </div>
      </form>
    </div>
  );
}
