/**
 * InfoHint — a small ⓘ affordance with a tooltip, for learnability hints.
 *
 * Why not `title=""`: native tooltips take ~1s to appear, cannot be styled,
 * and are unreachable by keyboard and touch. InfoHint shows on hover *and*
 * keyboard focus (it is a real button, so screen readers announce it) with a
 * ~300ms delay, and renders `aria-describedby` so assistive tech links the
 * hint to the icon.
 *
 * Division of labor with `title` (keep both, do not migrate):
 * - InfoHint = static explanations ("what is a digest?", "what does MAJOR mean?")
 * - title    = dynamic/truncated values (full URL, raw error string, an id)
 *
 * The bubble is portaled to <body> and position:fixed: every .table-wrap and
 * .modal is an overflow scroll container, and an absolutely-positioned bubble
 * near their top edge would be clipped to a sliver (overflow-y computes to
 * auto, and content above a scroll container's top edge cannot be scrolled
 * to). Fixed positioning escapes those clips; the bubble flips below the
 * trigger when there is no room above and is clamped to the viewport. It
 * closes on scroll/resize rather than trying to track the anchor.
 */

import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Info } from "lucide-react";

const VIEWPORT_MARGIN = 8;
const BUBBLE_GAP = 6;

interface BubblePosition {
  top: number;
  left: number;
  /** Right-aligned bubbles use translateX(-100%); flipped ones don't. */
  transform?: "translateX(-100%)";
}

export function InfoHint({
  children,
  label = "More info",
  placement = "top",
}: {
  children: ReactNode;
  label?: string;
  /** "top" suits table cells and forms; "right" suits narrow rails like the sidebar. */
  placement?: "top" | "right";
}) {
  const [open, setOpen] = useState(false);
  const [pos, setPos] = useState<BubblePosition | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const bubbleRef = useRef<HTMLSpanElement | null>(null);
  const hideTimer = useRef<number | null>(null);
  const tooltipId = useId();

  // Show after a short delay (avoids tooltip flicker when sweeping the cursor
  // across a row of hints); hide immediately on leave/blur.
  const scheduleShow = () => {
    if (hideTimer.current !== null) {
      window.clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
    hideTimer.current = window.setTimeout(() => setOpen(true), 300);
  };

  const hide = () => {
    if (hideTimer.current !== null) {
      window.clearTimeout(hideTimer.current);
      hideTimer.current = null;
    }
    setOpen(false);
  };

  // Anchor the open bubble to the trigger's viewport position. Runs in a
  // layout effect so the bubble is measured and placed before first paint.
  useLayoutEffect(() => {
    if (!open) return;
    const trigger = triggerRef.current;
    const bubble = bubbleRef.current;
    if (!trigger || !bubble) return;
    const rect = trigger.getBoundingClientRect();
    const bw = bubble.offsetWidth;
    const bh = bubble.offsetHeight;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const clampTop = (top: number) => Math.min(Math.max(top, VIEWPORT_MARGIN), vh - VIEWPORT_MARGIN);

    let next: BubblePosition;
    if (placement === "right") {
      let left = rect.right + BUBBLE_GAP;
      if (left + bw > vw - VIEWPORT_MARGIN) left = rect.left - BUBBLE_GAP - bw; // flip left
      next = { top: clampTop(rect.top), left: Math.max(left, VIEWPORT_MARGIN) };
    } else {
      // Prefer above (matches the old CSS), flip below when the top edge would
      // clip — table headers sit flush against the top of .table-wrap.
      let top = rect.top - bh - BUBBLE_GAP;
      if (top < VIEWPORT_MARGIN) top = rect.bottom + BUBBLE_GAP;
      // Right edge of the bubble sits 8px past the trigger's right edge; fall
      // back to viewport-left alignment when that would push it off-screen.
      const rightEdge = rect.right + 8;
      if (rightEdge - bw < VIEWPORT_MARGIN || rightEdge > vw - VIEWPORT_MARGIN) {
        next = { top: clampTop(top), left: VIEWPORT_MARGIN };
      } else {
        next = { top: clampTop(top), left: rightEdge, transform: "translateX(-100%)" };
      }
    }
    setPos(next);
  }, [open, placement]);

  // The bubble is viewport-fixed, so it cannot follow a scrolling anchor:
  // close it instead of letting it drift off the trigger.
  useEffect(() => {
    if (!open) return undefined;
    window.addEventListener("scroll", hide, true);
    window.addEventListener("resize", hide);
    return () => {
      window.removeEventListener("scroll", hide, true);
      window.removeEventListener("resize", hide);
    };
  }, [open]);

  useEffect(
    () => () => {
      if (hideTimer.current !== null) window.clearTimeout(hideTimer.current);
    },
    [],
  );

  return (
    <span
      className="info-hint"
      onMouseEnter={scheduleShow}
      onMouseLeave={hide}
      onFocus={scheduleShow}
      onBlur={hide}
    >
      <button
        type="button"
        ref={triggerRef}
        className="info-hint-trigger"
        aria-label={label}
        aria-expanded={open}
        aria-describedby={open ? tooltipId : undefined}
        onClick={(event) => {
          event.preventDefault();
          setOpen((value) => !value);
        }}
      >
        <Info size={13} aria-hidden />
      </button>
      {open
        ? createPortal(
            <span
              ref={bubbleRef}
              role="tooltip"
              id={tooltipId}
              className="info-hint-bubble"
              style={{
                top: pos?.top ?? -9999,
                left: pos?.left ?? -9999,
                transform: pos?.transform,
              }}
            >
              {children}
            </span>,
            document.body,
          )
        : null}
    </span>
  );
}
