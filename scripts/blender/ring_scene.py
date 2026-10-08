"""Photoreal gold solitaire for the Marlyn Jewelry scroll showcase (Blender 5, Cycles path tracing).

Usage (see scripts/blender/README.md):
  blender -b -P ring_scene.py -- --preview 0.42 --out preview.png          # one quick still at progress p
  blender -b -P ring_scene.py -- --frames 144 --out-dir frames/            # full turntable sequence

Units: 1 unit = 1 cm. The ring stands on a white studio floor (shadow catcher, so the PNG keeps only the soft
contact shadow), finger hole along Y, stone on +Z, camera looking along +Y.
Why it reads as a photograph: tapered comfort-fit band, 57-facet brilliant (correct pavilion angle so it stays white), graduated pavé with beads, polished gold tuned to
measured values from a commercial reference, bright studio dome + black flags for crisp reflection edges, macro depth of field.
"""
import argparse
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

# ---------------------------------------------------------------- args
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--preview", type=float, default=None, help="render one still at scroll progress 0..1")
ap.add_argument("--out", default="preview.png")
ap.add_argument("--frames", type=int, default=144)
ap.add_argument("--out-dir", default="frames")
ap.add_argument("--size", type=int, default=1280)
ap.add_argument("--samples", type=int, default=None)
ap.add_argument("--start", type=int, default=0, help="first frame index to render (resume)")
ap.add_argument("--exposure", type=float, default=-0.55)
ap.add_argument("--world", type=float, default=1.0, help="studio ambient brightness")
args = ap.parse_args(argv)

# ---------------------------------------------------------------- helpers
def clamp01(v): return max(0.0, min(1.0, v))
def smooth(a, b, v):
    t = clamp01((v - a) / (b - a)); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def sgnpow(x, e): return math.copysign(abs(x) ** e, x)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

def new_obj(name, mesh):
    o = bpy.data.objects.new(name, mesh); scene.collection.objects.link(o); return o

def shade_smooth(o):
    for p in o.data.polygons: p.use_smooth = True

def link(nt, a, b): nt.links.new(a, b)

# ---------------------------------------------------------------- materials
def gold_material():
    m = bpy.data.materials.new("Gold"); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (1.0, 0.70, 0.29, 1)
    b.inputs["Metallic"].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    fine = nt.nodes.new("ShaderNodeTexNoise")            # micro-scratches: the thing CG gold usually lacks
    fine.inputs["Scale"].default_value = 420; fine.inputs["Detail"].default_value = 9; fine.inputs["Roughness"].default_value = 0.65
    bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.008; bump.inputs["Distance"].default_value = 0.002
    broad = nt.nodes.new("ShaderNodeTexNoise")           # slight polish variation across the surface
    broad.inputs["Scale"].default_value = 18; broad.inputs["Detail"].default_value = 3
    rng = nt.nodes.new("ShaderNodeMapRange")
    rng.inputs["To Min"].default_value = 0.022; rng.inputs["To Max"].default_value = 0.040
    link(nt, tc.outputs["Object"], fine.inputs["Vector"]); link(nt, fine.outputs["Fac"], bump.inputs["Height"])
    link(nt, bump.outputs["Normal"], b.inputs["Normal"])
    link(nt, tc.outputs["Object"], broad.inputs["Vector"]); link(nt, broad.outputs["Fac"], rng.inputs["Value"])
    link(nt, rng.outputs["Result"], b.inputs["Roughness"])
    return m

def diamond_material(emission=0.0, tint=(0.955, 0.98, 1.0)):
    m = bpy.data.materials.new("Diamond"); m.use_nodes = True
    t = m.node_tree; t.nodes.clear()
    out = t.nodes.new("ShaderNodeOutputMaterial")
    # Single physically-correct glass. (A per-channel "fake dispersion" trio was tried and abandoned: the pure R/G/B
    # filters multiply to zero over repeated internal bounces, leaving the stone murky.)
    glass = t.nodes.new("ShaderNodeBsdfGlass")
    glass.inputs["IOR"].default_value = 2.417; glass.inputs["Roughness"].default_value = 0.0
    glass.inputs["Color"].default_value = (*tint, 1)   # D-colour bias; compounds per bounce, so keep it small
    clear = t.nodes.new("ShaderNodeBsdfTransparent")
    lp = t.nodes.new("ShaderNodeLightPath")
    shadow_mix = t.nodes.new("ShaderNodeMixShader")      # shadow rays pass through so light can reach the stone
    link(t, lp.outputs["Is Shadow Ray"], shadow_mix.inputs["Fac"])
    link(t, glass.outputs[0], shadow_mix.inputs[1]); link(t, clear.outputs[0], shadow_mix.inputs[2])
    last = shadow_mix
    if emission > 0:                                     # micro-pavé: a whisper of white so tiny stones still sparkle
        em = t.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1, 0.98, 0.95, 1); em.inputs["Strength"].default_value = 1.0
        mix = t.nodes.new("ShaderNodeMixShader"); mix.inputs["Fac"].default_value = emission
        link(t, shadow_mix.outputs[0], mix.inputs[1]); link(t, em.outputs[0], mix.inputs[2]); last = mix
    link(t, last.outputs[0], out.inputs["Surface"])
    return m

