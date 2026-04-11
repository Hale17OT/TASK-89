import { useParams, useNavigate, Link } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2, ArrowLeft, AlertCircle } from "lucide-react";
import { toast } from "sonner";
import { getPatient, updatePatient } from "@/api/endpoints/patients";
import { cn } from "@/lib/utils";

const editSchema = z.object({
  first_name: z.string().optional(),
  last_name: z.string().optional(),
  date_of_birth: z.string().optional(),
  gender: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email("Invalid email").optional().or(z.literal("")),
  address: z.string().optional(),
});

type EditFormValues = z.infer<typeof editSchema>;

export function PatientEditPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: patient, isLoading, isError } = useQuery({
    queryKey: ["patient", patientId],
    queryFn: () => getPatient(patientId!),
    enabled: !!patientId,
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EditFormValues>({
    resolver: zodResolver(editSchema),
  });

  const mutation = useMutation({
    mutationFn: (data: EditFormValues) => {
      const payload: Record<string, string> = {};
      for (const [k, v] of Object.entries(data)) {
        if (v !== undefined && v !== "") payload[k] = v;
      }
      return updatePatient(patientId!, payload);
    },
    onSuccess: () => {
      toast.success("Patient record updated");
      queryClient.invalidateQueries({ queryKey: ["patient", patientId] });
      navigate(`/patients/${patientId}`);
    },
    onError: (err: Error) => {
      toast.error(`Update failed: ${err.message}`);
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded-md bg-muted" />
        <div className="h-64 animate-pulse rounded-md bg-muted" />
      </div>
    );
  }

  if (isError || !patient) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-6 text-center">
        <AlertCircle className="mx-auto h-8 w-8 text-destructive" />
        <p className="mt-2 text-destructive">Failed to load patient record.</p>
        <Link to="/patients" className="mt-2 inline-block text-sm underline">Back to search</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link to={`/patients/${patientId}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back
        </Link>
        <h1 className="text-2xl font-bold">Edit Patient</h1>
      </div>

      <div className="rounded-md border border-amber-500/50 bg-amber-50 p-4 text-sm dark:bg-amber-950">
        Note: Only fields you fill in will be updated. Leave fields blank to keep existing values. MRN and SSN cannot be changed here.
      </div>

      <form onSubmit={handleSubmit((data) => mutation.mutate(data))} className="space-y-6">
        <div className="rounded-lg border bg-card p-6 shadow-sm space-y-4">
          {([
            { name: "first_name" as const, label: "First Name" },
            { name: "last_name" as const, label: "Last Name" },
            { name: "date_of_birth" as const, label: "Date of Birth", type: "date" },
            { name: "gender" as const, label: "Gender", isSelect: true },
            { name: "phone" as const, label: "Phone" },
            { name: "email" as const, label: "Email", type: "email" },
            { name: "address" as const, label: "Address" },
          ] as const).map((field) => (
            <div key={field.name}>
              <label htmlFor={field.name} className="block text-sm font-medium mb-1.5">{field.label}</label>
              {"isSelect" in field && field.isSelect ? (
                <select
                  id={field.name}
                  {...register(field.name)}
                  className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">-- No change --</option>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="X">Non-binary</option>
                  <option value="U">Unknown</option>
                </select>
              ) : (
                <input
                  id={field.name}
                  type={"type" in field ? field.type : "text"}
                  {...register(field.name)}
                  className={cn(
                    "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
                    errors[field.name] && "border-destructive"
                  )}
                />
              )}
              {errors[field.name] && (
                <p className="mt-1 text-sm text-destructive">{errors[field.name]?.message}</p>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3">
          <Link to={`/patients/${patientId}`} className="rounded-md border px-4 py-2 text-sm hover:bg-muted">Cancel</Link>
          <button type="submit" disabled={mutation.isPending} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
            {mutation.isPending && <Loader2 className="mr-2 inline h-4 w-4 animate-spin" />}
            Save Changes
          </button>
        </div>
      </form>
    </div>
  );
}
