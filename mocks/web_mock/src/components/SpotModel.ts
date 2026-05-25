/**
 * Loader for the Sketchfab "Boston Dynamics — Spot" model. Drop the
 * downloaded ``.glb`` at ``mocks/web_mock/public/spot.glb`` (Git LFS tracks
 * ``*.glb`` via ``.gitattributes``).
 *
 * Source: https://sketchfab.com/3d-models/boston-dynamics-robot-spot-71354fd599e34db898a7d083851b792a
 * License: see Sketchfab page (free, attribution required).
 */
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const MODEL_URL = "/spot.glb";

export type SpotRig = {
  /** The full model group — add this to your scene. */
  root: THREE.Object3D;
  /** The body mesh (used for color/material tweaks during state changes). */
  body: THREE.Mesh;
  /** Hip pivots for the four legs (FL, FR, RL, RR), or [] if model is real. */
  hips: THREE.Group[];
  /** True when the placeholder (box+legs) is in use. */
  isPlaceholder: boolean;
};

const BD_BLUE = new THREE.Color("#0057B8");

export function buildPlaceholder(): SpotRig {
  const root = new THREE.Group();
  const bodyMat = new THREE.MeshStandardMaterial({
    color: BD_BLUE,
    roughness: 0.5,
    metalness: 0.2,
  });
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.1, 0.35, 0.55), bodyMat);
  body.position.y = 0.5;
  root.add(body);

  const legMat = new THREE.MeshStandardMaterial({
    color: 0x222831,
    roughness: 0.7,
  });
  const hipPositions: Array<[number, number]> = [
    [0.45, 0.22],
    [0.45, -0.22],
    [-0.45, 0.22],
    [-0.45, -0.22],
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
  return { root, body, hips, isPlaceholder: true };
}

/**
 * Try to load the real Spot model from ``/spot.glb``. Resolves with
 * ``null`` if the file isn't present so callers can fall back to the
 * placeholder rig.
 */
export function loadSpotModel(): Promise<SpotRig | null> {
  return new Promise((resolve) => {
    const loader = new GLTFLoader();
    loader.load(
      MODEL_URL,
      (gltf) => {
        const root = gltf.scene;
        // Normalize scale so the model lands in roughly the same volume as
        // the placeholder body (1.1 × 0.35 × 0.55).
        const bbox = new THREE.Box3().setFromObject(root);
        const size = new THREE.Vector3();
        bbox.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);
        if (maxDim > 0) {
          const target = 1.1;
          const scale = target / maxDim;
          root.scale.setScalar(scale);
        }
        const recalc = new THREE.Box3().setFromObject(root);
        root.position.y -= recalc.min.y; // settle on the grid
        // Find a "body" mesh to recolor; fall back to the first mesh.
        let body: THREE.Mesh | undefined;
        root.traverse((obj) => {
          if (!body && obj instanceof THREE.Mesh) body = obj;
        });
        if (!body) {
          resolve(null);
          return;
        }
        resolve({ root, body, hips: [], isPlaceholder: false });
      },
      undefined,
      () => resolve(null)
    );
  });
}
