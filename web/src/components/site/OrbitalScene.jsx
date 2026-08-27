import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function OrbitalScene() {
  const mountRef = useRef(null)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return undefined

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 100)
    camera.position.set(0, 0.15, 7.2)

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.setClearColor(0x000000, 0)
    mount.appendChild(renderer.domElement)

    const ambientLight = new THREE.AmbientLight(0x9fffe0, 1.25)
    const keyLight = new THREE.PointLight(0x6df6c1, 18, 12)
    keyLight.position.set(2.6, 2.4, 4.5)
    const fillLight = new THREE.PointLight(0x6c8cff, 14, 10)
    fillLight.position.set(-3.5, -1.5, 2)
    scene.add(ambientLight, keyLight, fillLight)

    const system = new THREE.Group()
    scene.add(system)

    const coreMaterial = new THREE.MeshStandardMaterial({
      color: 0x4fe0ac,
      emissive: 0x0b725d,
      emissiveIntensity: 1.5,
      metalness: 0.4,
      roughness: 0.25,
      transparent: true,
      opacity: 0.82,
    })
    const core = new THREE.Mesh(new THREE.IcosahedronGeometry(1.18, 2), coreMaterial)
    system.add(core)

    const wireMaterial = new THREE.MeshBasicMaterial({
      color: 0xb5ffe7,
      transparent: true,
      opacity: 0.38,
      wireframe: true,
    })
    const wire = new THREE.Mesh(new THREE.IcosahedronGeometry(1.28, 2), wireMaterial)
    system.add(wire)

    const ringColors = [0x76f7c6, 0x7b94ff, 0xd28cff]
    const rings = ringColors.map((color, index) => {
      const ring = new THREE.Mesh(
        new THREE.TorusGeometry(1.72 + index * 0.22, 0.008, 8, 160),
        new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.58 - index * 0.1 }),
      )
      ring.rotation.set(0.7 + index * 0.36, 0.25 + index * 0.28, index * 0.8)
      system.add(ring)
      return ring
    })

    const particlePositions = new Float32Array(1100 * 3)
    for (let index = 0; index < particlePositions.length; index += 3) {
      const radius = 2.45 + Math.random() * 2.25
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      particlePositions[index] = radius * Math.sin(phi) * Math.cos(theta)
      particlePositions[index + 1] = radius * Math.cos(phi)
      particlePositions[index + 2] = radius * Math.sin(phi) * Math.sin(theta)
    }
    const particlesGeometry = new THREE.BufferGeometry()
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(particlePositions, 3))
    const particles = new THREE.Points(
      particlesGeometry,
      new THREE.PointsMaterial({ color: 0x9ffff0, size: 0.018, transparent: true, opacity: 0.62 }),
    )
    scene.add(particles)

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const pointer = { x: 0, y: 0 }
    const target = { x: 0, y: 0 }
    const onPointerMove = (event) => {
      const bounds = mount.getBoundingClientRect()
      pointer.x = ((event.clientX - bounds.left) / bounds.width - 0.5) * 2
      pointer.y = ((event.clientY - bounds.top) / bounds.height - 0.5) * 2
    }
    const onPointerLeave = () => {
      pointer.x = 0
      pointer.y = 0
    }
    mount.addEventListener('pointermove', onPointerMove)
    mount.addEventListener('pointerleave', onPointerLeave)

    const resize = () => {
      const { width, height } = mount.getBoundingClientRect()
      camera.aspect = width / Math.max(height, 1)
      camera.updateProjectionMatrix()
      renderer.setSize(width, height, false)
    }
    const resizeObserver = new ResizeObserver(resize)
    resizeObserver.observe(mount)
    resize()

    let frameId
    const animate = (time = 0) => {
      target.x += (pointer.x - target.x) * 0.035
      target.y += (pointer.y - target.y) * 0.035
      system.rotation.y = time * 0.00022 + target.x * 0.12
      system.rotation.x = target.y * -0.08
      particles.rotation.y = time * 0.00008
      rings.forEach((ring, index) => {
        ring.rotation.z += 0.00035 * (index % 2 === 0 ? 1 : -1)
      })
      renderer.render(scene, camera)
      if (!reducedMotion) frameId = requestAnimationFrame(animate)
    }
    animate()

    return () => {
      cancelAnimationFrame(frameId)
      resizeObserver.disconnect()
      mount.removeEventListener('pointermove', onPointerMove)
      mount.removeEventListener('pointerleave', onPointerLeave)
      core.geometry.dispose()
      coreMaterial.dispose()
      wire.geometry.dispose()
      wireMaterial.dispose()
      rings.forEach((ring) => {
        ring.geometry.dispose()
        ring.material.dispose()
      })
      particlesGeometry.dispose()
      particles.material.dispose()
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [])

  return <div ref={mountRef} className="absolute inset-0 h-full w-full [&_canvas]:block [&_canvas]:h-full [&_canvas]:w-full" aria-hidden="true" />
}
