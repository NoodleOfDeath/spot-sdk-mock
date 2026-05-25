import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { useAppSelector } from "../store/index.js";
import {
  buildPlaceholder,
  loadSpotModel,
  type SpotRig,
} from "./SpotModel.js";

const BD_BLUE = new THREE.Color("#0057B8");
const GRAY = new THREE.Color("#3a3f46");
const RED = new THREE.Color("#f85149");

export function RobotViewer() {
  const mountRef = useRef<HTMLDivElement>(null);
  const state = useAppSelector((s) => s.robot.current);
  const stateRef = useRef(state);
  stateRef.current = state;
  const [showOverlay, setShowOverlay] = useState(true);

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
    camera.position.set(2.5, 1.6, 3.5);
    camera.lookAt(0, 0.4, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.4;
    mount.appendChild(renderer.domElement);

    // PBR materials in the GLB need an environment map to look like anything
    // other than flat-dark. RoomEnvironment is a cheap built-in approximation
    // of a softbox/HDR — it's what makes the model legible even at low
    // light intensities.
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

    scene.add(new THREE.GridHelper(6, 12, 0x30363d, 0x161b22));
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

    let cancelled = false;
    loadSpotModel().then((real) => {
      if (cancelled || !real) return;
      scene.remove(rig.root);
      rig = real;
      scene.add(rig.root);
      setShowOverlay(false);
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

      const bodyMat = rig.body.material as THREE.MeshStandardMaterial;
      if (s?.estop_cut) {
        const flash = Math.sin(t * 8) > 0;
        bodyMat.color.copy(flash ? RED : BD_BLUE);
      } else if (standing) {
        bodyMat.color.copy(BD_BLUE);
        if (rig.isPlaceholder) rig.body.rotation.z = Math.sin(t * 1.8) * 0.02;
      } else {
        bodyMat.color.copy(GRAY);
        if (rig.isPlaceholder) rig.body.rotation.z = 0;
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
    };
  }, []);

  return (
    <div
      ref={mountRef}
      data-testid="robot-viewer"
      className="three-mount"
      style={{ position: "relative", width: "100%", height: "100%" }}
    >
      {showOverlay && <PlaceholderOverlay variant="state" />}
    </div>
  );
}

export function PlaceholderOverlay({
  variant,
}: {
  variant: "state" | "walk";
}) {
  return (
    <div className="model-overlay" data-testid="placeholder-overlay">
      <strong>Placeholder model</strong>
      <span>
        {variant === "walk"
          ? "Cartoon walk animation — drop a real .glb at "
          : "Box + cylinders stand-in — drop a real .glb at "}
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
