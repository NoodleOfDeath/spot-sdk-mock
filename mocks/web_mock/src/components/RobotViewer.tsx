import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import {
  fetchRobotState,
  postPowerCommand,
  postWalkCommand,
  type RobotState,
} from "../api.js";
import {
  buildPlaceholder,
  loadSpotModel,
  type SpotRig,
} from "./SpotModel.js";

const BD_BLUE = new THREE.Color("#0057B8");
const GRAY = new THREE.Color("#3a3f46");
const RED = new THREE.Color("#f85149");

const SPOT_LENGTH_M = 0.7;
const HIP_AMPLITUDE = THREE.MathUtils.degToRad(25);
const GAIT_HZ = 2;

declare global {
  interface Window {
    __spotX?: number;
    __spotScale?: number;
  }
}

export function RobotViewer() {
  const mountRef = useRef<HTMLDivElement>(null);
  // The viewer polls its own state at a fast rate so the model translates
  // smoothly while a walk is in flight. We bypass redux to avoid hammering
  // it with re-renders.
  const stateRef = useRef<RobotState | null>(null);
  const resetCameraRef = useRef<(() => void) | null>(null);
  const [walking, setWalking] = useState(false);
  const [showOverlay, setShowOverlay] = useState(true);
  const [powerState, setPowerState] = useState<string>("OFF");
  const [toast, setToast] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    window.setTimeout(() => setToast((t) => (t === msg ? null : t)), 4_000);
  };

  useEffect(() => {
    let cancel = false;
    const tick = async () => {
      if (cancel) return;
      const next = await fetchRobotState();
      if (!cancel && next) {
        stateRef.current = next;
        setWalking(next.locomotion_target_m != null);
        setPowerState(next.power_state.replace(/^STATE_/, ""));
      }
    };
    tick();
    const id = setInterval(tick, 150);
    return () => {
      cancel = true;
      clearInterval(id);
    };
  }, []);

  const replay = async () => {
    if (walking) return;
    setWalking(true);
    try {
      await postWalkCommand(5.0);
    } catch (err) {
      setWalking(false);
      showToast(err instanceof Error ? err.message : String(err));
    }
  };

  const resetPosition = async () => {
    if (walking) return;
    const currentX = stateRef.current?.body_pose_se2?.x ?? 0;
    if (Math.abs(currentX) < 1e-3) return;
    setWalking(true);
    try {
      await postWalkCommand(-currentX);
    } catch (err) {
      setWalking(false);
      showToast(err instanceof Error ? err.message : String(err));
    }
  };

  const togglePower = async () => {
    const isOn = powerState === "ON";
    try {
      await postPowerCommand(!isOn);
    } catch (err) {
      showToast(err instanceof Error ? err.message : String(err));
    }
  };
  const powerBusy = powerState === "POWERING_ON" || powerState === "POWERING_OFF";

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#0a0d12");

    const camera = new THREE.PerspectiveCamera(
      50,
      mount.clientWidth / Math.max(mount.clientHeight, 1),
      0.1,
      100
    );
    const CAM_OFFSET = new THREE.Vector3(2.6, 1.6, 3.5);
    camera.position.copy(CAM_OFFSET);
    camera.lookAt(0, 0.4, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.4;
    mount.appendChild(renderer.domElement);

    const pmrem = new THREE.PMREMGenerator(renderer);
    scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0, 0.4, 0);
    controls.minDistance = 1.5;
    controls.maxDistance = 12;
    controls.maxPolarAngle = Math.PI * 0.495;
    controls.enablePan = true;
    controls.touches = {
      ONE: THREE.TOUCH.ROTATE,
      TWO: THREE.TOUCH.DOLLY_PAN,
    };

    scene.add(new THREE.GridHelper(20, 40, 0x30363d, 0x161b22));
    scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 0.6);
    key.position.set(3, 4, 2);
    scene.add(key);
    // Warm point light overhead so the GLB picks up specular detail.
    // distance=0 → no falloff (infinite range), full intensity at the model.
    const point = new THREE.PointLight(0xffffff, 3, 0);
    point.position.set(2, 4, 3);
    scene.add(point);
    mount.dataset.pointLight = "true";

    let rig: SpotRig = buildPlaceholder();
    scene.add(rig.root);

    resetCameraRef.current = () => {
      const x = rig.root.position.x;
      controls.target.set(x, 0.4, 0);
      camera.position.set(x + CAM_OFFSET.x, CAM_OFFSET.y, CAM_OFFSET.z);
      controls.update();
    };

    let unitsPerMeter = 1.0;
    window.__spotScale = unitsPerMeter;
    window.__spotX = rig.root.position.x;
    const groundY = rig.root.position.y;

    let cancelled = false;
    loadSpotModel().then((real) => {
      if (cancelled || !real) return;
      scene.remove(rig.root);
      rig = real;
      // Rotate so the body's long axis aligns with +X, the direction of
      // motion for a straight walk.
      rig.root.rotation.y = -Math.PI / 2;
      scene.add(rig.root);
      setShowOverlay(false);
      const bbox = new THREE.Box3().setFromObject(real.root);
      const size = new THREE.Vector3();
      bbox.getSize(size);
      const modelLen = Math.max(size.x, size.z);
      unitsPerMeter = modelLen > 0 ? modelLen / SPOT_LENGTH_M : 1.0;
      window.__spotScale = unitsPerMeter;
    });

    const setStance = (raised: boolean) => {
      if (!rig.isPlaceholder) return;
      rig.body.position.y = raised ? 0.5 : 0.18;
      for (const hip of rig.hips) hip.position.y = raised ? 0.35 : 0.05;
    };
    setStance(false);

    const start = performance.now();
    let raf = 0;
    const animate = () => {
      const t = (performance.now() - start) / 1000;
      const s = stateRef.current;
      const standing =
        !!s && (s.power_state === "ON" || s.stand_state === "standing");
      setStance(standing);

      // Movement (and gait) only happens when motors are ON. While the
      // robot is powered off / powering up / down, the model stays parked
      // at its last seen pose.
      const powered =
        s?.power_state === "ON" || s?.power_state === "STATE_ON";
      const bx = powered ? s?.body_pose_se2?.x ?? 0 : window.__spotX != null
        ? (window.__spotX as number) / unitsPerMeter
        : 0;
      const targetX = bx * unitsPerMeter;
      rig.root.position.x = targetX;
      rig.root.position.y = groundY;
      rig.root.position.z = 0;
      window.__spotX = rig.root.position.x;

      const isWalking =
        powered &&
        s?.locomotion_target_m != null &&
        s.locomotion_target_m > 0;

      // Leg gait only animates while locomotion is in flight; otherwise
      // legs freeze (placeholder rig only — the real GLB has no per-leg
      // controls).
      if (rig.isPlaceholder && rig.hips.length === 4) {
        if (isWalking) {
          const phase = Math.sin(2 * Math.PI * GAIT_HZ * t);
          const pairA = [rig.hips[0], rig.hips[3]];
          const pairB = [rig.hips[1], rig.hips[2]];
          for (const hip of pairA) hip.rotation.z = phase * HIP_AMPLITUDE;
          for (const hip of pairB) hip.rotation.z = -phase * HIP_AMPLITUDE;
        } else {
          for (const hip of rig.hips) hip.rotation.z = 0;
        }
      }

      const bodyMat = rig.body.material as THREE.MeshStandardMaterial;
      if (s?.estop_cut) {
        const flash = Math.sin(t * 8) > 0;
        bodyMat.color.copy(flash ? RED : BD_BLUE);
      } else if (isWalking || standing) {
        bodyMat.color.copy(BD_BLUE);
        if (rig.isPlaceholder && !isWalking) {
          rig.body.rotation.z = Math.sin(t * 1.8) * 0.02;
        }
      } else {
        bodyMat.color.copy(GRAY);
        if (rig.isPlaceholder) rig.body.rotation.z = 0;
      }

      // Camera follows the body while a walk is in flight; otherwise it
      // sits at the fixed initial offset.
      if (isWalking) {
        controls.target.set(targetX, 0.4, 0);
        camera.position.set(
          targetX + CAM_OFFSET.x,
          CAM_OFFSET.y,
          CAM_OFFSET.z
        );
      }
      controls.update();
      renderer.render(scene, camera);
      raf = requestAnimationFrame(animate);
    };
    raf = requestAnimationFrame(animate);

    const onResize = () => {
      if (!mount) return;
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      camera.aspect = w / Math.max(h, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);
    const ro = new ResizeObserver(onResize);
    ro.observe(mount);

    return () => {
      cancelled = true;
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      ro.disconnect();
      controls.dispose();
      pmrem.dispose();
      renderer.dispose();
      mount.removeChild(renderer.domElement);
      resetCameraRef.current = null;
      window.__spotX = undefined;
      window.__spotScale = undefined;
    };
  }, []);

  const resetCamera = () => resetCameraRef.current?.();

  return (
    <div
      ref={mountRef}
      data-testid="robot-viewer"
      className="three-mount"
      style={{ position: "relative", width: "100%", height: "100%" }}
    >
      <div className="walk-controls">
        <button
          type="button"
          data-testid="walk-replay"
          className="walk-btn walk-btn-primary"
          onClick={replay}
          disabled={walking}
        >
          {walking ? "Walking…" : "Replay walk 5 m"}
        </button>
        <button
          type="button"
          data-testid="walk-reset"
          className="walk-btn"
          onClick={resetPosition}
          disabled={walking}
        >
          Return to Dock
        </button>
        <button
          type="button"
          data-testid="camera-reset"
          className="walk-btn"
          onClick={resetCamera}
        >
          Reset Camera
        </button>
      </div>
      <div className="power-overlay">
        <button
          type="button"
          data-testid="power-button"
          data-power-state={powerState}
          className={
            powerState === "ON" || powerState === "POWERING_ON"
              ? "power-btn power-btn-off"
              : "power-btn power-btn-on"
          }
          onClick={togglePower}
          disabled={powerBusy}
          aria-label={
            powerState === "ON" || powerState === "POWERING_ON"
              ? "Power Off"
              : "Power On"
          }
        >
          {powerBusy ? (
            <>
              <span className="spinner" aria-hidden="true" />
              {powerState === "POWERING_ON" ? "Powering On…" : "Powering Off…"}
            </>
          ) : powerState === "ON" ? (
            "Power Off"
          ) : (
            "Power On"
          )}
        </button>
      </div>
      {toast && (
        <div
          className="toast"
          data-testid="toast"
          role="alert"
          aria-live="assertive"
        >
          {toast}
        </div>
      )}
      {showOverlay && <PlaceholderOverlay />}
    </div>
  );
}

export function PlaceholderOverlay() {
  return (
    <div className="model-overlay" data-testid="placeholder-overlay">
      <strong>Placeholder model</strong>
      <span>
        Box + cylinders stand-in — drop a real .glb at{" "}
        <code>mocks/web_mock/public/spot.glb</code> to replace it.{" "}
        <a
          href="https://sketchfab.com/3d-models/boston-dynamics-robot-spot-71354fd599e34db898a7d083851b792a"
          target="_blank"
          rel="noreferrer"
        >
          Sketchfab source
        </a>
        .
      </span>
      <span className="hint">
        Click + drag (or one-finger touch) to orbit · two-finger pinch to zoom.
      </span>
    </div>
  );
}
