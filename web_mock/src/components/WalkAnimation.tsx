import { useEffect, useRef } from "react";
import * as THREE from "three";
import { useAppSelector } from "../store/index.js";

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

    scene.add(new THREE.GridHelper(6, 12, 0x30363d, 0x161b22));
    scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.1));
    const key = new THREE.DirectionalLight(0xffffff, 0.6);
    key.position.set(3, 4, 2);
    scene.add(key);

    const bodyMat = new THREE.MeshStandardMaterial({
      color: BD_BLUE,
      roughness: 0.5,
      metalness: 0.2,
    });
    const body = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.35, 0.55), bodyMat);
    body.position.y = 0.5;
    scene.add(body);

    const legMat = new THREE.MeshStandardMaterial({
      color: 0x222831,
      roughness: 0.7,
    });
    // Each leg is a hip-pivoted group: front-left, front-right, rear-left, rear-right.
    const hipPositions: Array<[number, number]> = [
      [0.45, 0.22], // FL
      [0.45, -0.22], // FR
      [-0.45, 0.22], // RL
      [-0.45, -0.22], // RR
    ];
    const hips: THREE.Group[] = [];
    for (const [x, z] of hipPositions) {
      const hip = new THREE.Group();
      hip.position.set(x, 0.35, z);
      body.add(hip);
      const leg = new THREE.Mesh(
        new THREE.CylinderGeometry(0.04, 0.04, 0.45, 12),
        legMat
      );
      leg.position.y = -0.225;
      hip.add(leg);
      hips.push(hip);
    }

    // Trot pairs: diagonals (FL + RR) and (FR + RL).
    const pairA = [hips[0], hips[3]];
    const pairB = [hips[1], hips[2]];

    const start = performance.now();
    let raf = 0;
    const animate = () => {
      const t = (performance.now() - start) / 1000;
      const s = stateRef.current;
      const mission = s?.mission_state ?? "IDLE";

      if (mission === "PLAYING") {
        const phase = Math.sin(2 * Math.PI * GAIT_HZ * t);
        for (const hip of pairA) hip.rotation.z = phase * HIP_AMPLITUDE;
        for (const hip of pairB) hip.rotation.z = -phase * HIP_AMPLITUDE;
        body.position.y = 0.5 + 0.03 * Math.sin(2 * Math.PI * GAIT_HZ * 2 * t);
        bodyMat.color.copy(BD_BLUE);
      } else if (mission === "PAUSED") {
        // freeze legs in place, body settles
        body.position.y = 0.5;
        bodyMat.color.copy(BD_BLUE).multiplyScalar(0.6);
      } else {
        // IDLE: standing pose, all hips at zero
        for (const hip of hips) hip.rotation.z = 0;
        body.position.y = 0.5;
        bodyMat.color.copy(GRAY);
      }
      if (s?.estop_cut) {
        const flash = Math.sin(t * 8) > 0;
        bodyMat.color.copy(flash ? RED : BD_BLUE);
      }

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
      data-testid="walk-animation"
      style={{ width: "100%", height: "100%" }}
    />
  );
}
