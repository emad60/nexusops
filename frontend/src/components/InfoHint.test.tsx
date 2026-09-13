import { afterEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { InfoHint } from "./InfoHint";

describe("InfoHint", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("renders a labelled trigger button without a visible tooltip", () => {
    render(<InfoHint>First 12 hex chars of the value's SHA-256 fingerprint.</InfoHint>);

    const trigger = screen.getByRole("button", { name: "More info" });
    expect(trigger).toBeInTheDocument();
    // Closed by default — the bubble is not in the document until shown.
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    expect(trigger).toHaveAttribute("aria-expanded", "false");
  });

  it("shows the bubble after the hover delay and hides on leave", () => {
    vi.useFakeTimers();
    render(<InfoHint>What does this mean?</InfoHint>);

    const trigger = screen.getByRole("button", { name: "More info" });
    fireEvent.mouseEnter(trigger.closest(".info-hint")!);

    // Before the delay elapses the tooltip is not there yet.
    act(() => {
      vi.advanceTimersByTime(200);
    });
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(150);
    });
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("What does this mean?");

    fireEvent.mouseLeave(trigger.closest(".info-hint")!);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("opens on keyboard focus and closes on blur", () => {
    vi.useFakeTimers();
    render(<InfoHint>Keyboard reachable.</InfoHint>);

    const trigger = screen.getByRole("button", { name: "More info" });
    fireEvent.focus(trigger.closest(".info-hint")!);

    act(() => {
      vi.advanceTimersByTime(300);
    });
    expect(screen.getByRole("tooltip")).toBeInTheDocument();

    fireEvent.blur(trigger.closest(".info-hint")!);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("links the bubble to the trigger via aria-describedby", () => {
    render(<InfoHint>Described hint.</InfoHint>);

    const trigger = screen.getByRole("button", { name: "More info" });
    fireEvent.click(trigger);

    const tooltip = screen.getByRole("tooltip");
    expect(trigger).toHaveAttribute("aria-describedby", tooltip.id);
    expect(trigger).toHaveAttribute("aria-expanded", "true");
  });

  it("supports a custom aria-label for context-specific triggers", () => {
    render(<InfoHint label="About severity">MAJOR means partial degradation.</InfoHint>);

    expect(
      screen.getByRole("button", { name: "About severity" }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "More info" }),
    ).not.toBeInTheDocument();
  });
});
