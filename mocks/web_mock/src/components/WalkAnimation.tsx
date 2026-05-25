import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import {
  fetchRobotState,
  postWalkCommand,
  type RobotState,
} from "../api.js";
import {
  buildPlaceholder,
  loadSpotModel,
  type SpotRig,
} from "./SpotModel.js";
import { PlaceholderOverlay } from "./RobotViewer.js";

const BD_BLUE = new THREE.Color("#0057B8");
const GRAY = new THREE.Color("#3a3f46");
const RED = new THREE.Color("#f85149");

// Real-world body length of Spot in metres. Combined with the model's
// bounding-box X extent at load time, this gives Three.js-units-per-metre.
const SPOT_LENGTH_M = 0.7;

declare global {
  interface Window {
    __spotX?: number;
    __spotScale?: number;
  }
}

export function WalkAnimation() {
  const mountRef = useRef<HTMLDivElement>(null);
  // The Walk panel polls its own state at a much higher rate than the
  // 2 s app-wide poll so the model translates smoothly while a walk is in
  // flight. We bypass redux to avoid hammering it with re-renders.
  const stateRef = useRef<RobotState | null>(null);
  const [walking, setWalking] = useState(false);

  useEffect(() => {
    let cancel = false;
    const tick = async () => {
      if (cancel) return;
      const next = await fetchRobotState();
      if (!cancel && next) {
        stateRef.current = next;
        setWalking(next.locomotion_target_m != null);
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
    } catch {
      setWalking(false);
    }
  };

  const resetPosition = async () => {
    if (walking) return;
    const currentX = stateRef.current?.body_pose_se2?.x ?? 0;
    if (Math.abs(currentX) < 1e-3) return;
    setWalking(true);
    try {
      await postWalkCommand(-currentX);
    } catch {
      setWalking(false);
    }
  };

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
    // Camera holds a fixed XZ offset behind+above the body so the model
    // stays framed as it slides.
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
    const point = new THREE.PointLight(0xffffff, 3, 0);
    point.position.set(2, 4, 3);
    scene.add(point);

    let rig: SpotRig = buildPlaceholder();
    scene.add(rig.root);

    // Three.js units per real-world metre. Computed once the real GLB has
    // loaded from its bounding-box X extent, then fixed for the session.
    let unitsPerMeter = 1.0;
    window.__spotScale = unitsPerMeter;
    window.__spotX = rig.root.position.x;
    const groundY = rig.root.position.y;

    let cancelled = false;
    loadSpotModel().then((real) => {
      if (cancelled || !real) return;
      scene.remove(rig.root);
      rig = real;
      // Rotate 90° so the body's long axis aligns with +X, the direction
      // of motion for a straight walk.
      rig.root.rotation.y = -Math.PI / 2;
      scene.add(rig.root);
      const bbox = new THREE.Box3().setFromObject(real.root);
      const size = new THREE.Vector3();
      bbox.getSize(size);
      const modelLen = Math.max(size.x, size.z); // forward axis dimension
      unitsPerMeter = modelLen > 0 ? modelLen / SPOT_LENGTH_M : 1.0;
      window.__spotScale = unitsPerMeter;
    });

    const start = performance.now();
    let raf = 0;
    const animate = () => {
      const t = (performance.now() - start) / 1000;
      const s = stateRef.current;
      const bodyMat = rig.body.material as THREE.MeshStandardMaterial;

      // Ground-plane translation driven by body_pose_se2.x. ``position.y``
      // is the ground plane (kept constant), ``position.z`` stays 0 — SE2
      // has no Z-axis movement.
      const bx = s?.body_pose_se2?.x ?? 0;
      const targetX = bx * unitsPerMeter;
      rig.root.position.x = targetX;
      rig.root.position.y = groundY;
      rig.root.position.z = 0;
      window.__spotX = rig.root.position.x;

      const walking =
        s?.locomotion_target_m != null && s.locomotion_target_m > 0;

      if (walking) {
        bodyMat.color.copy(BD_BLUE);
      } else if (s?.estop_cut) {
        const flash = Math.sin(t * 8) > 0;
        bodyMat.color.copy(flash ? RED : BD_BLUE);
      } else {
        bodyMat.color.copy(GRAY);
      }

      // Camera tracks the body with a fixed offset so the model stays framed.
      controls.target.set(targetX, 0.4, 0);
      camera.position.set(targetX + CAM_OFFSET.x, CAM_OFFSET.y, CAM_OFFSET.z);
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
      window.__spotX = undefined;
      window.__spotScale = undefined;
    };
  }, []);

  return (
    <div
      ref={mountRef}
      data-testid="walk-animation"
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
          Reset position
        </button>
      </div>
      <PlaceholderOverlay variant="walk" />
    </div>
  );
}
