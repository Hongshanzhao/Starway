<template>
  <canvas ref="canvas" class="three-canvas" aria-hidden="true"></canvas>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as THREE from 'three'

const canvas = ref(null)
let renderer
let scene
let camera
let frame
let group
let pointer = { x: 0, y: 0 }

function resize() {
  if (!renderer || !camera) return
  const width = canvas.value.clientWidth || window.innerWidth
  const height = canvas.value.clientHeight || window.innerHeight
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.updateProjectionMatrix()
}

function animate() {
  frame = requestAnimationFrame(animate)
  group.rotation.y += 0.0025
  group.rotation.x += 0.001
  group.position.x += (pointer.x * 0.35 - group.position.x) * 0.02
  group.position.y += (-pointer.y * 0.22 - group.position.y) * 0.02
  renderer.render(scene, camera)
}

onMounted(() => {
  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(55, 1, 0.1, 100)
  camera.position.z = 8
  renderer = new THREE.WebGLRenderer({ canvas: canvas.value, alpha: true, antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  group = new THREE.Group()
  scene.add(group)

  const palette = [0x78a083, 0xa5b5b2, 0xdceadf, 0xc9b1b0]
  const geometries = [
    new THREE.IcosahedronGeometry(0.72, 0),
    new THREE.OctahedronGeometry(0.56, 0),
    new THREE.TetrahedronGeometry(0.62, 0),
  ]
  for (let i = 0; i < 18; i += 1) {
    const material = new THREE.MeshStandardMaterial({
      color: palette[i % palette.length],
      roughness: 0.65,
      metalness: 0.05,
      transparent: true,
      opacity: 0.46,
    })
    const mesh = new THREE.Mesh(geometries[i % geometries.length], material)
    const x = Math.random() * 7.9 - 0.8
    const y = (Math.random() - 0.5) * 5.5
    mesh.position.set(x, y, (Math.random() - 0.5) * 3)
    mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, 0)
    group.add(mesh)
  }

  const particles = new THREE.Points(
    new THREE.BufferGeometry().setAttribute(
      'position',
      new THREE.Float32BufferAttribute(Array.from({ length: 240 }, () => (Math.random() - 0.5) * 10), 3),
    ),
    new THREE.PointsMaterial({ color: 0x78a083, size: 0.026, transparent: true, opacity: 0.42 }),
  )
  group.add(particles)

  scene.add(new THREE.AmbientLight(0xffffff, 1.8))
  const light = new THREE.DirectionalLight(0xffffff, 1.8)
  light.position.set(3, 4, 5)
  scene.add(light)

  resize()
  animate()
  window.addEventListener('resize', resize)
  window.addEventListener('pointermove', (event) => {
    pointer = { x: event.clientX / window.innerWidth - 0.5, y: event.clientY / window.innerHeight - 0.5 }
  })
})

onBeforeUnmount(() => {
  cancelAnimationFrame(frame)
  window.removeEventListener('resize', resize)
  renderer?.dispose()
})
</script>

<style scoped>
.three-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
</style>
