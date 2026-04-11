import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Loader2, ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { createPatient } from "@/api/endpoints/patients";
import type { CreatePatientPayload } from "@/api/types/patient.types";
import { cn } from "@/lib/utils";
import axios from "axios";

const patientSchema = z.object({
  mrn: z.string().min(1, "MRN is required"),
  ssn: z.string().optional(),
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  date_of_birth: z.string().min(1, "Date of birth is required"),
  gender: z.string().min(1, "Gender is required"),
  phone: z.string().optional(),
  email: z.string().optional(),
  address: z.string().optional(),
});

type PatientFormData = z.infer<typeof patientSchema>;

export function PatientCreatePage() {
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<PatientFormData>({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      gender: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (data: CreatePatientPayload) => createPatient(data),
    onSuccess: (patient) => {
      toast.success("Patient created successfully");
      navigate(`/patients/${patient.id}`);
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.data) {
        const serverErrors = error.response.data as Record<string, string[]>;
        for (const [field, messages] of Object.entries(serverErrors)) {
          if (field in patientSchema.shape) {
            setError(field as keyof PatientFormData, {
              message: Array.isArray(messages) ? messages[0] : String(messages),
            });
          }
        }
        if (serverErrors.detail) {
          toast.error(
            Array.isArray(serverErrors.detail)
              ? serverErrors.detail[0]
              : String(serverErrors.detail)
          );
        }
      } else {
        toast.error("Failed to create patient. Please try again.");
      }
    },
  });

  const onSubmit = (data: PatientFormData) => {
    const payload: CreatePatientPayload = {
      mrn: data.mrn,
      first_name: data.first_name,
      last_name: data.last_name,
      date_of_birth: data.date_of_birth,
      gender: data.gender,
      ...(data.ssn ? { ssn: data.ssn } : {}),
      ...(data.phone ? { phone: data.phone } : {}),
      ...(data.email ? { email: data.email } : {}),
      ...(data.address ? { address: data.address } : {}),
    };
    mutation.mutate(payload);
  };

  const inputCn = cn(
    "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2",
    "text-sm placeholder:text-muted-foreground",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    "disabled:cursor-not-allowed disabled:opacity-50"
  );

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/patients"
          className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border hover:bg-accent"
        >
          <ArrowLeft className="h-4 w-4" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            Register New Patient
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Enter the patient's demographic information.
          </p>
        </div>
      </div>

      {/* Form */}
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-6 rounded-lg border border-border bg-card p-6"
      >
        {/* MRN & SSN */}
        <div className="grid gap-4 sm:grid-cols-2">
          <FieldWrapper label="MRN" error={errors.mrn?.message} required>
            <input
              {...register("mrn")}
              placeholder="Medical Record Number"
              className={inputCn}
              disabled={mutation.isPending}
            />
          </FieldWrapper>
          <FieldWrapper label="SSN" error={errors.ssn?.message}>
            <input
              {...register("ssn")}
              placeholder="Social Security Number"
              className={inputCn}
              disabled={mutation.isPending}
            />
          </FieldWrapper>
        </div>

        {/* Name */}
        <div className="grid gap-4 sm:grid-cols-2">
          <FieldWrapper
            label="First Name"
            error={errors.first_name?.message}
            required
          >
            <input
              {...register("first_name")}
              placeholder="First name"
              className={inputCn}
              disabled={mutation.isPending}
            />
          </FieldWrapper>
          <FieldWrapper
            label="Last Name"
            error={errors.last_name?.message}
            required
          >
            <input
              {...register("last_name")}
              placeholder="Last name"
              className={inputCn}
              disabled={mutation.isPending}
            />
          </FieldWrapper>
        </div>

        {/* DOB & Gender */}
        <div className="grid gap-4 sm:grid-cols-2">
          <FieldWrapper
            label="Date of Birth"
            error={errors.date_of_birth?.message}
            required
          >
            <input
              type="date"
              {...register("date_of_birth")}
              className={inputCn}
              disabled={mutation.isPending}
            />
          </FieldWrapper>
          <FieldWrapper
            label="Gender"
            error={errors.gender?.message}
            required
          >
            <select
              {...register("gender")}
              className={inputCn}
              disabled={mutation.isPending}
            >
              <option value="">Select gender</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
              <option value="unknown">Unknown</option>
            </select>
          </FieldWrapper>
        </div>

        {/* Contact */}
        <div className="grid gap-4 sm:grid-cols-2">
          <FieldWrapper label="Phone" error={errors.phone?.message}>
            <input
              {...register("phone")}
              placeholder="Phone number"
              className={inputCn}
              disabled={mutation.isPending}
            />
          </FieldWrapper>
          <FieldWrapper label="Email" error={errors.email?.message}>
            <input
              type="email"
              {...register("email")}
              placeholder="Email address"
              className={inputCn}
              disabled={mutation.isPending}
            />
          </FieldWrapper>
        </div>

        {/* Address */}
        <FieldWrapper label="Address" error={errors.address?.message}>
          <textarea
            {...register("address")}
            placeholder="Full address"
            rows={3}
            className={cn(
              inputCn,
              "h-auto min-h-[80px] resize-none"
            )}
            disabled={mutation.isPending}
          />
        </FieldWrapper>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Link
            to="/patients"
            className={cn(
              "inline-flex items-center justify-center rounded-md border border-border px-4 py-2",
              "text-sm font-medium hover:bg-accent"
            )}
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={mutation.isPending}
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2",
              "text-sm font-medium text-primary-foreground shadow",
              "hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              "disabled:pointer-events-none disabled:opacity-50"
            )}
          >
            {mutation.isPending && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
            Create Patient
          </button>
        </div>
      </form>
    </div>
  );
}

function FieldWrapper({
  label,
  error,
  required,
  children,
}: {
  label: string;
  error?: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium leading-none">
        {label}
        {required && <span className="ml-1 text-destructive">*</span>}
      </label>
      {children}
      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  );
}
