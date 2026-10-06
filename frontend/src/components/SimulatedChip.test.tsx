import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SimulatedChip } from "./SimulatedChip";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
}));

vi.mock("../api/client", () => ({
  ApiError: class ApiError extends Error {},
  apiGet: mocks.apiGet,
}));

async function renderChip() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <SimulatedChip />
    </QueryClientProvider>,
  );
  // Let the ["meta"] query settle.
  await screen.findByText("Simulated").catch(() => undefined);
  return utils;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("SimulatedChip", () => {
  it("labels the view while the instance runs simulated", async () => {
    mocks.apiGet.mockResolvedValue({ environment: "development", simulation_mode: true });
    await renderChip();

    expect(await screen.findByText("Simulated")).toBeInTheDocument();
    expect(mocks.apiGet).toHaveBeenCalledWith("/meta", undefined, expect.anything());
  });

  it("stays hidden on a real instance", async () => {
    mocks.apiGet.mockResolvedValue({ environment: "production", simulation_mode: false });
    await renderChip();

    expect(screen.queryByText("Simulated")).not.toBeInTheDocument();
  });

  it("renders nothing until the runtime flag is known", async () => {
    // A pending/undefined /meta must never be read as "simulated": the chip is
    // an honesty label, so a false positive is worse than a late one.
    mocks.apiGet.mockReturnValue(new Promise(() => {}));
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <SimulatedChip />
      </QueryClientProvider>,
    );

    expect(screen.queryByText("Simulated")).not.toBeInTheDocument();
  });
});
