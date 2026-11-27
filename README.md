# Cyber Content Videos

**0xLore**: daily YouTube Shorts that explain lesser-known cybersecurity concepts as short
stories. Each one is fact-checked against the original research papers,
advisories or vendor documents.

## Layout
```
videos/<date>-<topic>/
  video.mp4   final render (1080×1920, 30 fps, H.264); published via its raw URL
  script.md   voiceover, the source for every claim, and YouTube metadata
  render.py   script that renders this video (Kokoro TTS + PIL + ffmpeg)
```

## Rendering
```bash
pip install kokoro-onnx soundfile numpy pillow
# kokoro-v1.0.onnx and voices-v1.0.bin from github.com/thewh1teagle/kokoro-onnx releases
python3 videos/<folder>/render.py <dir-with-model-files> out.mp4
```
Music and sound effects are generated in code, so there's no third-party audio.

## Workflow
Pick topic → research and fact-check → script + sources → owner review →
render → owner approves the video → schedule on YouTube via Metricool.
Nothing is published without the owner's explicit approval.
