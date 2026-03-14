/**
 * Three.js 3D Toronto: reflective materials, colorful buildings, streets, pedestrians.
 * Lake Ontario reflects environment; simulation state drives day/night, economy lights, pollution fog.
 */
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { CityState } from "../types/city-state.js";

// More realistic, colorful palette
const BUILDING_MATERIALS: Array<{ color: number; metalness: number; roughness: number; isGlass?: boolean }> = [
  { color: 0x4a90a4, metalness: 0.7, roughness: 0.15, isGlass: true },  // blue glass
  { color: 0x5a9b6e, metalness: 0.6, roughness: 0.2, isGlass: true },   // green glass
  { color: 0xc4a574, metalness: 0.1, roughness: 0.85 },                 // sand/brick
  { color: 0xb85450, metalness: 0.05, roughness: 0.9 },                // brick red
  { color: 0x8b7355, metalness: 0.1, roughness: 0.8 },                 // brown
  { color: 0x9ca3af, metalness: 0.3, roughness: 0.6 },                 // concrete
  { color: 0xd4c4a8, metalness: 0.15, roughness: 0.75 },                // beige
  { color: 0x6b7b8c, metalness: 0.5, roughness: 0.35 },                 // blue-gray
  { color: 0xa8c5c9, metalness: 0.65, roughness: 0.2, isGlass: true },   // light blue glass
  { color: 0x7d6e83, metalness: 0.2, roughness: 0.7 },                 // mauve
];

const STREET_COLOR = 0x2c2c2e;
const SIDEWALK_COLOR = 0x6b6b6e;
const GRASS_COLOR = 0x3d5a3d;

export interface TorontoSceneOptions {
  canvas: HTMLCanvasElement;
  onResize?: () => void;
}

interface Pedestrian {
  group: THREE.Group;
  path: THREE.Vector3[];
  t: number;
  speed: number;
  walkPhase: number;
}

export class TorontoScene {
  private scene: THREE.Scene;
  private camera: THREE.PerspectiveCamera;
  private renderer: THREE.WebGLRenderer;
  private controls: OrbitControls;
  private cnTower: THREE.Group;
  private buildings: THREE.Mesh[] = [];
  private buildingLights: THREE.PointLight[] = [];
  private sunLight: THREE.DirectionalLight;
  private ambientLight: THREE.AmbientLight;
  private lake: THREE.Mesh;
  private fog: THREE.Fog;
  private clock = new THREE.Clock();
  private animationId: number = 0;
  private pedestrians: Pedestrian[] = [];
  private pedestrianPaths: THREE.Vector3[][] = [];
  private envMap: THREE.Texture | null = null;

