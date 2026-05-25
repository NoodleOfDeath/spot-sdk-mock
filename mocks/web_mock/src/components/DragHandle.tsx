import { useRef } from "react";

interface DragHandleProps {
  onDrag: (deltaY: number) => void;
  testId?: string;
  ariaLabel?: string;
}

/**
 * 8 px horizontal bar that reports vertical pointer drag deltas. Parent
 * is responsible for applying the deltas to the surrounding panel heights
 * (so it can enforce min/max clamps).
 */
export function DragHandle({
  onDrag,
  testId = "panel-drag-handle",
  ariaLabel = "Resize panels",
}: DragHandleProps) {
  const lastYRef = useRef<number | null>(null);
  const activePointerRef = useRef<number | null>(null);

  const onPointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    e.preventDefault();
    activePointerRef.current = e.pointerId;
    lastYRef.current = e.clientY;
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    e.currentTarget.classList.add("dragging");
  };

  const onPointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (activePointerRef.current !== e.pointerId) return;
    if (lastYRef.current === null) return;
    const dy = e.clientY - lastYRef.current;
    lastYRef.current = e.clientY;
    if (dy !== 0) onDrag(dy);
  };

  const release = (e: React.PointerEvent<HTMLDivElement>) => {
    if (activePointerRef.current !== e.pointerId) return;
    activePointerRef.current = null;
    lastYRef.current = null;
    try {
      (e.target as HTMLElement).releasePointerCapture(e.pointerId);
    } catch {
      /* ignore */
    }
    e.currentTarget.classList.remove("dragging");
  };

  return (
    <div
      className="panel-drag-handle"
      data-testid={testId}
      role="separator"
      aria-orientation="horizontal"
      aria-label={ariaLabel}
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onPointerUp={release}
      onPointerCancel={release}
    />
  );
}
