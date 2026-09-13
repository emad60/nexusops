import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { CheckboxField, PasswordField, SearchInput, SelectField, TextAreaField, TextField } from "./form";

function LabelProbe() {
  const [value, setValue] = useState("");
  return (
    <TextField
      label="Server name"
      required
      hint="Shown in the sidebar"
      error="Name is required."
      value={value}
      onChange={(event) => setValue(event.target.value)}
    />
  );
}

describe("TextField", () => {
  it("associates the label, hint and error with the input", () => {
    render(<LabelProbe />);

    const input = screen.getByLabelText(/Server name/);
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input).toHaveAttribute(
      "aria-describedby",
      expect.stringMatching(/-error -hint$|-error .*-hint/),
    );

    const error = screen.getByRole("alert");
    expect(error).toHaveTextContent("Name is required.");
    expect(error).toHaveAttribute("id", expect.stringMatching(/-error$/));
    expect(screen.getByText("Shown in the sidebar")).toHaveAttribute(
      "id",
      expect.stringMatching(/-hint$/),
    );
  });

  it("renders the required marker visually without native validation", () => {
    render(<TextField label="Name" required value="" onChange={() => {}} />);
    const input = screen.getByLabelText(/Name/);
    // No native attribute (native bubbles would preempt the styled onSubmit
    // errors) — but screen readers still announce the field as required.
    expect(input).not.toHaveAttribute("required");
    expect(input).toHaveAttribute("aria-required", "true");
    expect(screen.getByText("*")).toBeInTheDocument();
  });

  it("drops aria-describedby entirely when there is no hint or error", () => {
    render(<TextField label="Name" value="" onChange={() => {}} />);
    const input = screen.getByLabelText("Name");
    expect(input).not.toHaveAttribute("aria-describedby");
    expect(input).not.toHaveAttribute("aria-required");
  });

  it("types into the controlled input", () => {
    render(<LabelProbe />);
    fireEvent.change(screen.getByLabelText(/Server name/), { target: { value: "edge-01" } });
    expect(screen.getByDisplayValue("edge-01")).toBeInTheDocument();
  });

  it("applies the mono class on demand", () => {
    render(<TextField label="Token" mono value="" onChange={() => {}} />);
    expect(screen.getByLabelText("Token")).toHaveClass("mono");
  });
});

describe("PasswordField", () => {
  it("renders type=password with a working reveal toggle", () => {
    render(<PasswordField label="Password" value="hunter2" onChange={() => {}} />);

    const input = screen.getByLabelText("Password");
    expect(input).toHaveAttribute("type", "password");

    const toggle = screen.getByRole("button", { name: "Show password" });
    expect(toggle).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(toggle);

    expect(input).toHaveAttribute("type", "text");
    expect(screen.getByRole("button", { name: "Hide password" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("preserves focus in the input when toggling visibility", () => {
    render(<PasswordField label="Password" value="hunter2" onChange={() => {}} />);

    const input = screen.getByLabelText("Password");
    fireEvent.focus(input);
    fireEvent.click(screen.getByRole("button", { name: "Show password" }));

    // Toggling must not steal focus (the user is mid-typing).
    expect(input).toBeEnabled();
    expect(screen.getByDisplayValue("hunter2")).toBeInTheDocument();
  });

  it("wires hint and error like TextField", () => {
    render(
      <PasswordField
        label="Secret"
        error="Required."
        hint="Never shown again"
        value=""
        onChange={() => {}}
      />,
    );
    expect(screen.getByLabelText(/Secret/)).toHaveAttribute("aria-invalid", "true");
    expect(screen.getByRole("alert")).toHaveTextContent("Required.");
    expect(screen.getByText("Never shown again")).toBeInTheDocument();
  });
});

describe("TextAreaField", () => {
  it("shows a character counter when maxLength is set", () => {
    function Probe() {
      const [value, setValue] = useState("hello");
      return (
        <TextAreaField
          label="Resolution"
          maxLength={100}
          value={value}
          onChange={(event) => setValue(event.target.value)}
        />
      );
    }
    render(<Probe />);

    expect(screen.getByText("5/100")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Resolution"), { target: { value: "hello world" } });
    expect(screen.getByText("11/100")).toBeInTheDocument();
  });

  it("hides the counter when showCount is false", () => {
    render(
      <TextAreaField label="Notes" maxLength={50} showCount={false} value="abc" onChange={() => {}} />,
    );
    expect(screen.queryByText(/\/50/)).not.toBeInTheDocument();
  });

  it("wires the error alert", () => {
    render(<TextAreaField label="Notes" error="Too long." value="" onChange={() => {}} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Too long.");
  });
});

describe("SelectField", () => {
  it("renders options and reports the selection", () => {
    function Probe() {
      const [value, setValue] = useState("");
      return (
        <SelectField label="Role" value={value} onChange={(e) => setValue(e.target.value)}>
          <option value="">—</option>
          <option value="r1">Owner</option>
        </SelectField>
      );
    }
    render(<Probe />);

    fireEvent.change(screen.getByLabelText("Role"), { target: { value: "r1" } });
    expect(screen.getByLabelText("Role")).toHaveValue("r1");
  });

  it("associates error state", () => {
    render(
      <SelectField label="Role" error="Pick a role." value="" onChange={() => {}}>
        <option value="">—</option>
      </SelectField>,
    );
    expect(screen.getByLabelText(/Role/)).toHaveAttribute("aria-invalid", "true");
  });
});

describe("CheckboxField", () => {
  it("toggles via its wrapped label", () => {
    function Probe() {
      const [checked, setChecked] = useState(false);
      return (
        <CheckboxField
          label="Simulated server (demo data)"
          checked={checked}
          onChange={(event) => setChecked(event.target.checked)}
        />
      );
    }
    render(<Probe />);

    const box = screen.getByLabelText("Simulated server (demo data)");
    expect(box).not.toBeChecked();
    fireEvent.click(screen.getByText("Simulated server (demo data)"));
    expect(box).toBeChecked();
  });
});

describe("SearchInput", () => {
  function SearchProbe({ initial = "" }: { initial?: string }) {
    const [value, setValue] = useState(initial);
    return (
      <SearchInput
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onClear={() => setValue("")}
        placeholder="Search servers…"
      />
    );
  }

  it("shows the clear button only while there is content and clears on click", () => {
    render(<SearchProbe initial="edge" />);

    expect(screen.getByDisplayValue("edge")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Clear search" }));
    expect(screen.getByDisplayValue("")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Clear search" })).not.toBeInTheDocument();
  });

  it("refocuses the input after clearing with the button", () => {
    render(<SearchProbe initial="edge" />);

    fireEvent.click(screen.getByRole("button", { name: "Clear search" }));
    // Clearing unmounts the button — without the refocus, keyboard users
    // would fall back to <body> right as they want to type a new query.
    expect(screen.getByDisplayValue("")).toHaveFocus();
  });

  it("keeps typing working alongside the clear affordance", () => {
    const onChange = vi.fn();
    render(<SearchInput value="" onClear={() => {}} placeholder="Search containers…" onChange={onChange} />);
    fireEvent.change(screen.getByPlaceholderText(/Search containers/), { target: { value: "db" } });
    expect(onChange).toHaveBeenCalled();
  });
});
