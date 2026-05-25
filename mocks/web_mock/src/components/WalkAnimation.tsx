import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { useAppSelector } from "../store/index.js";
import {
  buildPlaceholder,
  loadSpotModel,
  type SpotRig,
} from "./SpotModel.js";
import { PlaceholderOverlay } from "./RobotViewer.js";

const BD_BLUE = new THREE.Color("#0057B8");
const GRAY = new THREE.Color("#3a3f46");
const RED = new THREE.Color("#f85149");

const HIP_AMPLITUDE = THREE.MathUtils.degToRad(25); // ±25°
const GAIT_HZ = 2;

export function WalkAnimation() {
  const mountRef = useRef<HTMLDivElement>(null);
  const state = useAppSelector((s) => s.robot.current);
  const stateRef = useRef(state);
  stateRef.current = state;

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
    camera.position.set(2.6, 1.6, 3.5);
    camera.lookAt(0, 0.4, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

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

    scene.add(new THREE.GridHelper(6, 12, 0x30363d, 0x161b22));
    scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 0.6);
    key.position.set(3, 4, 2);
    scene.add(key);

    let rig: SpotRig = buildPlaceholder();
    scene.add(rig.root);

    let cancelled = false;
    loadSpotModel().then((real) => {
      if (cancelled || !real) return;
      scene.remove(rig.root);
      rig = real;
      scene.add(rig.root);
    });

    const start = performance.now();
    let raf = 0;
    const animate = () => {
      const t = (performance.now() - start) / 1000;
      const s = stateRef.current;
      const mission = s?.mission_state ?? "IDLE";

      const bodyMat = rig.body.material as THREE.MeshStandardMaterial;
      const placeholder = rig.isPlaceholder;

      if (mission === "PLAYING") {
        if (placeholder) {
          const phase = Math.sin(2 * Math.PI * GAIT_HZ * t);
          const pairA = [rig.hips[0], rig.hips[3]];
          const pairB = [rig.hips[1], rig.hips[2]];
          for (const hip of pairA) hip.rotation.z = phase * HIP_AMPLITUDE;
          for (const hip of pairB) hip.rotation.z = -phase * HIP_AMPLITUDE;
          rig.body.position.y =
            0.5 + 0.03 * Math.sin(2 * Math.PI * GAIT_HZ * 2 * t);
        } else {
          // Real model: gentle bob + slight yaw to suggest motion.
          rig.root.position.y = 0.03 * Math.sin(2 * Math.PI * GAIT_HZ * 2 * t);
          rig.root.rotation.y = Math.sin(t * 0.5) * 0.08;
        }
        bodyMat.color.copy(BD_BLUE);
      } else if (mission === "PAUSED") {
        if (placeholder) rig.body.position.y = 0.5;
        else {
          rig.root.position.y = 0;
          rig.root.rotation.y = 0;
        }
        bodyMat.color.copy(BD_BLUE).multiplyScalar(0.6);
      } else {
        if (placeholder) {
          for (const hip of rig.hips) hip.rotation.z = 0;
          rig.body.position.y = 0.5;
        } else {
          rig.root.position.y = 0;
          rig.root.rotation.y = 0;
        }
        bodyMat.color.copy(GRAY);
      }
      if (s?.estop_cut) {
        const flash = Math.sin(t * 8) > 0;
        bodyMat.color.copy(flash ? RED : BD_BLUE);
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
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      data-testid="walk-animation"
      style={{ position: "relative", width: "100%", height: "100%" }}
    >
      <PlaceholderOverlay variant="walk" />
    </div>
  );
}