def flat_material(name, color, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    return m

GOLD = gold_material()
DIAMOND = diamond_material()
DIAMOND_PAVE = diamond_material(emission=0.05, tint=(0.84, 0.92, 1.0))   # tiny stones are mostly surrounded by gold, so they take more bias

# ---------------------------------------------------------------- band (tapered comfort-fit, superellipse section)
INNER = 0.83                                              # inner radius, cm (~size 7)
def thickness(phi): return lerp(0.27, 0.17, smooth(0, math.pi, abs(phi)) ** 0.65)
def width(phi):     return lerp(0.36, 0.24, smooth(0, math.pi, abs(phi)) ** 0.60)
def r_out(phi):     return INNER + thickness(phi)

def band_mesh():
    NP, NQ = 480, 96
    v, f = [], []
    for i in range(NP):
        phi = -math.pi + 2 * math.pi * i / NP             # 0 = top (12 o'clock)
        a = thickness(phi) / 2; b = width(phi) / 2; C = INNER + a
        rx, rz = math.sin(phi), math.cos(phi)
        for j in range(NQ):
            psi = 2 * math.pi * j / NQ; c, s = math.cos(psi), math.sin(psi)
            n = 3.2 if c >= 0 else 2.2                     # flatter outside, rounder comfort-fit inside
            r = C + a * sgnpow(c, 2 / n); y = b * sgnpow(s, 2 / n)
            v.append((rx * r, y, rz * r))
    for i in range(NP):
        for j in range(NQ):
            i2, j2 = (i + 1) % NP, (j + 1) % NQ
            f.append((i * NQ + j, i * NQ + j2, i2 * NQ + j2, i2 * NQ + j))
    me = bpy.data.meshes.new("BandMesh"); me.from_pydata(v, [], f); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return me

# ---------------------------------------------------------------- diamond (full 57-facet round brilliant)
def brilliant_mesh(name, R, table=0.57, crown_h=0.34, pav_d=0.88, girdle=0.025):
    ang = lambda k, n, off=0.0: (k / n) * 2 * math.pi + off
    v, f = [], []
    def add(x, y, z): v.append((x, y, z)); return len(v) - 1
    H, gz = crown_h * R, girdle * R
    T = [add(table * R * math.cos(ang(i, 8)), table * R * math.sin(ang(i, 8)), gz + H) for i in range(8)]
    S = [add(0.80 * R * math.cos(ang(i, 8, math.pi / 8)), 0.80 * R * math.sin(ang(i, 8, math.pi / 8)), gz + 0.33 * H) for i in range(8)]
    G = [add(R * math.cos(ang(j, 16)), R * math.sin(ang(j, 16)), gz) for j in range(16)]
    Gb = [add(R * math.cos(ang(j, 16)), R * math.sin(ang(j, 16)), 0.0) for j in range(16)]
    P = [add(0.24 * R * math.cos(ang(i, 8, math.pi / 8)), 0.24 * R * math.sin(ang(i, 8, math.pi / 8)), -0.76 * pav_d * R) for i in range(8)]
    C = add(0, 0, -pav_d * R)
    f.append([T[i] for i in reversed(range(8))])                           # table
    for i in range(8):
        f.append([T[i], T[(i + 1) % 8], S[i]][::-1])                       # 8 star
        f.append([T[i], S[i - 1], G[2 * i], S[i]][::-1])                   # 8 bezel
        f.append([S[i], G[2 * i], G[2 * i + 1]][::-1])                     # 16 upper girdle halves
        f.append([S[i], G[2 * i + 1], G[(2 * i + 2) % 16]][::-1])
        f.append([Gb[2 * i], Gb[2 * i + 1], P[i]])                         # 16 lower girdle halves
        f.append([Gb[2 * i + 1], Gb[(2 * i + 2) % 16], P[i]])
        f.append([Gb[2 * i], P[i - 1], C, P[i]])                           # 8 pavilion mains
    for j in range(16):
        f.append([G[j], G[(j + 1) % 16], Gb[(j + 1) % 16], Gb[j]][::-1])   # girdle band
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    return me

# ---------------------------------------------------------------- primitives
def cone_between(name, r1, r2, p0, p1, mat, verts=24):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=d.length, location=(p0 + p1) / 2)
    o = bpy.context.active_object; o.name = name
    o.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(mat); shade_smooth(o); return o

