import { useEffect, useRef } from 'react'
import * as THREE from 'three'

function makeEnvMap() {
  const size = 128
  const canvas = document.createElement('canvas')
  canvas.width = size
  canvas.height = size
  const ctx = canvas.getContext('2d')
  const gradient = ctx.createLinearGradient(0, 0, 0, size)
  gradient.addColorStop(0, '#f4f6f8')
  gradient.addColorStop(0.22, '#c5ced8')
  gradient.addColorStop(0.5, '#6f7b88')
  gradient.addColorStop(0.78, '#2a3038')
  gradient.addColorStop(1, '#0d0f12')
  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, size, size)
  ctx.strokeStyle = 'rgba(255,255,255,0.35)'
  ctx.lineWidth = 6
  ctx.beginPath()
  ctx.moveTo(0, size * 0.18)
  ctx.lineTo(size, size * 0.32)
  ctx.stroke()
  const texture = new THREE.CanvasTexture(canvas)
  texture.mapping = THREE.EquirectangularReflectionMapping
  texture.colorSpace = THREE.SRGBColorSpace
  return texture
}

export default function OrbitalScene() {
  const mountRef = useRef(null)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return undefined

    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(36, 1, 0.1, 100)
    camera.position.set(0, 0.35, 7.4)

    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.outputColorSpace = THREE.SRGBColorSpace
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.08
    renderer.setClearColor(0x000000, 0)
    mount.appendChild(renderer.domElement)

    const envMap = makeEnvMap()
    scene.environment = envMap

    const ambientLight = new THREE.AmbientLight(0xb8c2cc, 0.55)
    const keyLight = new THREE.SpotLight(0xf2f5f8, 38, 20, Math.PI / 5, 0.45, 1.1)
    keyLight.position.set(3.4, 4.6, 5.2)
    const rimLight = new THREE.PointLight(0x9eb0c4, 26, 16)
    rimLight.position.set(-4.2, 1.4, -2.4)
    const fillLight = new THREE.PointLight(0xd7cbb6, 9, 12)
    fillLight.position.set(0.4, -3.2, 3.2)
    scene.add(ambientLight, keyLight, rimLight, fillLight)

    const system = new THREE.Group()
    scene.add(system)

    const glassMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xd5dce4,
      metalness: 0.88,
      roughness: 0.1,
      clearcoat: 1,
      clearcoatRoughness: 0.06,
      transmission: 0.28,
      thickness: 1.35,
      ior: 1.48,
      iridescence: 0.28,
      iridescenceIOR: 1.25,
      envMapIntensity: 1.35,
      transparent: true,
    })
    const lens = new THREE.Mesh(new THREE.SphereGeometry(1.22, 64, 64), glassMaterial)
    system.add(lens)

    const coreMaterial = new THREE.MeshStandardMaterial({
      color: 0x12161c,
      metalness: 0.85,
      roughness: 0.28,
      envMapIntensity: 0.8,
    })
    const core = new THREE.Mesh(new THREE.SphereGeometry(0.7, 48, 48), coreMaterial)
    system.add(core)

    const bezelMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xcfd6de,
      metalness: 1,
      roughness: 0.16,
      clearcoat: 0.7,
      envMapIntensity: 1.4,
    })
    const bezel = new THREE.Mesh(new THREE.TorusGeometry(1.42, 0.045, 16, 140), bezelMaterial)
    bezel.rotation.x = Math.PI / 2.15
    system.add(bezel)

    const ringMaterial = new THREE.MeshPhysicalMaterial({
      color: 0xb9c3ce,
      metalness: 1,
      roughness: 0.22,
      transparent: true,
      opacity: 0.78,
      envMapIntensity: 1.1,
    })
    const outerRing = new THREE.Mesh(new THREE.TorusGeometry(2.02, 0.012, 12, 180), ringMaterial)
    outerRing.rotation.x = Math.PI / 2
    system.add(outerRing)

    const tickGroup = new THREE.Group()
    const tickMaterial = new THREE.MeshBasicMaterial({ color: 0xe4eaef, transparent: true, opacity: 0.42 })
    for (let index = 0; index < 24; index += 1) {
      const tick = new THREE.Mesh(new THREE.BoxGeometry(index % 6 === 0 ? 0.08 : 0.04, 0.012, 0.012), tickMaterial)
      const angle = (index / 24) * Math.PI * 2
      tick.position.set(Math.cos(angle) * 1.86, 0, Math.sin(angle) * 1.86)
      tick.lookAt(0, 0, 0)
      tickGroup.add(tick)
    }
    tickGroup.rotation.x = Math.PI / 2
    system.add(tickGroup)

    const sweepGeometry = new THREE.CircleGeometry(1.95, 56, 0, Math.PI * 0.22)
    sweepGeometry.rotateX(-Math.PI / 2)
    const sweepMaterial = new THREE.MeshBasicMaterial({
      color: 0xd7dee6,
      transparent: true,
      opacity: 0.16,
      side: THREE.DoubleSide,
      depthWrite: false,
    })
    const sweep = new THREE.Mesh(sweepGeometry, sweepMaterial)
    sweep.position.y = 0.02
    system.add(sweep)

    const blipMaterial = new THREE.MeshBasicMaterial({ color: 0xf3f6f8, transparent: true, opacity: 0.9 })
    const blips = [0.55, 1.35, 2.2].map((phase, index) => {
      const blip = new THREE.Mesh(new THREE.SphereGeometry(0.035 + index * 0.008, 12, 12), blipMaterial)
      system.add(blip)
      return { mesh: blip, phase, radius: 0.95 + index * 0.28 }
    })

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
      target.x += (pointer.x - target.x) * 0.04
      target.y += (pointer.y - target.y) * 0.04
      system.rotation.y = time * 0.00012 + target.x * 0.16
      system.rotation.x = 0.18 + target.y * -0.1
      sweep.rotation.y = time * 0.00115
      lens.rotation.y = time * -0.00008
      blips.forEach((blip) => {
        const angle = time * 0.0009 + blip.phase
        blip.mesh.position.set(Math.cos(angle) * blip.radius, 0.05, Math.sin(angle) * blip.radius)
        blip.mesh.material.opacity = 0.45 + Math.sin(time * 0.004 + blip.phase) * 0.4
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
      lens.geometry.dispose()
      glassMaterial.dispose()
      core.geometry.dispose()
      coreMaterial.dispose()
      bezel.geometry.dispose()
      bezelMaterial.dispose()
      outerRing.geometry.dispose()
      ringMaterial.dispose()
      tickGroup.children.forEach((tick) => tick.geometry.dispose())
      tickMaterial.dispose()
      sweepGeometry.dispose()
      sweepMaterial.dispose()
      blips.forEach((blip) => blip.mesh.geometry.dispose())
      blipMaterial.dispose()
      envMap.dispose()
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [])

  return (
    <div
      ref={mountRef}
      className="absolute inset-0 h-full w-full [&_canvas]:block [&_canvas]:h-full [&_canvas]:w-full"
      aria-hidden="true"
    />
  )
}
