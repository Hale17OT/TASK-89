import { useNavigate, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { createSubscription } from "@/api/endpoints/reports";

const REPORT_TYPES = [
  { value: "daily_reconciliation", label: "Daily Reconciliation" },
  { value: "consent_expiry", label: "Consent Expiry" },
  { value: "break_glass_review", label: "Break Glass Review" },
  { value: "media_originality", label: "Media Originality" },
  { value: "financial_summary", label: "Financial Summary" },
  { value: "audit_activity", label: "Audit Activity" },
] as const;

const DAYS_OF_WEEK = [
  { value: 0, label: "Monday" },
  { value: 1, label: "Tuesday" },
  { value: 2, label: "Wednesday" },
  { value: 3, label: "Thursday" },
  { value: 4, label: "Friday" },
  { value: 5, label: "Saturday" },
  { value: 6, label: "Sunday" },
] as const;

const subscriptionSchema = z
  .object({
    name: z.string().min(1, "Name is required"),
    report_type: z.string().min(1, "Report type is required"),
    schedule: z.enum(["daily", "weekly"]),
    run_day_of_week: z.coerce.number().min(0).max(6).optional(),
    run_time: z.string().min(1, "Run time is required"),
    output_format: z.enum(["pdf", "excel", "image"]),
    delivery_target: z.enum(["shared_folder", "print_queue"]),
    delivery_path: z.string().optional(),
  })
  .refine(
    (data) =>
      data.schedule !== "weekly" || data.run_day_of_week !== undefined,
    { message: "Day of week is required for weekly schedules", path: ["run_day_of_week"] }
  );

type SubscriptionFormValues = z.infer<typeof subscriptionSchema>;

export function SubscriptionCreatePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<SubscriptionFormValues>({
    resolver: zodResolver(subscriptionSchema),
    defaultValues: {
      name: "",
      report_type: "",
      schedule: "daily",
      run_day_of_week: undefined,
      run_time: "08:00",
      output_format: "pdf",
      delivery_target: "shared_folder",
      delivery_path: "",
    },
  });

  const schedule = watch("schedule");

  const mutation = useMutation({
    mutationFn: (data: SubscriptionFormValues) => {
      const payload: Record<string, unknown> = {
        name: data.name,
        report_type: data.report_type,
        schedule: data.schedule,
        run_time: data.run_time,
        output_format: data.output_format,
        parameters: {
          delivery_target: data.delivery_target,
          delivery_path: data.delivery_path || "",
        },
      };
      if (data.schedule === "weekly" && data.run_day_of_week !== undefined) {
        payload.run_day_of_week = data.run_day_of_week;
      }
      return createSubscription(payload as Partial<any>);
    },
    onSuccess: () => {
      toast.success("Subscription created successfully");
      queryClient.invalidateQueries({ queryKey: ["subscriptions"] });
      navigate("/reports");
    },
    onError: (err: Error) => {
      toast.error(`Failed to create subscription: ${err.message}`);
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/reports"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">
          New Subscription
        </h1>
      </div>

      <form
        onSubmit={handleSubmit((data) => mutation.mutate(data))}
        className="space-y-6"
      >
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm space-y-6">
          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium mb-1.5">
              Name
            </label>
            <input
              id="name"
              type="text"
              {...register("name")}
              placeholder="My Daily Report"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            {errors.name && (
              <p className="mt-1 text-sm text-destructive">
                {errors.name.message}
              </p>
            )}
          </div>

          {/* Report Type */}
          <div>
            <label
              htmlFor="report_type"
              className="block text-sm font-medium mb-1.5"
            >
              Report Type
            </label>
            <select
              id="report_type"
              {...register("report_type")}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="">Select a report type...</option>
              {REPORT_TYPES.map((rt) => (
                <option key={rt.value} value={rt.value}>
                  {rt.label}
                </option>
              ))}
            </select>
            {errors.report_type && (
              <p className="mt-1 text-sm text-destructive">
                {errors.report_type.message}
              </p>
            )}
          </div>

          {/* Schedule */}
          <div>
            <label
              htmlFor="schedule"
              className="block text-sm font-medium mb-1.5"
            >
              Schedule
            </label>
            <select
              id="schedule"
              {...register("schedule")}
              className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>

          {/* Day of Week (conditional) */}
          {schedule === "weekly" && (
            <div>
              <label
                htmlFor="run_day_of_week"
                className="block text-sm font-medium mb-1.5"
              >
                Day of Week
              </label>
              <select
                id="run_day_of_week"
                {...register("run_day_of_week")}
                className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Select a day...</option>
                {DAYS_OF_WEEK.map((day) => (
                  <option key={day.value} value={day.value}>
                    {day.label}
                  </option>
                ))}
              </select>
              {errors.run_day_of_week && (
                <p className="mt-1 text-sm text-destructive">
                  {errors.run_day_of_week.message}
                </p>
              )}
            </div>
          )}

          {/* Run Time */}
          <div>
            <label
              htmlFor="run_time"
              className="block text-sm font-medium mb-1.5"
            >
              Run Time
            </label>
            <input
              id="run_time"
              type="time"
              {...register("run_time")}
              className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            {errors.run_time && (
              <p className="mt-1 text-sm text-destructive">
                {errors.run_time.message}
              </p>
            )}
          </div>

          {/* Output Format */}
          <div>
            <label
              htmlFor="output_format"
              className="block text-sm font-medium mb-1.5"
            >
              Output Format
            </label>
            <select
              id="output_format"
              {...register("output_format")}
              className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="pdf">PDF</option>
              <option value="excel">Excel</option>
              <option value="image">Image</option>
            </select>
          </div>

          {/* Delivery Target */}
          <div>
            <label htmlFor="delivery_target" className="block text-sm font-medium mb-1.5">
              Delivery Target
            </label>
            <select
              id="delivery_target"
              {...register("delivery_target")}
              className="w-full max-w-xs rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="shared_folder">Shared Folder</option>
              <option value="print_queue">Print Queue</option>
            </select>
          </div>

          {/* Delivery Path */}
          <div>
            <label htmlFor="delivery_path" className="block text-sm font-medium mb-1.5">
              Delivery Path (optional)
            </label>
            <input
              id="delivery_path"
              type="text"
              {...register("delivery_path")}
              placeholder="/mnt/shared/reports or \\\\server\\print"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              Leave empty for the default location. For shared folders, enter a network path. For print queues, enter the spooler watch directory.
            </p>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground shadow hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mutation.isPending && (
              <Loader2 className="h-4 w-4 animate-spin" />
            )}
            Create Subscription
          </button>
        </div>
      </form>
    </div>
  );
}
