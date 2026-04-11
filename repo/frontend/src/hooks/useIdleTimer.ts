import { useEffect, useRef, useCallback } from "react";
import { IDLE_WARNING_MS, IDLE_TIMEOUT_MS, SESSION_REFRESH_INTERVAL_MS } from "@/lib/constants";
import { refreshSession } from "@/api/endpoints/auth";

interface UseIdleTimerOptions {
  onWarning: () => void;
  onExpire: () => void;
  enabled: boolean;
}

/**
 * Monitors user activity and manages session lifecycle:
 * - Resets idle timer on mouse/keyboard/touch events
 * - Fires onWarning at IDLE_WARNING_MS (13 min)
 * - Fires onExpire at IDLE_TIMEOUT_MS (15 min)
 * - Periodically calls session refresh endpoint
 */
export function useIdleTimer({ onWarning, onExpire, enabled }: UseIdleTimerOptions) {
  const lastActivity = useRef(Date.now());
  const warningFired = useRef(false);
  const refreshTimer = useRef<ReturnType<typeof setInterval>>();
  const checkTimer = useRef<ReturnType<typeof setInterval>>();

  const resetActivity = useCallback(() => {
    lastActivity.current = Date.now();
    warningFired.current = false;
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const activityEvents = ["mousemove", "keydown", "touchstart", "scroll", "click"];
    const handler = () => resetActivity();

    activityEvents.forEach((evt) => document.addEventListener(evt, handler, { passive: true }));

    // Check idle state every 30 seconds
    checkTimer.current = setInterval(() => {
      const elapsed = Date.now() - lastActivity.current;

      if (elapsed >= IDLE_TIMEOUT_MS) {
        onExpire();
      } else if (elapsed >= IDLE_WARNING_MS && !warningFired.current) {
        warningFired.current = true;
        onWarning();
      }
    }, 30_000);

    // Periodically refresh session to keep server-side alive
    refreshTimer.current = setInterval(() => {
      const elapsed = Date.now() - lastActivity.current;
      if (elapsed < IDLE_WARNING_MS) {
        refreshSession().catch(() => {
          // Session refresh failed - server may have expired it
        });
      }
    }, SESSION_REFRESH_INTERVAL_MS);

    return () => {
      activityEvents.forEach((evt) => document.removeEventListener(evt, handler));
      if (checkTimer.current) clearInterval(checkTimer.current);
      if (refreshTimer.current) clearInterval(refreshTimer.current);
    };
  }, [enabled, onWarning, onExpire, resetActivity]);

  return { resetActivity };
}
