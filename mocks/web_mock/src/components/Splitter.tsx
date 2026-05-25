import { useCallback, useEffect, useRef, useState } from "react";

type Props = {
  direction: "vertical" | "horizontal";
  /** Reads current size (px) to feed delta deltas during drag. */
  getSize: () => number;
  /** Called with the new size (px) on drag. */
  onSize: (px: number) => void;
  /** Optional min/max clamp. */
  min?: number;
  max?: number;
  /** test-id for Playwright */
  testId?: string;
};

/**
 * Thin draggable handle that resizes a sibling element. Pure JS — no
 * external dependency. ``direction`` determines whether the handle is a
 * vertical bar (drags horizontally to change a width) or a horizontal bar
 * (drags vertically to change a height).
 */
export function Splitter({
  direction,
  getSize,
  onSize,
  min = 100,
  max = 9999,
  testId,
}: Props) {
  const [dragging, setDragging] = useState(false);
  const startRef = useRef({ pos: 0, size: 0 });

  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId);
      startRef.current = {
        pos: direction === "vertical" ? e.clientX : e.clientY,
        size: getSize(),
      };
      setDragging(true);
      e.preventDefault();
    },
    [direction, getSize]
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!dragging) return;
      const cur = direction === "vertical" ? e.clientX : e.clientY;
      const delta = cur - startRef.current.pos;
      const next = Math.max(min, Math.min(max, startRef.current.size + delta));
      onSize(next);
    },
    [dragging, direction, min, max, onSize]
  );

  const onPointerUp = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      try {
        (e.currentTarget as HTMLElement).releasePointerCapture(e.pointerId);
      } catch {
        /* ignore */
      }
      setDragging(false);
    },
    []
  );

  // Body cursor while dragging so it doesn't flicker as the pointer crosses
  // sibling elements.
  useEffect(() => {
    if (!dragging) return;
    const prev = document.body.style.cursor;
    document.body.style.cursor =
      direction === "vertical" ? "col-resize" : "row-resize";
    return () => {
      document.body.style.cursor = prev;
    };
  }, [dragging, direction]);

  return (
    <div
      className={`splitter splitter-${direction}${dragging ? " dragging" : ""}`}
      data-testid={testId}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={onPointerUp}
      onPointerCancel={onPointerUp}
    />
  );
}
