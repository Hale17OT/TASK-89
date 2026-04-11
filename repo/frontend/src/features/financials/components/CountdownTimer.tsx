import { useState, useEffect } from "react";
import { cn } from "@/lib/utils";

interface CountdownTimerProps {
  totalSeconds: number;
  remainingSeconds: number;
}

export function CountdownTimer({
  totalSeconds,
  remainingSeconds: initialRemaining,
}: CountdownTimerProps) {
  const [remaining, setRemaining] = useState(initialRemaining);

  useEffect(() => {
    setRemaining(initialRemaining);
  }, [initialRemaining]);

  useEffect(() => {
    if (remaining <= 0) return;
    const timer = setInterval(() => {
      setRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [remaining]);

  const minutes = Math.floor(remaining / 60);
  const seconds = remaining % 60;
  const percentage = totalSeconds > 0 ? (remaining / totalSeconds) * 100 : 0;

  const isGreen = remaining > 600; // > 10 min
  const isAmber = remaining > 300 && remaining <= 600; // 5-10 min
  const isRed = remaining <= 300; // < 5 min

  const barColor = isGreen
    ? "bg-green-500"
    : isAmber
      ? "bg-amber-500"
      : "bg-red-500";

  const textColor = isGreen
    ? "text-green-600"
    : isAmber
      ? "text-amber-600"
      : "text-red-600";

  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2.5 rounded-full bg-muted overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full transition-all duration-1000",
            barColor,
            isRed && "animate-pulse"
          )}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span
        className={cn("text-sm font-mono font-semibold tabular-nums", textColor)}
      >
        {String(minutes).padStart(2, "0")}:{String(seconds).padStart(2, "0")}
      </span>
    </div>
  );
}
