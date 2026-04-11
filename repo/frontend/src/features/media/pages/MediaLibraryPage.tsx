import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  Upload,
  AlertCircle,
  Image as ImageIcon,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { listMedia } from "@/api/endpoints/media";
import { cn } from "@/lib/utils";

const PAGE_SIZE = 12;

const ORIGINALITY_OPTIONS = [
  { value: "", label: "All" },
  { value: "original", label: "Original" },
  { value: "reposted", label: "Reposted" },
  { value: "disputed", label: "Disputed" },
] as const;

const originalityColors: Record<string, string> = {
  original:
    "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
  reposted:
    "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
  disputed: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
};

export function MediaLibraryPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);

  const params: Record<string, string | number | undefined> = {
    page,
    page_size: PAGE_SIZE,
  };
  if (search) params.search = search;
  if (statusFilter) params.originality_status = statusFilter;

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["media", params],
    queryFn: () => listMedia(params),
  });

  const media = data?.results ?? [];
  const totalCount = data?.count ?? 0;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Media Library</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Browse and manage uploaded media assets.
          </p>
        </div>
        <Link
          to="/media/upload"
          className={cn(
            "inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2",
            "text-sm font-medium text-primary-foreground shadow",
            "hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          )}
        >
          <Upload className="h-4 w-4" />
          Upload
        </Link>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
            }}
            className={cn(
              "flex h-10 w-full rounded-md border border-input bg-background pl-10 pr-3 py-2",
              "text-sm placeholder:text-muted-foreground",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            )}
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className={cn(
            "flex h-10 rounded-md border border-input bg-background px-3 py-2",
            "text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          )}
        >
          {ORIGINALITY_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div
              key={i}
              className="animate-pulse rounded-lg border border-border bg-muted"
            >
              <div className="h-40 rounded-t-lg bg-muted" />
              <div className="space-y-2 p-3">
                <div className="h-4 w-3/4 rounded bg-background/50" />
                <div className="h-3 w-1/2 rounded bg-background/50" />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error */}
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
      )}

      {/* Empty */}
      {!isLoading && !isError && media.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card p-12 text-center">
          <ImageIcon className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="font-medium text-muted-foreground">
            No media assets found.
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            {search || statusFilter
              ? "Try adjusting your filters."
              : "Upload media to get started."}
          </p>
        </div>
      )}

      {/* Grid */}
      {!isLoading && !isError && media.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {media.map((asset) => (
              <Link
                key={asset.id}
                to={`/media/${asset.id}`}
                className="group rounded-lg border border-border bg-card transition-colors hover:bg-accent/50"
              >
                <div className="flex h-40 items-center justify-center rounded-t-lg bg-muted">
                  <ImageIcon className="h-10 w-10 text-muted-foreground/40" />
                </div>
                <div className="space-y-2 p-3">
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
                    {asset.watermark_burned && (
                      <span className="text-xs text-muted-foreground">
                        Watermarked
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {(page - 1) * PAGE_SIZE + 1} to{" "}
                {Math.min(page * PAGE_SIZE, totalCount)} of {totalCount} results
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className={cn(
                    "inline-flex h-9 w-9 items-center justify-center rounded-md border border-border",
                    "hover:bg-accent disabled:pointer-events-none disabled:opacity-50"
                  )}
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <span className="text-sm">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() =>
                    setPage((p) => Math.min(totalPages, p + 1))
                  }
                  disabled={page === totalPages}
                  className={cn(
                    "inline-flex h-9 w-9 items-center justify-center rounded-md border border-border",
                    "hover:bg-accent disabled:pointer-events-none disabled:opacity-50"
                  )}
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
