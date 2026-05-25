import { useEffect, useRef } from "react";
import * as THREE from "three";
import { useRobotState } from "../hooks/useRobotState.js";

const BD_BLUE = new THREE.Color("#0057B8");
const GRAY = new THREE.Color("#3a3f46");
const RED = new THREE.Color("#f85149");

export function RobotViewer() {
  const mountRef = useRef<HTMLDivElement>(null);
  const state = useRobotState(2000);
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#0a0d12");
    const aspect = mount.clientWidth / Math.max(mount.clientHeight, 1);
    const camera = new THREE.PerspectiveCamera(50, aspect, 0.1, 100);
    camera.position.set(2.5, 1.6, 3.5);
    camera.lookAt(0, 0.4, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    // Floor grid
    const grid = new THREE.GridHelper(6, 12, 0x30363d, 0x161b22);
    scene.add(grid);

    // Lighting
    const hemi = new THREE.HemisphereLight(0xffffff, 0x444444, 1.1);
    scene.add(hemi);
    const key = new THREE.DirectionalLight(0xffffff, 0.6);
    key.position.set(3, 4, 2);
    scene.add(key);

    // Spot body
    const bodyMat = new THREE.MeshStandardMaterial({
      color: GRAY,
      roughness: 0.5,
      metalness: 0.2,
    });
    const body = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.35, 0.55), bodyMat);
    scene.add(body);

    const legMat = new THREE.MeshStandardMaterial({
      color: 0x222831,
      roughness: 0.7,
    });
    const legPositions: [number, number][] = [
      [0.45, 0.22],
      [0.45, -0.22],
      [-0.45, 0.22],
      [-0.45, -0.22],
    ];
    const legs: THREE.Mesh[] = [];
    for (const [x, z] of legPositions) {
      const leg = new THREE.Mesh(
        new THREE.CylinderGeometry(0.04, 0.04, 0.45, 12),
        legMat
      );
      leg.position.set(x, -0.2, z);
      scene.add(leg);
      legs.push(leg);
    }

    const setStance = (raised: boolean) => {
      body.position.y = raised ? 0.5 : 0.18;
      for (const leg of legs) leg.position.y = raised ? -0.05 : -0.2;
    };
    setStance(false);

    let flashPhase = 0;
    const start = performance.now();
    const animate = () => {
      const t = (performance.now() - start) / 1000;
      const s = stateRef.current;
      const standing =
        !!s && (s.power_state === "ON" || s.stand_state === "standing");
      setStance(standing);

      if (s?.estop_cut) {
        flashPhase = (flashPhase + 0.1) % 1;
        bodyMat.color.lerpColors(BD_BLUE, RED, flashPhase > 0.5 ? 1 : 0.2);
      } else if (standing) {
        bodyMat.color.copy(BD_BLUE);
        body.rotation.z = Math.sin(t * 1.8) * 0.02;
      } else {
        bodyMat.color.copy(GRAY);
        body.rotation.z = 0;
      }

      renderer.render(scene, camera);
      raf = requestAnimationFrame(animate);
    };
    let raf = requestAnimationFrame(animate);

    const onResize = () => {
      if (!mount) return;
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      camera.aspect = w / Math.max(h, 1);
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  return (
    <div
      ref={mountRef}
      data-testid="robot-viewer"
      style={{ width: "100%", height: "100%" }}
    />
  );
}
