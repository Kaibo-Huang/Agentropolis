/**
 * Three.js 3D Toronto city scene driven by simulation state.
 * Lake Ontario to the south, CN Tower, downtown grid. Day/night, pollution fog, economy lights.
 */
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { CityState } from "../types/city-state.js";

const LAKE_COLOR = 0x1a4d6b;
const GROUND_COLOR = 0x2d3a2e;
const CN_TOWER_COLOR = 0x4a5568;
const BUILDING_COLORS = [0x5c6b73, 0x4a5568, 0x3d4f5c, 0x6b7b7c, 0x5a6570];

export interface TorontoSceneOptions {
  canvas: HTMLCanvasElement;
  onResize?: () => void;
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

  constructor(options: TorontoSceneOptions) {
    const { canvas } = options;
    this.scene = new THREE.Scene();
    this.fog = new THREE.Fog(0x87ceeb, 80, 350);
    this.scene.fog = this.fog;

    this.camera = new THREE.PerspectiveCamera(50, 1, 0.1, 2000);
    this.camera.position.set(120, 80, 120);
    this.camera.lookAt(0, 20, 0);

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setClearColor(0x0d1117);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.minDistance = 40;
    this.controls.maxDistance = 400;
    this.controls.maxPolarAngle = Math.PI / 2 - 0.1;
    this.controls.target.set(0, 15, 0);

    this.ambientLight = new THREE.AmbientLight(0x404060, 0.4);
    this.scene.add(this.ambientLight);

    this.sunLight = new THREE.DirectionalLight(0xfff5e6, 0.9);
    this.sunLight.position.set(80, 120, 60);
    this.sunLight.castShadow = true;
    this.sunLight.shadow.mapSize.set(1024, 1024);
    this.sunLight.shadow.camera.near = 0.5;
    this.sunLight.shadow.camera.far = 400;
    this.sunLight.shadow.camera.left = -120;
    this.sunLight.shadow.camera.right = 120;
    this.sunLight.shadow.camera.top = 120;
    this.sunLight.shadow.camera.bottom = -120;
    this.scene.add(this.sunLight);

    this.lake = this.createLake();
    this.scene.add(this.lake);

    this.createGround();
    this.cnTower = this.createCNTower();
    this.scene.add(this.cnTower);
    this.createDowntownBuildings();

    this.resize();
    window.addEventListener("resize", () => this.resize());
  }

  private createLake(): THREE.Mesh {
    const geometry = new THREE.PlaneGeometry(400, 200);
    const material = new THREE.MeshStandardMaterial({
      color: LAKE_COLOR,
      metalness: 0.3,
      roughness: 0.8,
      flatShading: true,
    });
    const mesh = new THREE.Mesh(geometry, material);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.set(0, 0, -180);
    mesh.receiveShadow = true;
    return mesh;
  }

  private createGround(): void {
    const geometry = new THREE.PlaneGeometry(500, 500);
    const material = new THREE.MeshStandardMaterial({
      color: GROUND_COLOR,
      roughness: 0.95,
      metalness: 0,
    });
    const ground = new THREE.Mesh(geometry, material);
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = 0;
    ground.receiveShadow = true;
    this.scene.add(ground);
  }

  private createCNTower(): THREE.Group {
    const group = new THREE.Group();

    const podGeo = new THREE.SphereGeometry(8, 24, 24, 0, Math.PI * 2, 0, Math.PI / 2);
    const podMat = new THREE.MeshStandardMaterial({
      color: 0x6b7280,
      metalness: 0.6,
      roughness: 0.4,
    });
    const pod = new THREE.Mesh(podGeo, podMat);
    pod.position.y = 52;
    pod.castShadow = true;
    pod.receiveShadow = true;
    group.add(pod);

    const shaftGeo = new THREE.CylinderGeometry(3, 6, 50, 16);
    const shaftMat = new THREE.MeshStandardMaterial({
      color: CN_TOWER_COLOR,
      metalness: 0.5,
      roughness: 0.5,
    });
    const shaft = new THREE.Mesh(shaftGeo, shaftMat);
    shaft.position.y = 25;
    shaft.castShadow = true;
    group.add(shaft);

    const legGeo = new THREE.CylinderGeometry(0.5, 1.5, 30, 6);
    const legMat = new THREE.MeshStandardMaterial({
      color: 0x374151,
      metalness: 0.6,
      roughness: 0.4,
    });
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
    const antennaMat = new THREE.MeshStandardMaterial({
      color: 0x1f2937,
      metalness: 0.8,
      roughness: 0.3,
    });
    const antenna = new THREE.Mesh(antennaGeo, antennaMat);
    antenna.position.y = 103;
    antenna.castShadow = true;
    group.add(antenna);

    group.position.set(0, 0, 0);
    return group;
  }

  private createDowntownBuildings(): void {
    const grid = [
      [40, 25], [35, 45], [30, 20], [25, 55], [20, 30], [15, 40], [10, 22],
      [38, 18], [32, 38], [28, 50], [22, 28], [18, 42], [12, 25], [8, 35],
      [42, 32], [36, 28], [26, 35], [24, 48], [14, 38], [6, 28],
    ];
    const spacing = 22;
    const baseX = -spacing * 1.5;
    const baseZ = -spacing * 1.5;

    for (let i = 0; i < grid.length; i++) {
      const [w, h] = grid[i];
      const color = BUILDING_COLORS[i % BUILDING_COLORS.length];
      const geometry = new THREE.BoxGeometry(w * 0.4, h, w * 0.4);
      const material = new THREE.MeshStandardMaterial({
        color,
        metalness: 0.2,
        roughness: 0.7,
      });
      const building = new THREE.Mesh(geometry, material);
      const col = Math.floor(i / 7);
      const row = i % 7;
      building.position.x = baseX + row * spacing + (Math.random() - 0.5) * 4;
      building.position.z = baseZ + col * spacing + (Math.random() - 0.5) * 4;
      building.position.y = h / 2;
      building.castShadow = true;
      building.receiveShadow = true;
      this.scene.add(building);
      this.buildings.push(building);

      const light = new THREE.PointLight(0xffeedd, 0.4, 15);
      light.position.copy(building.position);
      light.position.y += h * 0.3 + Math.random() * 4;
      light.position.x += (Math.random() - 0.5) * 3;
      light.position.z += (Math.random() - 0.5) * 3;
      this.scene.add(light);
      this.buildingLights.push(light);
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

  /** Drive visuals from simulation state and day. */
  updateState(state: Readonly<CityState>, day: number): void {
    const timeOfDay = (day % 24) / 24;
    const sunAngle = timeOfDay * Math.PI * 2 - Math.PI / 2;
    const sunX = Math.cos(sunAngle) * 150;
    const sunZ = Math.sin(sunAngle) * 150;
    this.sunLight.position.set(sunX, 80, sunZ);
    const isNight = timeOfDay < 0.25 || timeOfDay > 0.75;
    const sunIntensity = isNight ? 0.15 : 0.9;
    const sunColor = isNight ? 0x6688aa : 0xfff5e6;
    this.sunLight.intensity = sunIntensity;
    this.sunLight.color.setHex(sunColor);
    this.ambientLight.intensity = isNight ? 0.2 : 0.4;

    const economyFactor = state.economy / 100;
    this.buildingLights.forEach((light, i) => {
      const threshold = 0.2 + (i / this.buildingLights.length) * 0.7;
      const on = isNight && economyFactor >= threshold;
      light.visible = on;
      light.intensity = on ? 0.3 + economyFactor * 0.3 : 0;
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
  }
}
