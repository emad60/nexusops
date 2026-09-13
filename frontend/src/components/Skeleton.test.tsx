import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Skeleton, SkeletonCard, TableSkeleton } from "./Skeleton";
import { EmptyState } from "./ui";

describe("TableSkeleton", () => {
  it("announces one status region, not fake table semantics", () => {
    render(<TableSkeleton label="Loading servers" rows={3} cols={4} />);

    // role="status" with the label is the only semantic surface.
    const status = screen.getByRole("status", { name: "Loading servers" });
    expect(status).toBeInTheDocument();

    // Deliberately not a <table>: fake table roles would satisfy
    // findByRole("table") before real data arrives.
    expect(screen.queryByRole("table")).not.toBeInTheDocument();

    const bars = status.querySelectorAll(".skeleton");
    // 4 header bars + 3 rows x 4 bars.
    expect(bars.length).toBe(16);
  });
});

describe("Skeleton", () => {
  it("renders aria-hidden bars with custom dimensions", () => {
    const { container } = render(<Skeleton w={120} h={14} />);

    const bar = container.querySelector(".skeleton");
    expect(bar).toHaveAttribute("aria-hidden", "true");
    expect(bar).toHaveStyle({ width: "120px", height: "14px" });
  });

  it("renders the card variant as a plain decorative block", () => {
    render(<SkeletonCard lines={2} />);

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(document.querySelectorAll(".skeleton").length).toBe(3);
  });
});

describe("EmptyState", () => {
  it("renders title, hint and an optional action", () => {
    render(
      <EmptyState
        icon="◎"
        title="No servers found"
        hint="Register your first server."
        action={<button type="button">Register server</button>}
      />,
    );

    expect(screen.getByText("No servers found")).toHaveClass("empty-title");
    expect(screen.getByText("Register your first server.")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Register server" }),
    ).toBeInTheDocument();
  });

  it("omits the hint and action when not provided", () => {
    render(<EmptyState title="Nothing here" />);

    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(document.querySelector(".empty-state .small")).not.toBeInTheDocument();
    expect(document.querySelector(".empty-state button")).not.toBeInTheDocument();
  });
});