def sphere(name, r, loc, mat, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=seg, ring_count=seg // 2)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mat); shade_smooth(o); return o

def torus(name, major, minor, loc, mat, rot=(0, 0, 0), seg=96):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=seg, minor_segments=24, location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mat); shade_smooth(o); return o

ring = bpy.data.objects.new("RingRoot", None); scene.collection.objects.link(ring)
def adopt(o): o.parent = ring; return o

band = new_obj("Band", band_mesh()); band.data.materials.append(GOLD); shade_smooth(band); adopt(band)

# ---------------------------------------------------------------- head: six-prong basket + 1 ct stone
TOP = r_out(0)
GR = 0.34                                                 # girdle radius (~6.8 mm)
Z_G = TOP + 0.27
gem = new_obj("Diamond", brilliant_mesh("DiamondMesh", GR)); gem.location = (0, 0, Z_G)
gem.data.materials.append(DIAMOND); adopt(gem)

Z_TOP = Z_G + 0.052
def prong_r(z): return GR * lerp(0.30, 0.94, (z - TOP) / (Z_TOP - TOP))
Z_RAIL = Z_G - GR * 0.55
adopt(torus("Rail", prong_r(Z_RAIL), 0.019, (0, 0, Z_RAIL), GOLD, seg=128))
for k in range(6):
    a = k * math.pi / 3 + math.pi / 6
    base = (math.cos(a) * prong_r(TOP), math.sin(a) * prong_r(TOP), TOP - 0.02)
    top = (math.cos(a) * prong_r(Z_TOP), math.sin(a) * prong_r(Z_TOP), Z_TOP)
    adopt(cone_between(f"Prong{k}", 0.040, 0.029, base, top, GOLD, verts=20))
    adopt(sphere(f"Claw{k}", 0.040, (math.cos(a) * GR * 0.885, math.sin(a) * GR * 0.885, Z_TOP + 0.004), GOLD))

# ---------------------------------------------------------------- graduated pavé with shared beads
NS = 7
def pave_phi(k): return 0.36 + k * 0.165
def pave_r(k): return lerp(0.066, 0.040, k / (NS - 1))
meshes = {k: brilliant_mesh(f"Pave{k}", pave_r(k)) for k in range(NS)}   # correct pavilion angle so total internal reflection keeps them white
for side in (-1, 1):
    for k in range(NS):
        phi = side * pave_phi(k); r = r_out(phi) - 0.002
        pos = (math.sin(phi) * r, 0, math.cos(phi) * r)
        s = new_obj("Pave", meshes[k]); s.data.materials.append(DIAMOND_PAVE); s.location = pos; s.rotation_euler = (0, phi, 0); adopt(s)
        adopt(torus("Seat", pave_r(k) * 1.12, 0.008, pos, GOLD, rot=(0, phi, 0), seg=40))
        if k < NS - 1:                                     # bead between this stone and the next
            pm = side * (pave_phi(k) + pave_phi(k + 1)) / 2; rb = r_out(pm) + 0.002
            adopt(sphere("Bead", 0.017, (math.sin(pm) * rb, 0, math.cos(pm) * rb), GOLD, seg=16))

# ---------------------------------------------------------------- studio
floor_z = -r_out(math.pi)
bpy.ops.mesh.primitive_plane_add(size=120, location=(0, 0, floor_z))
floor = bpy.context.active_object; floor.name = "Floor"
floor.data.materials.append(flat_material("White", (0.9, 0.9, 0.9), 0.5)); floor.is_shadow_catcher = True
floor.visible_glossy = False

BLACK = flat_material("Flag", (0.006, 0.006, 0.006), 0.6)
def flag(name, size, loc, look_at=(0, 0, 0.6)):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = (size[0], size[1], 1)
    o.rotation_euler = (Vector(look_at) - Vector(loc)).to_track_quat("Z", "Y").to_euler()
    o.data.materials.append(BLACK); o.visible_camera = False; o.visible_shadow = False; return o

