import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Search, Plus, AlertCircle, Users } from "lucide-react";
import { searchPatients } from "@/api/endpoints/patients";
import { cn } from "@/lib/utils";

export function PatientSearchPage() {
  const [inputValue, setInputValue] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(inputValue);
    }, 300);
    return () => clearTimeout(timer);
  }, [inputValue]);

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["patients", "search", debouncedQuery],
    queryFn: () => searchPatients(debouncedQuery),
    enabled: debouncedQuery.length > 0,
  });

  const patients = data ?? [];
  const hasSearched = debouncedQuery.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Patients</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Search for patient records by name, MRN, or other criteria.
          </p>
        </div>
        <Link
          to="/patients/new"
          className={cn(
            "inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2",
            "text-sm font-medium text-primary-foreground shadow",
            "hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          )}
        >
          <Plus className="h-4 w-4" />
          Create Patient
        </Link>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search by name, MRN, or date of birth..."
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className={cn(
            "flex h-10 w-full rounded-md border border-input bg-background px-10 py-2",
            "text-sm placeholder:text-muted-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          )}
        />
      </div>

      {/* Results Area */}
      {!hasSearched && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card p-12 text-center">
          <Users className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="text-muted-foreground">
            Enter a search term above to find patients.
          </p>
        </div>
      )}

      {hasSearched && isLoading && <SkeletonTable />}

      {hasSearched && isError && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-6">
          <div className="flex items-center gap-3">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <div className="flex-1">
              <p className="font-medium text-destructive">
                Failed to search patients
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
                "text-sm font-medium text-destructive",
                "hover:bg-destructive/10"
              )}
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {hasSearched && !isLoading && !isError && patients.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-card p-12 text-center">
          <Search className="mb-4 h-12 w-12 text-muted-foreground/50" />
          <p className="font-medium text-muted-foreground">
            No patients found.
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            Try a different search term.
          </p>
        </div>
      )}

      {hasSearched && !isLoading && !isError && patients.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  MRN
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Name
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  DOB
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Gender
                </th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                  Status
                </th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr
                  key={patient.id}
                  className="border-b border-border last:border-0 hover:bg-muted/50 transition-colors"
                >
                  <td className="px-4 py-3 font-mono text-sm">
                    <Link
                      to={`/patients/${patient.id}`}
                      className="text-primary underline-offset-4 hover:underline"
                    >
                      {patient.mrn}
                    </Link>
                  </td>
                  <td className="px-4 py-3">{patient.name}</td>
                  <td className="px-4 py-3">{patient.date_of_birth}</td>
                  <td className="px-4 py-3 capitalize">{patient.gender}</td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                        patient.is_active
                          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                          : "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400"
                      )}
                    >
                      {patient.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function SkeletonTable() {
  return (
    <div className="overflow-hidden rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border bg-muted/50">
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              MRN
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Name
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              DOB
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Gender
            </th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: 5 }).map((_, i) => (
            <tr key={i} className="border-b border-border last:border-0">
              <td className="px-4 py-3">
                <div className="h-4 w-20 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-32 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-24 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-16 animate-pulse rounded bg-muted" />
              </td>
              <td className="px-4 py-3">
                <div className="h-4 w-16 animate-pulse rounded bg-muted" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