  constructor(options: TorontoSceneOptions) {
    const { canvas } = options;
    this.scene = new THREE.Scene();
    this.fog = new THREE.Fog(0x87ceeb, 80, 350);
    this.scene.fog = this.fog;

    this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 2000);
    this.camera.position.set(120, 80, 120);
    this.camera.lookAt(0, 15, 0);

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x87b5d3);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;

    this.setupEnvironment();

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.minDistance = 40;
    this.controls.maxDistance = 400;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.1;
    this.controls.target.set(0, 15, 0);

    this.ambientLight = new THREE.AmbientLight(0x6699bb, 0.35);
    this.scene.add(this.ambientLight);

    this.sunLight = new THREE.DirectionalLight(0xfff5e6, 0.95);
    this.sunLight.position.set(80, 120, 60);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.set(2048, 2048);
    this.sunLight.shadow.camera.near = 0.5;
    this.sunLight.shadow.camera.far = 400;
    this.sunLight.shadow.camera.left = -120;
    this.sunLight.shadow.camera.right = 120;
    this.sunLight.shadow.camera.top = 120;
    this.sunLight.shadow.camera.bottom = -120;
    this.scene.add(this.sunLight);

    this.createStreetsAndBlocks();
    this.lake = this.createLake();
    this.scene.add(this.lake);
    this.cnTower = this.createCNTower();
    this.scene.add(this.cnTower);
    this.createDowntownBuildings();
    this.createPedestrians();

    this.resize();
    window.addEventListener("resize", () => this.resize());
  }

  private setupEnvironment(): void {
    const skyScene = new THREE.Scene();
    const skyGeo = new THREE.SphereGeometry(400, 32, 24, 0, Math.PI * 2, 0, Math.PI / 2);
    const skyMat = new THREE.MeshBasicMaterial({
      color: 0x87ceeb,
      side: THREE.BackSide,
    });
    const sky = new THREE.Mesh(skyGeo, skyMat);
    skyScene.add(sky);
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.envMap = pmrem.fromScene(skyScene).texture;
    this.scene.environment = this.envMap;
    this.scene.background = new THREE.Color(0x87b5d3);
    skyGeo.dispose();
    skyMat.dispose();
  }

  private createLake(): THREE.Mesh {
    const geometry = new THREE.PlaneGeometry(400, 200);
    const material = new THREE.MeshPhysicalMaterial({
      color: 0x1a5a7a,
      metalness: 0.95,
      roughness: 0.05,
      clearcoat: 0.6,
      clearcoatRoughness: 0.1,
      envMapIntensity: 1.2,
    });
    if (this.envMap) material.envMap = this.envMap;
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(0, 0, -180);
    mesh.receiveShadow = true;
    return mesh;
  }

  private createStreetsAndBlocks(): void {
    const spacing = 24;
    const streetW = 10;
    const blockW = spacing - streetW;
    const base = -spacing * 2;

    for (let row = 0; row <= 6; row++) {
      for (let col = 0; col <= 6; col++) {
        const x = base + col * spacing;
        const z = base + row * spacing;
        const isStreet = row === 3 || col === 3;
        if (isStreet) {
          const streetGeo = new THREE.PlaneGeometry(blockW + streetW, blockW + streetW);
          const streetMat = new THREE.MeshStandardMaterial({
            color: STREET_COLOR,
            roughness: 0.95,
            metalness: 0,
          });
          const street = new THREE.Mesh(streetGeo, streetMat);
          street.rotation.x = -Math.PI / 2;
          street.position.set(x, 0.01, z);
          street.receiveShadow = true;
          this.scene.add(street);
        } else {
          const sidewalkGeo = new THREE.PlaneGeometry(blockW, blockW);
          const sidewalkMat = new THREE.MeshStandardMaterial({
            color: SIDEWALK_COLOR,
            roughness: 0.9,
            metalness: 0,
          });
          const sidewalk = new THREE.Mesh(sidewalkGeo, sidewalkMat);
          sidewalk.rotation.x = -Math.PI / 2;
          sidewalk.position.set(x, 0.02, z);
          sidewalk.receiveShadow = true;
          this.scene.add(sidewalk);
          if ((row + col) % 3 === 0) {
            const grassGeo = new THREE.PlaneGeometry(blockW - 4, blockW - 4);
            const grassMat = new THREE.MeshStandardMaterial({
              color: GRASS_COLOR,
              roughness: 0.98,
              metalness: 0,
            });
            const grass = new THREE.Mesh(grassGeo, grassMat);
            grass.rotation.x = -Math.PI / 2;
            grass.position.set(x, 0.03, z);
            this.scene.add(grass);
          }
        }
      }
    }
  }

  private createCNTower(): THREE.Group {
    const group = new THREE.Group();
    const towerMat = this.envMap
      ? new THREE.MeshPhysicalMaterial({
          color: 0x4a5568,
          metalness: 0.85,
          roughness: 0.2,
          envMap: this.envMap,
          envMapIntensity: 1,
        })
      : new THREE.MeshStandardMaterial({
          color: 0x4a5568,
          metalness: 0.85,
          roughness: 0.2,
        });

    const podGeo = new THREE.SphereGeometry(8, 24, 24, 0, Math.PI * 2, 0, Math.PI / 2);
    const pod = new THREE.Mesh(podGeo, towerMat.clone());
    pod.position.y = 52;
    pod.castShadow = true;
    pod.receiveShadow = true;
    group.add(pod);

    const shaftGeo = new THREE.CylinderGeometry(3, 6, 50, 16);
    const shaft = new THREE.Mesh(shaftGeo, towerMat.clone());
    shaft.position.y = 25;
    shaft.castShadow = true;
    group.add(shaft);

    const legMat = new THREE.MeshStandardMaterial({
      color: 0x374151,
      metalness: 0.7,
      roughness: 0.3,
    });
    const legGeo = new THREE.CylinderGeometry(0.5, 1.5, 30, 6);
    for (let i = 0; i < 3; i++) {
      const leg = new THREE.Mesh(legGeo, legMat);
      const angle = (i / 3) * Math.PI * 2 - Math.PI / 2;
      leg.position.x = Math.cos(angle) * 8;
      leg.position.z = Math.sin(angle) * 8;
      leg.position.y = 15;
      leg.rotation.z = -angle;
      leg.castShadow = true;
      group.add(leg);
    }

    const antennaGeo = new THREE.CylinderGeometry(0.3, 0.5, 102, 8);
    const antenna = new THREE.Mesh(antennaGeo, towerMat.clone());
    antenna.position.y = 103;
    antenna.castShadow = true;
    group.add(antenna);

    return group;
  }

  private createDowntownBuildings(): void {
    const grid = [
      [38, 28], [34, 48], [30, 22], [26, 55], [22, 32], [18, 42], [12, 24],
      [40, 20], [32, 40], [28, 52], [24, 30], [20, 45], [14, 28], [10, 36],
      [42, 34], [36, 30], [26, 38], [24, 50], [16, 40], [8, 30],
    ];
    const spacing = 24;
    const streetW = 10;
    const blockW = spacing - streetW;
    const baseX = -spacing * 2 + streetW / 2 + blockW / 2;
    const baseZ = -spacing * 2 + streetW / 2 + blockW / 2;

    const seed = (i: number) => ((i * 7919) % 1000) / 1000;
    for (let i = 0; i < grid.length; i++) {
      const [w, h] = grid[i];
      const matDef = BUILDING_MATERIALS[i % BUILDING_MATERIALS.length];
      const geometry = new THREE.BoxGeometry(w * 0.35, h, w * 0.35);
      const material = matDef.isGlass && this.envMap
        ? new THREE.MeshPhysicalMaterial({
            color: matDef.color,
            metalness: matDef.metalness,
            roughness: matDef.roughness,
            transparent: true,
            opacity: 0.85,
            envMap: this.envMap,
            envMapIntensity: 1.2,
            clearcoat: 0.3,
            clearcoatRoughness: 0.2,
          })
        : new THREE.MeshStandardMaterial({
            color: matDef.color,
            metalness: matDef.metalness,
            roughness: matDef.roughness,
          });
      if (this.envMap && !matDef.isGlass) (material as THREE.MeshStandardMaterial).envMap = this.envMap;
      const building = new THREE.Mesh(geometry, material);
      const col = Math.floor(i / 7);
      const row = i % 7;
      const offsetX = (seed(i) - 0.5) * 3;
      const offsetZ = (seed(i + 100) - 0.5) * 3;
      building.position.x = baseX + row * spacing + offsetX;
      building.position.z = baseZ + col * spacing + offsetZ;
      building.position.y = h / 2;
      building.castShadow = true;
      building.receiveShadow = true;
      this.scene.add(building);
      this.buildings.push(building);

      const light = new THREE.PointLight(0xffeedd, 0.5, 18);
      light.position.copy(building.position);
      light.position.y += h * 0.35 + seed(i + 200) * 5;
      light.position.x += (seed(i + 300) - 0.5) * 4;
      light.position.z += (seed(i + 400) - 0.5) * 4;
      this.scene.add(light);
      this.buildingLights.push(light);
    }
  }

  private createPedestrianPaths(): void {
    const spacing = 24;
    const streetW = 10;
    const halfBlock = (spacing - streetW) / 2;
    const base = -spacing * 2;
    const y = 0.5;
    const paths: THREE.Vector3[][] = [];

    const wx = (col: number) => base + col * spacing + streetW / 2 + halfBlock;
    const wz = (row: number) => base + row * spacing + streetW / 2 + halfBlock;
    const addPath = (points: [number, number][]) => {
      paths.push(points.map(([x, z]) => new THREE.Vector3(x, y, z)));
    };

    for (let i = 0; i <= 6; i++) {
      if (i === 3) continue;
      const z = wz(i);
      addPath([[base + streetW / 2, z], [base + 7 * spacing - streetW / 2, z]]);
      addPath([[base + 7 * spacing - streetW / 2, z], [base + streetW / 2, z]]);
    }
    for (let i = 0; i <= 6; i++) {
      if (i === 3) continue;
      const x = wx(i);
      addPath([[x, base + streetW / 2], [x, base + 7 * spacing - streetW / 2]]);
      addPath([[x, base + 7 * spacing - streetW / 2], [x, base + streetW / 2]]);
    }
    addPath([[wx(2), wz(2)], [wx(5), wz(2)], [wx(5), wz(5)], [wx(2), wz(5)], [wx(2), wz(2)]]);
    addPath([[wx(4), wz(1)], [wx(4), wz(6)]]);
    this.pedestrianPaths = paths;
  }

  private createOnePedestrian(color: number): THREE.Group {
    const group = new THREE.Group();
    const bodyGeo = new THREE.CapsuleGeometry(0.35, 0.9, 4, 8);
    const bodyMat = new THREE.MeshStandardMaterial({
      color,
      roughness: 0.8,
      metalness: 0,
    });
    const body = new THREE.Mesh(bodyGeo, bodyMat);
    body.position.y = 0.45;
    body.castShadow = true;
    group.add(body);
    const headGeo = new THREE.SphereGeometry(0.28, 12, 12);
    const headMat = new THREE.MeshStandardMaterial({
      color: 0xffdbac,
      roughness: 0.9,
      metalness: 0,
    });
    const head = new THREE.Mesh(headGeo, headMat);
    head.position.y = 1.15;
    head.castShadow = true;
    group.add(head);
    return group;
  }

  private createPedestrians(): void {
    this.createPedestrianPaths();
    const colors = [0x2563eb, 0xdc2626, 0x16a34a, 0xca8a04, 0x7c3aed, 0x0891b2, 0x4b5563, 0xea580c];
    const count = 55;
    for (let i = 0; i < count; i++) {
      const path = this.pedestrianPaths[i % this.pedestrianPaths.length];
      const group = this.createOnePedestrian(colors[i % colors.length]);
      group.position.copy(path[0]);
      this.scene.add(group);
      this.pedestrians.push({
        group,
        path,
        t: (i / count) * (path.length - 1),
        speed: 0.08 + (i % 5) * 0.02,
        walkPhase: i * 0.5,
      });
    }
  }

  private updatePedestrians(delta: number): void {
    for (const p of this.pedestrians) {
      const len = p.path.length - 1;
      if (len <= 0) continue;
      p.t += p.speed * delta * 0.5;
      if (p.t >= len) p.t -= len;
      if (p.t < 0) p.t += len;
      const i0 = Math.floor(p.t) % p.path.length;
      const i1 = (i0 + 1) % p.path.length;
      const a = p.t - Math.floor(p.t);
      p.group.position.lerpVectors(p.path[i0], p.path[i1], a);
      p.group.lookAt(p.path[i1].x, p.group.position.y, p.path[i1].z);
      p.walkPhase += delta * 8;
      const bob = Math.sin(p.walkPhase) * 0.02;
      p.group.position.y = 0.5 + bob;
    }
  }

  private resize(): void {
    const canvas = this.renderer.domElement;
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    if (width === 0 || height === 0) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  updateState(state: Readonly<CityState>, day: number): void {
    const timeOfDay = (day % 24) / 24;
    const sunAngle = timeOfDay * Math.PI * 2 - Math.PI / 2;
    const sunX = Math.cos(sunAngle) * 150;
    const sunZ = Math.sin(sunAngle) * 150;
    this.sunLight.position.set(sunX, 80, sunZ);
    const isNight = timeOfDay < 0.25 || timeOfDay > 0.75;
    const sunIntensity = isNight ? 0.15 : 0.95;
    const sunColor = isNight ? 0x6688aa : 0xfff5e6;
    this.sunLight.intensity = sunIntensity;
    this.sunLight.color.setHex(sunColor);
    this.ambientLight.intensity = isNight ? 0.2 : 0.35;

    const economyFactor = state.economy / 100;
    this.buildingLights.forEach((light, i) => {
      const threshold = 0.2 + (i / this.buildingLights.length) * 0.7;
      const on = isNight && economyFactor >= threshold;
      light.visible = on;
      light.intensity = on ? 0.4 + economyFactor * 0.4 : 0;
    });

    const pollutionNorm = state.pollution / 100;
    const fogNear = 60 + pollutionNorm * 80;
    const fogFar = 250 + pollutionNorm * 150;
    const fogColor = new THREE.Color();
    fogColor.setHSL(0.55, 0.1, 0.4 + pollutionNorm * 0.25);
    this.scene.fog = new THREE.Fog(fogColor, fogNear, fogFar);
  }

  startRenderLoop(getState: () => { state: Readonly<CityState>; day: number }): void {
    const tick = () => {
      this.animationId = requestAnimationFrame(tick);
      const delta = this.clock.getDelta();
      this.updatePedestrians(delta);
      const { state, day } = getState();
      this.updateState(state, day);
      this.controls.update();
      this.renderer.render(this.scene, this.camera);
    };
    tick();
  }

  dispose(): void {
    cancelAnimationFrame(this.animationId);
    window.removeEventListener("resize", () => this.resize());
    this.controls.dispose();
    this.renderer.dispose();
    this.envMap?.dispose();
  }
}
