# Rendering the showcase frames

`ring_scene.py` builds a placeholder gold solitaire (real brilliant-cut stone, six prongs, bezel-set pavé) and renders a
transparent-background turntable with Cycles. Choreography matches the page's three chapters.

Blender 5.2 is not part of the repo. It was installed portable at
`C:\Users\<you>\tools\blender-5.2.2\blender-5.2.2-windows-x64\blender.exe` (official zip from download.blender.org).

```powershell
$b = "<path to blender.exe>"
# quick still at scroll progress 0..1
& $b -b -P scripts/blender/ring_scene.py -- --preview 0.42 --size 800 --samples 96 --out preview.png
# full sequence (resume with --start N)
& $b -b -P scripts/blender/ring_scene.py -- --frames 120 --size 1024 --samples 128 --out-dir <frames dir>
# encode to web frames
python -I scripts/encode-frames.py <frames dir>
```

On an RTX 3060 laptop (OptiX) a 1024px frame at 128 samples takes about 5 s.

If you change the camera path in `pose()`, update `pushAt()` in `js/hero-seq.js` so the background morph and chapter
timing stay in step with the render.

To use real photos later: shoot a turntable (36–120 evenly spaced frames, same lighting, piece centred), cut the
backgrounds out to transparent PNG, put them in a folder and run `encode-frames.py` on it.
