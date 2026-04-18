"use client"

import { useRef, useMemo } from "react"
import { Canvas, useFrame, useThree } from "@react-three/fiber"
import * as THREE from "three"

function Particles() {
  const meshRef = useRef<THREE.Points>(null)
  const mouseRef = useRef({ x: 0, y: 0 })
  const { viewport } = useThree()

  const count = 1500
  const { positions, velocities, basePositions } = useMemo(() => {
    const positions = new Float32Array(count * 3)
    const velocities = new Float32Array(count * 3)
    const basePositions = new Float32Array(count * 3)

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const r = 2.5 + Math.random() * 2

      const x = r * Math.sin(phi) * Math.cos(theta)
      const y = r * Math.sin(phi) * Math.sin(theta)
      const z = r * Math.cos(phi) - 2

      positions[i * 3] = x
      positions[i * 3 + 1] = y
      positions[i * 3 + 2] = z

      basePositions[i * 3] = x
      basePositions[i * 3 + 1] = y
      basePositions[i * 3 + 2] = z

      velocities[i * 3] = (Math.random() - 0.5) * 0.002
      velocities[i * 3 + 1] = (Math.random() - 0.5) * 0.002
      velocities[i * 3 + 2] = (Math.random() - 0.5) * 0.002
    }
    return { positions, velocities, basePositions }
  }, [])

  const sizes = useMemo(() => {
    const s = new Float32Array(count)
    for (let i = 0; i < count; i++) {
      s[i] = Math.random() * 2.5 + 0.5
    }
    return s
  }, [])

  useFrame(({ clock, pointer }) => {
    if (!meshRef.current) return
    const time = clock.getElapsedTime()

    mouseRef.current.x += (pointer.x * viewport.width * 0.3 - mouseRef.current.x) * 0.02
    mouseRef.current.y += (pointer.y * viewport.height * 0.3 - mouseRef.current.y) * 0.02

    const posArray = meshRef.current.geometry.attributes.position.array as Float32Array

    for (let i = 0; i < count; i++) {
      const i3 = i * 3

      posArray[i3] = basePositions[i3] +
        Math.sin(time * 0.3 + i * 0.01) * 0.15 +
        mouseRef.current.x * 0.08
      posArray[i3 + 1] = basePositions[i3 + 1] +
        Math.cos(time * 0.2 + i * 0.015) * 0.15 +
        mouseRef.current.y * 0.08
      posArray[i3 + 2] = basePositions[i3 + 2] +
        Math.sin(time * 0.25 + i * 0.012) * 0.1
    }

    meshRef.current.geometry.attributes.position.needsUpdate = true
    meshRef.current.rotation.y = time * 0.02
  })

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={count}
        />
        <bufferAttribute
          attach="attributes-size"
          args={[sizes, 1]}
          count={count}
        />
      </bufferGeometry>
      <pointsMaterial
        color="#00C48C"
        size={0.025}
        sizeAttenuation
        transparent
        opacity={0.6}
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  )
}

function MorphingMesh() {
  const meshRef = useRef<THREE.Mesh>(null)
  const materialRef = useRef<THREE.MeshStandardMaterial>(null)

  useFrame(({ clock, pointer }) => {
    if (!meshRef.current) return
    const time = clock.getElapsedTime()

    meshRef.current.rotation.x = time * 0.05 + pointer.y * 0.1
    meshRef.current.rotation.y = time * 0.08 + pointer.x * 0.1

    const geo = meshRef.current.geometry as THREE.IcosahedronGeometry
    const pos = geo.attributes.position
    const baseGeo = new THREE.IcosahedronGeometry(1.8, 4)
    const basePos = baseGeo.attributes.position

    for (let i = 0; i < pos.count; i++) {
      const bx = basePos.getX(i)
      const by = basePos.getY(i)
      const bz = basePos.getZ(i)

      const noise =
        Math.sin(bx * 2 + time * 0.5) *
        Math.cos(by * 2 + time * 0.3) *
        Math.sin(bz * 2 + time * 0.4) * 0.15

      pos.setXYZ(i, bx + bx * noise, by + by * noise, bz + bz * noise)
    }
    pos.needsUpdate = true
    geo.computeVertexNormals()
    baseGeo.dispose()
  })

  return (
    <mesh ref={meshRef} position={[0, 0, -2]}>
      <icosahedronGeometry args={[1.8, 4]} />
      <meshStandardMaterial
        ref={materialRef}
        color="#0a0a0a"
        wireframe
        transparent
        opacity={0.15}
        emissive="#00C48C"
        emissiveIntensity={0.05}
      />
    </mesh>
  )
}

export function HeroScene() {
  return (
    <div className="absolute inset-0 z-0">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 60 }}
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <ambientLight intensity={0.3} />
        <pointLight position={[5, 5, 5]} intensity={0.5} color="#00C48C" />
        <MorphingMesh />
        <Particles />
      </Canvas>
    </div>
  )
}
