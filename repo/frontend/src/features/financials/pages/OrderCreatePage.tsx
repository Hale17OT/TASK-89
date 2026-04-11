import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useForm, useFieldArray } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation } from "@tanstack/react-query";
import { Loader2, Plus, Trash2, ArrowLeft } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import { createOrder } from "@/api/endpoints/financials";
import { searchPatients as searchPatientsApi } from "@/api/endpoints/patients";
import type { PatientMasked } from "@/api/types/patient.types";

const lineItemSchema = z.object({
  description: z.string().min(1, "Description is required"),
  quantity: z.coerce.number().min(1, "Quantity must be at least 1"),
  unit_price: z.coerce.number().min(0.01, "Price must be greater than 0"),
});

const orderSchema = z.object({
  patient_id: z.string().min(1, "Patient is required"),
  line_items: z.array(lineItemSchema).min(1, "At least one line item is required"),
  notes: z.string().optional(),
});

type OrderFormValues = z.infer<typeof orderSchema>;

export function OrderCreatePage() {
  const navigate = useNavigate();
  const [patientSearch, setPatientSearch] = useState("");
  const [patientResults, setPatientResults] = useState<PatientMasked[]>([]);
  const [selectedPatient, setSelectedPatient] = useState<PatientMasked | null>(
    null
  );
  const [isSearching, setIsSearching] = useState(false);

  const {
    register,
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<OrderFormValues>({
    resolver: zodResolver(orderSchema),
    defaultValues: {
      patient_id: "",
      line_items: [{ description: "", quantity: 1, unit_price: 0 }],
      notes: "",
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "line_items",
  });

  const watchedItems = watch("line_items");
  const runningTotal = watchedItems.reduce((sum, item) => {
    const qty = Number(item.quantity) || 0;
    const price = Number(item.unit_price) || 0;
    return sum + qty * price;
  }, 0);

  const mutation = useMutation({
    mutationFn: (data: OrderFormValues) =>
      createOrder({
        patient_id: data.patient_id,
        line_items: data.line_items.map((li) => ({
          description: li.description,
          quantity: Number(li.quantity),
          unit_price: Number(li.unit_price),
        })),
        notes: data.notes,
      }),
    onSuccess: (result) => {
      toast.success("Order created successfully");
      navigate(`/financials/${result.id}`);
    },
    onError: (err: Error) => {
      toast.error(`Failed to create order: ${err.message}`);
    },
  });

  async function searchPatients(query: string) {
    if (query.length < 2) {
      setPatientResults([]);
      return;
    }
    setIsSearching(true);
    try {
      const results = await searchPatientsApi(query);
      setPatientResults(results);
    } catch {
      setPatientResults([]);
    } finally {
      setIsSearching(false);
    }
  }

  function selectPatient(patient: PatientMasked) {
    setSelectedPatient(patient);
    setValue("patient_id", patient.id);
    setPatientSearch("");
    setPatientResults([]);
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link
          to="/financials"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Create Order</h1>
      </div>

      <form
        onSubmit={handleSubmit((data) => mutation.mutate(data))}
        className="space-y-6"
      >
        {/* Patient Selector */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold">Patient</h2>

          {selectedPatient ? (
            <div className="flex items-center justify-between rounded-md border border-border bg-muted/50 px-4 py-3">
              <div>
                <p className="text-sm font-medium">
                  {selectedPatient.name}
                </p>
                <p className="text-xs text-muted-foreground">
                  MRN: {selectedPatient.mrn}
                </p>
              </div>
              <button
                type="button"
                onClick={() => {
                  setSelectedPatient(null);
                  setValue("patient_id", "");
                }}
                className="text-sm text-muted-foreground hover:text-destructive"
              >
                Change
              </button>
            </div>
          ) : (
            <div className="relative">
              <input
                type="text"
                placeholder="Search patients by name or MRN..."
                value={patientSearch}
                onChange={(e) => {
                  setPatientSearch(e.target.value);
                  searchPatients(e.target.value);
                }}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              {isSearching && (
                <Loader2 className="absolute right-3 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
              )}
              {patientResults.length > 0 && (
                <ul className="absolute z-10 mt-1 w-full rounded-md border border-border bg-popover shadow-md max-h-48 overflow-auto">
                  {patientResults.map((p) => (
                    <li key={p.id}>
                      <button
                        type="button"
                        onClick={() => selectPatient(p)}
                        className="w-full px-4 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
                      >
                        <span className="font-medium">{p.name}</span>
                        <span className="ml-2 text-muted-foreground">
                          MRN: {p.mrn}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {errors.patient_id && (
            <p className="text-sm text-destructive">
              {errors.patient_id.message}
            </p>
          )}
        </div>

        {/* Line Items */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Line Items</h2>
            <button
              type="button"
              onClick={() =>
                append({ description: "", quantity: 1, unit_price: 0 })
              }
              className="inline-flex items-center gap-1 rounded-md bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground hover:bg-secondary/80"
            >
              <Plus className="h-3 w-3" />
              Add Item
            </button>
          </div>

          {errors.line_items?.root && (
            <p className="text-sm text-destructive">
              {errors.line_items.root.message}
            </p>
          )}

          <div className="space-y-3">
            {fields.map((field, index) => (
              <div
                key={field.id}
                className="grid grid-cols-[1fr_100px_120px_40px] gap-3 items-start"
              >
                <div>
                  <input
                    {...register(`line_items.${index}.description`)}
                    placeholder="Description"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  {errors.line_items?.[index]?.description && (
                    <p className="mt-1 text-xs text-destructive">
                      {errors.line_items[index]?.description?.message}
                    </p>
                  )}
                </div>
                <div>
                  <input
                    type="number"
                    min={1}
                    {...register(`line_items.${index}.quantity`)}
                    placeholder="Qty"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  {errors.line_items?.[index]?.quantity && (
                    <p className="mt-1 text-xs text-destructive">
                      {errors.line_items[index]?.quantity?.message}
                    </p>
                  )}
                </div>
                <div>
                  <input
                    type="number"
                    step="0.01"
                    min={0}
                    {...register(`line_items.${index}.unit_price`)}
                    placeholder="Unit Price"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  {errors.line_items?.[index]?.unit_price && (
                    <p className="mt-1 text-xs text-destructive">
                      {errors.line_items[index]?.unit_price?.message}
                    </p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => fields.length > 1 && remove(index)}
                  disabled={fields.length <= 1}
                  className="mt-1 inline-flex items-center justify-center rounded-md p-2 text-muted-foreground hover:text-destructive disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>

          {/* Running Total */}
          <div className="flex justify-end border-t border-border pt-4">
            <div className="text-right">
              <p className="text-sm text-muted-foreground">Total</p>
              <p className="text-2xl font-bold font-mono">
                ${runningTotal.toFixed(2)}
              </p>
            </div>
          </div>
        </div>

        {/* Notes */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm space-y-4">
          <h2 className="text-lg font-semibold">Notes</h2>
          <textarea
            {...register("notes")}
            rows={3}
            placeholder="Optional notes..."
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
          />
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
            Create Order
          </button>
        </div>
      </form>
    </div>
  );
}
