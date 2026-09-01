"use client";

import { useEffect, useRef } from "react";

const PARTICLES_PER_SIDE = 120;
const POINT_SPACING = 2.5;
const PARTICLE_COUNT = PARTICLES_PER_SIDE * PARTICLES_PER_SIDE;

function getWaveY(x: number, z: number, time: number) {
  return (
    Math.sin(x * 0.1 + time * 1.35) * 5 -
    Math.cos(z * 0.1 + time * 1.35) * 5 -
    25
  );
}

export default function ParticleWave() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let disposed = false;
    let disposeScene = () => undefined;

    const initialize = async () => {
      try {
        const container = containerRef.current;
        if (!container || disposed) return;

        const THREE = await import("three");
        if (disposed) return;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(
          75,
          container.clientWidth / container.clientHeight,
          0.1,
          1000
        );
        camera.position.set(0, 15, 100);
        camera.lookAt(0, -36, 0);

        let renderer: import("three").WebGLRenderer;
        try {
          renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        } catch {
          // WebGL is optional decoration; never let it prevent the page from rendering.
          return;
        }

        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setClearColor(0xffffff, 0);
        container.appendChild(renderer.domElement);

        const geometry = new THREE.BufferGeometry();
        const positions = new Float32Array(PARTICLE_COUNT * 3);
        const coordinates = new Float32Array(PARTICLE_COUNT * 2);

        for (let index = 0; index < PARTICLE_COUNT; index += 1) {
          const x =
            (index % PARTICLES_PER_SIDE - PARTICLES_PER_SIDE / 2) * POINT_SPACING;
          const z =
            (Math.floor(index / PARTICLES_PER_SIDE) - PARTICLES_PER_SIDE / 2) *
            POINT_SPACING;

          positions[index * 3] = x;
          positions[index * 3 + 1] = getWaveY(x, z, 0);
          positions[index * 3 + 2] = z;
          coordinates[index * 2] = x;
          coordinates[index * 2 + 1] = z;
        }

        const positionAttribute = new THREE.BufferAttribute(positions, 3);
        geometry.setAttribute("position", positionAttribute);

        const material = new THREE.PointsMaterial({
          color: 0x6d4ae2,
          size: 0.7,
          transparent: true,
          opacity: 0.6,
          depthWrite: false,
        });
        const particles = new THREE.Points(geometry, material);
        particles.position.set(0, -95, -85);
        particles.scale.x = 1.2;
        scene.add(particles);

        const reducedMotion = window.matchMedia(
          "(prefers-reduced-motion: reduce)"
        ).matches;
        let animationFrame: number | undefined;

        const render = () => {
          if (!disposed) renderer.render(scene, camera);
        };

        const animate = (now: number) => {
          const time = now / 1000;
          const pointPositions = positionAttribute.array as Float32Array;

          for (let index = 0; index < PARTICLE_COUNT; index += 1) {
            pointPositions[index * 3 + 1] = getWaveY(
              coordinates[index * 2],
              coordinates[index * 2 + 1],
              time
            );
          }

          positionAttribute.needsUpdate = true;
          render();
          animationFrame = requestAnimationFrame(animate);
        };

        if (reducedMotion) render();
        else animationFrame = requestAnimationFrame(animate);

        const resize = () => {
          const { clientWidth, clientHeight } = container;
          if (!clientWidth || !clientHeight || disposed) return;
          camera.aspect = clientWidth / clientHeight;
          camera.updateProjectionMatrix();
          renderer.setSize(clientWidth, clientHeight);
          render();
        };

        const resizeObserver =
          typeof ResizeObserver === "undefined"
            ? undefined
            : new ResizeObserver(resize);
        resizeObserver?.observe(container);
        if (!resizeObserver) window.addEventListener("resize", resize);

        disposeScene = () => {
          resizeObserver?.disconnect();
          if (!resizeObserver) window.removeEventListener("resize", resize);
          if (animationFrame !== undefined) cancelAnimationFrame(animationFrame);
          scene.remove(particles);
          geometry.dispose();
          material.dispose();
          renderer.dispose();
          renderer.domElement.remove();
        };
      } catch {
        // Loading the optional decorative layer must not affect the application.
      }
    };

    void initialize();

    return () => {
      disposed = true;
      disposeScene();
    };
  }, []);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      style={{
        maskImage: "linear-gradient(to bottom, transparent 0%, transparent 34%, rgba(0, 0, 0, 0.18) 45%, black 60%)",
        WebkitMaskImage: "linear-gradient(to bottom, transparent 0%, transparent 34%, rgba(0, 0, 0, 0.18) 45%, black 60%)",
      }}
      className="pointer-events-none absolute inset-0 z-0 overflow-hidden"
    />
  );
}
