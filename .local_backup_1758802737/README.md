## Valheim World File Analysis (seed.db/seed.fwl)

This repo contains a Node.js analyzer to inspect and extract structured data from Valheim dedicated server world files (`.db` and `.fwl`). It produces logs, extracted artifacts, clustering views, and terrain height grids suitable for use in a web app (terrain/biome/region overlays).

### Prerequisites
- Node.js 16+ (tested with modern Node).
- Disk space: up to a few GB for extracted artifacts on large worlds.
- Files in this directory:
  - `file_analyzer.js` (the analyzer)
  - `seed.db` and `seed.fwl` (your world files)

### Quick Start (repeatable process)
1) Run the analyzer with absolute paths (recommended):

```bash
node /home/steve/projects/valheim/file_analyzer.js \
  /home/steve/projects/valheim/seed.fwl \
  /home/steve/projects/valheim/seed.db
```

2) Review per-file analysis logs (auto-created):

```bash
less /home/steve/projects/valheim/seed.fwl.analysis.txt
less /home/steve/projects/valheim/seed.db.analysis.txt
```

3) Explore extracted artifacts and manifests:

```bash
ls -1 /home/steve/projects/valheim/extracted/seed.db
cat /home/steve/projects/valheim/extracted/seed.db/index.json | head -n 50
cat /home/steve/projects/valheim/extracted/seed.db/clusters.json | head -n 50
ls -1 /home/steve/projects/valheim/extracted/seed.db/clusters
```

### What the analyzer does
The analyzer performs a series of non-destructive heuristics over each input file:
- Signature scan: looks for known headers (gzip, zlib, SQLite markers, UnityFS hints, Valheim-like patterns).
- Structure analysis: basic chunk-size patterns and embedded header checks.
- Decompression attempts:
  - Full-file: gzip/deflate/deflate-raw/brotli.
  - Chunked: common chunk sizes (1–64 KB) with inflate.
  - Signature-based: starts decompression from any found gzip/zlib header offsets.
- Advanced extraction:
  - XOR key attempts on the raw file.
  - Header skipping, endianness variations.
- Content analysis of each decompressed blob:
  - Detects XML/JSON-like content.
  - Detects terrain-like float32 patterns and height value plausibility.

### Outputs and structure
For each input file, outputs are written alongside a per-file log and an extraction directory:

- Logs
  - `<file>.analysis.txt` — Full console output for that file; always created.

- Extraction directory
  - `extracted/<basename>/index.json` — Index of all artifacts with metadata (method, offset, quick analysis).
  - `extracted/<basename>/clusters.json` — Manifest grouping artifacts by detected type.
  - `extracted/<basename>/clusters/` — Symlinked views for quick browsing by type:
    - `sqlite/`, `xml/`, `json/`, `terrain/`, `unknown/`.

- Artifact naming scheme
  - `gzip_at_<offset>.bin`, `zlib_at_<offset>.bin` — Decompressed blobs from signature-based offsets.
  - `chunk_<offset>_<size>.bin` — Blobs decompressed from chunked attempts.
  - When terrain-like data is detected:
    - `*.float32_preview.csv` — Small preview (first ~1K bytes as float32), 16 columns per row.
    - `*.float32_1d.csv` — Full 1D export of the best contiguous float32 region.
    - `*.float32_grid_w<width>_h<height>.csv` — Full 2D grid export (when dimensions inferred).
    - `*.float32.raw.bin` — Raw binary slice (float32 LE) of the inferred region.
    - `*.float32.meta.json` — Metadata for the float32 region (start offset, count, stats, paths).
  - When XML-like data is detected:
    - `*.xml` — Saved starting from the first `<` in the blob.

### Typical workflow for terrain/biome overlays
1) Run the analyzer against `seed.db`.
2) Inspect `extracted/seed.db/terrain` and corresponding `*.float32_*` files to load heights.
3) Use `*.float32_grid_w*_h*.csv` or `*.float32.raw.bin` as input to your raster pipeline.
4) If needed, normalize or resample values for your web app’s tiles.

### Re-running safely
- Outputs are overwritten on re-run for the same filenames.
- To start fresh:

```bash
rm -rf /home/steve/projects/valheim/extracted/seed.db \
       /home/steve/projects/valheim/seed.db.analysis.txt \
       /home/steve/projects/valheim/seed.fwl.analysis.txt
```

### Tips
- Logs are verbose. To skim: `tail -n 200 seed.db.analysis.txt`.
- Find exported grids quickly:

```bash
ls -1 /home/steve/projects/valheim/extracted/seed.db | grep float32_
```

### Limitations
- Valheim formats are custom and evolve; this tool uses heuristics and best-effort scans.
- No SQLite has been detected so far in sample worlds (common for Valheim).
- Grid dimension inference is heuristic-based; adjust as needed for your pipeline.

### Extending
- To tweak heuristics (chunk sizes, XOR keys, grid inference), edit `file_analyzer.js`.
- If you need heightmaps in GeoTIFF/PNG, stitch and encode from the exported CSV/bin grids in your build step.

### Example one-liners

Run only on `seed.db` and save output to a file:

```bash
node /home/steve/projects/valheim/file_analyzer.js /home/steve/projects/valheim/seed.db \
  > /home/steve/projects/valheim/seed.db.run.log 2>&1
```

Open cluster manifests:

```bash
cat /home/steve/projects/valheim/extracted/seed.db/clusters.json | jq '.' | head -n 80
```



