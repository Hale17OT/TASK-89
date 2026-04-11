import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Shield, Loader2, AlertCircle } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import axios from "axios";
import apiClient from "@/api/client";

const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
  rememberDevice: z.boolean().default(false),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login, user, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [serverError, setServerError] = useState<string | null>(null);
  const [prefillUsername, setPrefillUsername] = useState<string>("");
  const [prefillLoaded, setPrefillLoaded] = useState(false);

  const from =
    (location.state as { from?: { pathname: string } })?.from?.pathname ??
    "/dashboard";

  // Redirect if already logged in
  useEffect(() => {
    if (user && !authLoading) {
      navigate(from, { replace: true });
    }
  }, [user, authLoading, navigate, from]);

  // Fetch CSRF cookie and pre-filled username on mount
  useEffect(() => {
    // Ensure CSRF cookie is set before any POST
    apiClient.get("auth/csrf/").catch(() => {});
    // Fetch pre-filled username from backend HttpOnly cookie
    apiClient
      .get<{ username: string | null }>("auth/remember-device/prefill/")
      .then((res) => {
        setPrefillUsername(res.data.username ?? "");
      })
      .catch(() => {})
      .finally(() => setPrefillLoaded(true));
  }, []);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: "",
      password: "",
      rememberDevice: false,
    },
  });

  // Update form defaults once prefill loads
  useEffect(() => {
    if (prefillLoaded && prefillUsername) {
      reset({
        username: prefillUsername,
        password: "",
        rememberDevice: true,
      });
    }
  }, [prefillLoaded, prefillUsername, reset]);

  const onSubmit = async (data: LoginFormValues) => {
    setServerError(null);
    try {
      await login({ username: data.username, password: data.password });
      // After successful login, call remember-device endpoint if checked
      if (data.rememberDevice) {
        try {
          await apiClient.post("auth/remember-device/");
        } catch {
          // Non-critical: don't block login on remember-device failure
        }
      }
      navigate(from, { replace: true });
    } catch (error) {
      if (axios.isAxiosError(error) && error.response?.data) {
        const data = error.response.data;
        setServerError(data.message || data.detail || "Invalid credentials.");
      } else {
        setServerError("An unexpected error occurred. Please try again.");
      }
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted p-4">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary">
            <Shield className="h-6 w-6 text-primary-foreground" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">MedRights</h1>
          <p className="text-sm text-muted-foreground">
            Patient Media &amp; Consent Portal
          </p>
        </div>

        {/* Form Card */}
        <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Server Error */}
            {serverError && (
              <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{serverError}</span>
              </div>
            )}

            {/* Username */}
            <div className="space-y-2">
              <label
                htmlFor="username"
                className="text-sm font-medium leading-none"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                autoComplete="username"
                autoFocus={!prefillUsername}
                className={cn(
                  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background",
                  "placeholder:text-muted-foreground",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  errors.username && "border-destructive"
                )}
                placeholder="Enter your username"
                {...register("username")}
              />
              {errors.username && (
                <p className="text-xs text-destructive">
                  {errors.username.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-2">
              <label
                htmlFor="password"
                className="text-sm font-medium leading-none"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                autoFocus={!!prefillUsername}
                className={cn(
                  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background",
                  "placeholder:text-muted-foreground",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                  "disabled:cursor-not-allowed disabled:opacity-50",
                  errors.password && "border-destructive"
                )}
                placeholder="Enter your password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-xs text-destructive">
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Remember Device */}
            <div className="flex items-center gap-2">
              <input
                id="rememberDevice"
                type="checkbox"
                className="h-4 w-4 rounded border-input text-primary focus:ring-ring"
                {...register("rememberDevice")}
              />
              <label
                htmlFor="rememberDevice"
                className="text-sm text-muted-foreground"
              >
                Remember my username on this device
              </label>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={cn(
                "inline-flex h-10 w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow",
                "hover:bg-primary/90",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                "disabled:pointer-events-none disabled:opacity-50"
              )}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-xs text-muted-foreground">
          Protected health information. Authorized users only.
        </p>
      </div>
    </div>
  );
}
