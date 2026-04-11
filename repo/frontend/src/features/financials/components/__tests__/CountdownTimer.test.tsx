import { describe, it, expect } from "vitest";
import { renderWithProviders, screen } from "@/test/test-utils";
import { CountdownTimer } from "../CountdownTimer";

describe("CountdownTimer", () => {
  it("renders minutes and seconds", () => {
    renderWithProviders(
      <CountdownTimer totalSeconds={1800} remainingSeconds={754} />
    );

    // 754 seconds = 12 minutes, 34 seconds => "12:34"
    expect(screen.getByText("12:34")).toBeInTheDocument();
  });

  it("shows green color when more than 10 minutes remaining", () => {
    renderWithProviders(
      <CountdownTimer totalSeconds={1800} remainingSeconds={900} />
    );

    // 900 seconds = 15 min > 10 min => green
    const timeText = screen.getByText("15:00");
    expect(timeText.className).toContain("text-green-600");
  });

  it("shows red color when less than 5 minutes remaining", () => {
    renderWithProviders(
      <CountdownTimer totalSeconds={1800} remainingSeconds={120} />
    );

    // 120 seconds = 2 min < 5 min => red
    const timeText = screen.getByText("02:00");
    expect(timeText.className).toContain("text-red-600");
  });
});