def softbox(name, size, loc, power, color=(1, 1, 1), look_at=(0, 0, 0.6), shadow=False):
    ld = bpy.data.lights.new(name, "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = size
    ld.use_shadow = shadow          # only the key light casts the (single, soft) contact shadow onto the floor
    ld.energy = power; ld.color = color
    o = bpy.data.objects.new(name, ld); scene.collection.objects.link(o); o.location = loc
    o.rotation_euler = (Vector(look_at) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    o.visible_camera = False; return o

WARM, COOL = (1.0, 0.97, 0.92), (0.93, 0.96, 1.0)
softbox("KeyTop",    (7, 7),      (0.5, -1.5, 9.5), 1100, (1.0, 0.985, 0.96), shadow=True)
softbox("FrontFill", (5, 3),    (0, -7.5, 5.5), 700, (0.97, 0.985, 1.0))
softbox("LeftStrip", (1.4, 9),    (-7.5, -3.0, 1.5), 1500, WARM)
softbox("RightStrip", (1.4, 9),   (7.5, -3.5, 2.0), 1300, COOL)
softbox("BackRim",   (6, 4),      (0, 8.5, 3.5), 520, WARM)
softbox("Spark1",    (0.5, 0.5),  (3.0, -4.5, 5.5), 420, COOL)
softbox("Spark2",    (0.5, 0.5),  (-3.5, -3.5, 4.5), 380, WARM)
softbox("Spark3",    (0.4, 0.4),  (0.8, -6.5, 6.5), 340, COOL)

# black flags carve crisp dark lines into the gold's reflections and give the stone contrast
flag("FlagL",   (3.2, 10),  (-4.2, 0.5, 1.2))
flag("FlagR",   (3.2, 10),  (4.4, 1.5, 1.4))
flag("FlagBack", (8, 2.2),  (0, 5.5, 4.8))
flag("FlagFront", (8, 3.0), (0, -6.5, 0.4))

world = bpy.data.worlds.new("World"); world.use_nodes = True; scene.world = world
bg = world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.96, 0.96, 0.97, 1); bg.inputs["Strength"].default_value = args.world

# ---------------------------------------------------------------- camera (85 mm, macro depth of field)
cam_data = bpy.data.cameras.new("Cam"); cam_data.lens = 85; cam_data.sensor_width = 36
cam_data.dof.use_dof = True; cam_data.dof.aperture_fstop = 9
cam = bpy.data.objects.new("Cam", cam_data); scene.collection.objects.link(cam); scene.camera = cam
focus = bpy.data.objects.new("Focus", None); scene.collection.objects.link(focus); cam_data.dof.focus_object = focus

def pose(p):
    push = smooth(0.26, 0.50, p) - smooth(0.62, 0.86, p)
    ring.rotation_euler = (0, 0, lerp(math.radians(-40), math.radians(360 + 28), p))
    elev = lerp(50, 12, smooth(0, 0.35, p)) + push * 24
    dist = 8.8 - push * 4.1
    tz = lerp(0.20, 1.30, push)
    t = Vector((0, 0, tz)); focus.location = t
    e = math.radians(elev)
    cam.location = t + Vector((0, -dist * math.cos(e), dist * math.sin(e)))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()

# ---------------------------------------------------------------- render settings
scene.render.engine = "CYCLES"
cy = scene.cycles
cy.samples = args.samples or (64 if args.preview is not None else 256)
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.015
cy.max_bounces = 32; cy.transmission_bounces = 28; cy.glossy_bounces = 16; cy.diffuse_bounces = 3
cy.transparent_max_bounces = 48; cy.sample_clamp_indirect = 10
cy.caustics_reflective = False; cy.caustics_refractive = False
cy.use_denoising = True
try: cy.denoiser = "OPENIMAGEDENOISE"
except Exception: pass

try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("OPTIX", "CUDA"):
        try:
            prefs.compute_device_type = kind; prefs.refresh_devices()
            devs = [d for d in prefs.devices if d.type == kind]
            if devs:
                for d in prefs.devices: d.use = (d.type == kind)
                cy.device = "GPU"; print("Cycles device:", kind, [d.name for d in devs]); break
        except Exception as ex: print("device", kind, "failed:", ex)
except Exception as ex:
    print("GPU setup skipped:", ex)

r = scene.render
r.resolution_x = r.resolution_y = args.size; r.resolution_percentage = 100
r.film_transparent = True
r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGBA"; r.image_settings.color_depth = "8"
vs = scene.view_settings
for pick in ("Khronos PBR Neutral", "Standard"):
    try:
        vs.view_transform = pick; print("view transform:", pick); break
    except TypeError:
        continue
try: vs.look = "None"
except TypeError: pass
vs.exposure = args.exposure

# ---------------------------------------------------------------- go
if args.preview is not None:
    pose(args.preview); r.filepath = args.out
    bpy.ops.render.render(write_still=True); print("wrote", args.out)
else:
    os.makedirs(args.out_dir, exist_ok=True)
    for i in range(args.start, args.frames):
        pose(i / (args.frames - 1)); r.filepath = os.path.join(args.out_dir, f"{i:04d}.png")
        bpy.ops.render.render(write_still=True); print(f"frame {i + 1}/{args.frames}", flush=True)
