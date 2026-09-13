/**
 * Shared form primitives — one shell (Field) plus typed controls on top.
 *
 * Every control wires the same contract:
 * - the label is programmatically associated with the control (htmlFor/id),
 * - `error` renders a role="alert" message under the control and flips
 *   aria-invalid on it (pages validate on submit and mirror the API),
 * - `hint` is persistent guidance, always visible and dimmed,
 * - `required` adds the visual "*" marker and aria-required (announced by
 *   screen readers) — it deliberately does NOT set the native attribute,
 *   because most forms here validate in onSubmit with styled errors and
 *   native bubbles would preempt them (min/max/pattern pass through).
 *
 * Before this module only LoginPage had real per-field validation UI; every
 * other form hand-rolled its own (or none). Retrofit pages import from here
 * instead of re-implementing field markup.
 */

import {
  useId,
  useRef,
  useState,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { Eye, EyeOff, Search, X } from "lucide-react";
import { InfoHint } from "./InfoHint";

/** Aria attributes the shell computes for the control it wraps. */
export interface FieldAria {
  id: string;
  "aria-describedby": string | undefined;
  "aria-invalid": true | undefined;
  "aria-required": true | undefined;
}

interface FieldBaseProps {
  label: ReactNode;
  required?: boolean;
  error?: string | null;
  hint?: ReactNode;
  /** On-demand tooltip rendered next to the label (see InfoHint). */
  info?: ReactNode;
  /** Stable id override — needed when code addresses the control by id. */
  id?: string;
}

/** Render-prop shell for custom controls; the typed inputs below cover common cases. */
export function Field({
  label,
  required,
  error,
  hint,
  info,
  id,
  children,
}: FieldBaseProps & { children: (aria: FieldAria) => ReactNode }) {
  const generated = useId();
  const inputId = id ?? generated;
  const errorId = `${inputId}-error`;
  const hintId = `${inputId}-hint`;
  const describedBy =
    [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(" ") || undefined;

  return (
    <div className={`field${error ? " has-error" : ""}`}>
      <div className="label-row">
        <label htmlFor={inputId}>
          {label}
          {required ? (
            <span className="req" aria-hidden="true">
              {" "}
              *
            </span>
          ) : null}
        </label>
        {/* Next to the label, not inside it: the trigger must not end up in the
            input's accessible name (or in getByLabelText matches). */}
        {info ? <InfoHint>{info}</InfoHint> : null}
      </div>
      <div className="field-control">{children({ id: inputId, "aria-describedby": describedBy, "aria-invalid": error ? true : undefined, "aria-required": required || undefined })}</div>
      {error ? (
        <p className="field-error" id={errorId} role="alert">
          {error}
        </p>
      ) : null}
      {hint ? (
        <p className="field-hint" id={hintId}>
          {hint}
        </p>
      ) : null}
    </div>
  );
}

type TextFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "className"> &
  FieldBaseProps & {
    /** Render the control with the monospace font (keys, tokens, code-ish values). */
    mono?: boolean;
  };

export function TextField({ label, required, error, hint, info, id, mono, ...inputProps }: TextFieldProps) {
  return (
    <Field label={label} required={required} error={error} hint={hint} info={info} id={id}>
      {(aria) => <input {...aria} {...inputProps} className={mono ? "input mono" : "input"} />}
    </Field>
  );
}

type PasswordFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "id" | "className" | "type"> &
  FieldBaseProps & { mono?: boolean };

/**
 * Password-style input with a show/hide reveal toggle. Defaults to type
 * "password"; the toggle is a labelled, aria-pressed button so it stays
 * keyboard- and screen-reader-accessible.
 */
export function PasswordField({ label, required, error, hint, info, id, mono, ...inputProps }: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);
  return (
    <Field label={label} required={required} error={error} hint={hint} info={info} id={id}>
      {(aria) => (
        <>
          <input
            {...aria}
            {...inputProps}
            type={visible ? "text" : "password"}
            className={`input has-trailing${mono ? " mono" : ""}`}
          />
          <button
            type="button"
            className="btn ghost sm field-trailing"
            aria-label={visible ? "Hide password" : "Show password"}
            aria-pressed={visible}
            title={visible ? "Hide value" : "Show value"}
            onClick={() => setVisible((current) => !current)}
          >
            {visible ? <EyeOff size={14} aria-hidden /> : <Eye size={14} aria-hidden />}
          </button>
        </>
      )}
    </Field>
  );
}

type TextAreaFieldProps = Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id" | "className"> &
  FieldBaseProps & {
    /** Show a character counter when maxLength is set (default: on). */
    showCount?: boolean;
  };

export function TextAreaField({
  label,
  required,
  error,
  hint,
  info,
  id,
  showCount = true,
  ...areaProps
}: TextAreaFieldProps) {
  const value = typeof areaProps.value === "string" ? areaProps.value : "";
  return (
    <Field label={label} required={required} error={error} hint={hint} info={info} id={id}>
      {(aria) => (
        <>
          <textarea {...aria} {...areaProps} className="input" />
          {showCount && areaProps.maxLength ? (
            <span className="char-counter">
              {value.length}/{areaProps.maxLength}
            </span>
          ) : null}
        </>
      )}
    </Field>
  );
}

type SelectFieldProps = Omit<SelectHTMLAttributes<HTMLSelectElement>, "id" | "className"> &
  FieldBaseProps;

export function SelectField({
  label,
  required,
  error,
  hint,
  info,
  id,
  children,
  ...selectProps
}: SelectFieldProps) {
  return (
    <Field label={label} required={required} error={error} hint={hint} info={info} id={id}>
      {(aria) => (
        <select {...aria} {...selectProps} className="input">
          {children}
        </select>
      )}
    </Field>
  );
}

type CheckboxFieldProps = Omit<InputHTMLAttributes<HTMLInputElement>, "className" | "type"> & {
  label: ReactNode;
  info?: ReactNode;
};

/**
 * Single checkbox with an explicitly associated label. The optional InfoHint
 * sits outside the <label> so its focusable trigger never toggles the checkbox
 * as a side effect of being clicked.
 */
export function CheckboxField({ label, info, id, ...checkboxProps }: CheckboxFieldProps) {
  const generated = useId();
  const inputId = id ?? generated;
  return (
    <div className="check-field">
      <input type="checkbox" id={inputId} {...checkboxProps} />
      <label htmlFor={inputId}>
        <span>{label}</span>
      </label>
      {info ? <InfoHint>{info}</InfoHint> : null}
    </div>
  );
}

type SearchInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "className" | "type"> & {
  value: string;
  onClear: () => void;
};

/** Toolbar search box: lead icon plus a clear button while it has content. */
export function SearchInput({ value, onClear, ...inputProps }: SearchInputProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  return (
    <div className="search-field">
      <Search size={14} aria-hidden className="search-lead" />
      <input ref={inputRef} type="search" className="input search-input" value={value} {...inputProps} />
      {value ? (
        <button
          type="button"
          className="btn ghost sm search-clear"
          aria-label="Clear search"
          onClick={() => {
            onClear();
            // Clearing unmounts this button; move focus to the input first so
            // keyboard users don't fall back to <body>.
            inputRef.current?.focus();
          }}
        >
          <X size={12} aria-hidden />
        </button>
      ) : null}
    </div>
  );
}
