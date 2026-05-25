import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useAppSelector } from "../store/index.js";
import { TestPanel } from "./TestPanel.js";
import { DragHandle } from "./DragHandle.js";

const HANDLE_PX = 8;
const MIN_PANEL_PX = 120;

/**
 * Two vertically stacked, independently resizable panels split between
 * local (``mocks/robot_mock/tests/``) and vendor SDK tests. Heights live
 * here so the DragHandle in the middle can clamp both sides to
 * ``MIN_PANEL_PX``.
 */
export function TestList() {
  const local = useAppSelector((s) => s.tests.local);
  const vendor = useAppSelector((s) => s.tests.vendor);
  const loading = useAppSelector((s) => s.tests.loading);
  const error = useAppSelector((s) => s.tests.error);

  const containerRef = useRef<HTMLDivElement>(null);
  const [containerH, setContainerH] = useState(0);
  const [localH, setLocalH] = useState(0);
  const initializedRef = useRef(false);

  // Measure the container once mounted and re-measure on resize. We only
  // seed the initial 50/50 split once the container has a real (non-zero)
  // height so the panel doesn't get stuck at the minimum.
  useLayoutEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const measure = () => {
      const h = el.clientHeight;
      if (h <= 0) return;
      setContainerH(h);
      if (!initializedRef.current) {
        initializedRef.current = true;
        setLocalH(Math.max(MIN_PANEL_PX, Math.floor((h - HANDLE_PX) / 2)));
      }
    };
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Clamp localH if the container shrinks below what would leave the
  // vendor panel its minimum.
  useEffect(() => {
    if (containerH === 0) return;
    const maxLocal = containerH - HANDLE_PX - MIN_PANEL_PX;
    if (localH > maxLocal) setLocalH(Math.max(MIN_PANEL_PX, maxLocal));
  }, [containerH, localH]);

  const vendorH = Math.max(MIN_PANEL_PX, containerH - HANDLE_PX - localH);

  const onDrag = (dy: number) => {
    setLocalH((prev) => {
      const next = prev + dy;
      const maxLocal = containerH - HANDLE_PX - MIN_PANEL_PX;
      return Math.min(Math.max(MIN_PANEL_PX, next), Math.max(MIN_PANEL_PX, maxLocal));
    });
  };

  if (error) {
    return <p style={{ color: "var(--red)" }}>Failed to load tests: {error}</p>;
  }
  if (loading && local.length === 0 && vendor.length === 0) {
    return <p style={{ color: "var(--muted)" }}>Loading tests…</p>;
  }

  return (
    <div className="test-list-split" data-testid="test-list" ref={containerRef}>
      <TestPanel
        title="Custom Tests"
        source="local"
        tests={local}
        height={localH}
        searchLabel="Filter custom tests"
        runAllTestId="run-all-local"
        searchTestId="search-local"
        panelTestId="local-test-panel"
      />
      <DragHandle
        onDrag={onDrag}
        testId="panels-drag-handle"
        ariaLabel="Resize test panels"
      />
      <TestPanel
        title="Spot SDK Tests"
        source="vendor"
        tests={vendor}
        height={vendorH}
        searchLabel="Filter SDK tests"
        runAllTestId="run-all-vendor"
        searchTestId="search-vendor"
        panelTestId="vendor-test-panel"
      />
    </div>
  );
}
