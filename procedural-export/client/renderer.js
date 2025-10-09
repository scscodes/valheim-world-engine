/**
 * Valheim World Map Renderer
 * Renders 512×512 sample data to canvas with configurable resolution and smoothing
 */

// Biome enum values from Valheim
const BIOMES = {
    1: { name: 'Meadows', color: [121, 179, 85] },
    2: { name: 'BlackForest', color: [64, 81, 50] },
    4: { name: 'Swamp', color: [119, 108, 82] },
    8: { name: 'Mountain', color: [220, 225, 238] },
    16: { name: 'Plains', color: [193, 181, 122] },
    32: { name: 'Ocean', color: [59, 103, 163] },
    64: { name: 'Mistlands', color: [78, 93, 107] },
    256: { name: 'DeepNorth', color: [210, 230, 255] },
    512: { name: 'Ashlands', color: [155, 75, 60] }
};

class ValheimMapRenderer {
    constructor() {
        this.samplesData = null;
        this.canvas = null;
        this.ctx = null;
        this.currentMode = 'biome';
        this.polarFilter = true;  // Directional polar biome filtering
        this.availableSeeds = [];

        this.discoverSeeds();
        this.setupEventListeners();
        this.renderLegend();
    }

    async discoverSeeds() {
        // Try to find available sample files
        const possibleSeeds = ['hnLycKKCMI', 'hkLycKKCMI'];
        const possiblePaths = [
            (seed, res) => `../output/${seed}-samples-${res}.json`,
            (seed, res) => `../output/samples/${seed}-samples-${res}.json`
        ];
        const possibleResolutions = [512, 1024, 2048];

        const seedSelector = document.getElementById('seedSelector');

        for (const seed of possibleSeeds) {
            for (const pathTemplate of possiblePaths) {
                for (const res of possibleResolutions) {
                    const path = pathTemplate(seed, res);
                    try {
                        const response = await fetch(path, { method: 'HEAD' });
                        if (response.ok) {
                            const seedInfo = { seed, resolution: res, path };
                            this.availableSeeds.push(seedInfo);

                            const option = document.createElement('option');
                            option.value = path;
                            option.textContent = `${seed} (${res}×${res})`;
                            seedSelector.appendChild(option);
                        }
                    } catch (e) {
                        // File doesn't exist, skip
                    }
                }
            }
        }

        if (this.availableSeeds.length > 0) {
            // Auto-select first seed
            seedSelector.selectedIndex = 1;
            console.log(`Found ${this.availableSeeds.length} available samples`);
        }
    }

    setupEventListeners() {
        document.getElementById('seedSelector').addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadData(e.target.value);
            }
        });
        document.getElementById('loadBtn').addEventListener('click', () => {
            const selector = document.getElementById('seedSelector');
            if (selector.value) {
                this.loadData(selector.value);
            } else {
                alert('Please select a world seed first');
            }
        });
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadPNG());
        document.getElementById('renderMode').addEventListener('change', (e) => {
            this.currentMode = e.target.value;
            if (this.samplesData) this.render();
        });
        document.getElementById('polarFilter').addEventListener('change', (e) => {
            this.polarFilter = e.target.checked;
            if (this.samplesData) this.render();
        });
        document.getElementById('canvasSize').addEventListener('change', () => {
            if (this.samplesData) this.render();
        });
        document.getElementById('smoothing').addEventListener('change', (e) => {
            if (this.canvas) {
                this.canvas.style.imageRendering = e.target.value;
            }
        });
    }

    renderLegend() {
        const legendContainer = document.getElementById('legend');
        legendContainer.innerHTML = '';

        Object.entries(BIOMES).forEach(([id, biome]) => {
            const item = document.createElement('div');
            item.className = 'legend-item';

            const colorBox = document.createElement('div');
            colorBox.className = 'legend-color';
            colorBox.style.background = `rgb(${biome.color.join(',')})`;

            const label = document.createElement('span');
            label.textContent = biome.name;

            item.appendChild(colorBox);
            item.appendChild(label);
            legendContainer.appendChild(item);
        });
    }

    async loadData(samplePath) {
        const btn = document.getElementById('loadBtn');
        btn.disabled = true;
        btn.textContent = 'Loading...';

        const container = document.getElementById('mapContainer');
        container.innerHTML = '<div class="loading">Loading sample data...</div>';

        try {
            // Load samples data from specified path
            const response = await fetch(samplePath);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);

            this.samplesData = await response.json();

            // Update info display
            document.getElementById('worldName').textContent = this.samplesData.WorldName;
            document.getElementById('seed').textContent = this.samplesData.WorldName; // Seed name same as world
            document.getElementById('resolution').textContent = `${this.samplesData.Resolution}×${this.samplesData.Resolution}`;
            document.getElementById('sampleCount').textContent = this.samplesData.SampleCount.toLocaleString();
            document.getElementById('exportTime').textContent = this.samplesData.ExportTimestamp;

            // Render the map
            this.render();

            btn.textContent = 'Reload Data';
            document.getElementById('downloadBtn').disabled = false;
        } catch (error) {
            container.innerHTML = `<div class="loading" style="color: #ff6b6b;">Error: ${error.message}<br><br>Make sure sample data exists at:<br>../output/samples/hkLycKKCMI-samples-1024.json</div>`;
            btn.textContent = 'Retry Load';
        } finally {
            btn.disabled = false;
        }
    }

    render() {
        const startTime = performance.now();

        const resolution = this.samplesData.Resolution;
        const canvasSize = parseInt(document.getElementById('canvasSize').value);

        // Create canvas
        const container = document.getElementById('mapContainer');
        container.innerHTML = '';

        const canvasWrapper = document.createElement('div');
        canvasWrapper.className = 'canvas-container';

        this.canvas = document.createElement('canvas');
        this.canvas.width = canvasSize;
        this.canvas.height = canvasSize;
        this.canvas.style.imageRendering = document.getElementById('smoothing').value;

        const coords = document.createElement('div');
        coords.className = 'coordinates';
        coords.id = 'coordinates';
        coords.textContent = 'Move mouse over map';

        canvasWrapper.appendChild(this.canvas);
        canvasWrapper.appendChild(coords);
        container.appendChild(canvasWrapper);

        this.ctx = this.canvas.getContext('2d');

        // Create temporary canvas at native resolution
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = resolution;
        tempCanvas.height = resolution;
        const tempCtx = tempCanvas.getContext('2d');
        const imageData = tempCtx.createImageData(resolution, resolution);

        // Convert samples array to 2D grid for faster lookup
        console.log('Converting samples to grid...');
        const grid = this.samplesToGrid(this.samplesData.Samples, resolution);

        console.log('Rendering pixels...');

        let renderStats = {};
        if (this.currentMode === 'biome') {
            renderStats = this.renderBiomes(imageData, grid, resolution);
        } else {
            this.renderHeightmap(imageData, grid, resolution);
        }

        // Draw to temp canvas then scale to target
        tempCtx.putImageData(imageData, 0, 0);
        this.ctx.drawImage(tempCanvas, 0, 0, canvasSize, canvasSize);

        const renderTime = (performance.now() - startTime).toFixed(1);
        let statsText = `Rendered ${this.samplesData.SampleCount.toLocaleString()} samples in ${renderTime}ms`;

        if (renderStats.polarFiltered) {
            statsText += ` | Polar filter: ${renderStats.polarFiltered.toLocaleString()} reclassified (${(renderStats.polarFiltered/this.samplesData.SampleCount*100).toFixed(1)}%)`;
        }

        document.getElementById('stats').textContent = statsText;

        // Add mouse tracking
        this.addMouseTracking(resolution);

        console.log(`Render complete: ${renderTime}ms`);
    }

    samplesToGrid(samples, resolution) {
        const grid = new Array(resolution);
        for (let i = 0; i < resolution; i++) {
            grid[i] = new Array(resolution);
        }

        // Samples are in row-major order: [x=0,z=0], [x=0,z=1], ...
        let idx = 0;
        for (let x = 0; x < resolution; x++) {
            for (let z = 0; z < resolution; z++) {
                grid[x][z] = samples[idx++];
            }
        }

        return grid;
    }

    renderBiomes(imageData, grid, resolution) {
        const data = imageData.data;
        const SEA_LEVEL = 30.0;  // Valheim's base height for ocean
        const SHORELINE_DEPTH = -5.0;  // Shallow water threshold

        let polarFilterCount = 0;  // Track reclassifications

        for (let y = 0; y < resolution; y++) {
            for (let x = 0; x < resolution; x++) {
                // FIX: Invert Y-axis so top of screen = north (positive Z)
                const gridY = (resolution - 1) - y;
                const sample = grid[x][gridY];
                let biomeId = sample.Biome;
                const height = sample.Height;

                // QUALITY FIX #1: Correct Ocean misclassification
                // Ocean biome appears at >7900m from center, but if land is above sea level,
                // it's actually distant land, not ocean. Render as Mistlands (the usual outer biome)
                if (biomeId === 32 && height >= SEA_LEVEL) {
                    biomeId = 64;  // Reclassify as Mistlands (typical outer land biome)
                }

                // QUALITY FIX #2: DeepNorth/Ashlands land vs water distinction
                // Similar issue - these can be underwater (true ocean) or above water (land)
                if ((biomeId === 256 || biomeId === 512) && height < (SEA_LEVEL - 10)) {
                    biomeId = 32;  // Deep water in edge biomes = Ocean
                }

                // QUALITY FIX #4: Mistlands Recovery & Polar Biome Filtering
                // Problem: GetBiome() checks polar biomes BEFORE Mistlands, so they "steal"
                // the outer ring (6-10km) where Mistlands should dominate.
                // Solution: Convert most outer ring polar biomes → Mistlands,
                // keeping polar biomes only in far polar regions (crescents at poles)
                if (this.polarFilter) {
                    const worldX = sample.X;
                    const worldZ = sample.Z;
                    const distFromCenter = Math.sqrt(worldX * worldX + worldZ * worldZ);

                    // Define outer ring where Mistlands should dominate
                    const OUTER_RING_MIN = 6000;
                    const OUTER_RING_MAX = 10000;
                    const POLAR_THRESHOLD = 7000;  // Only keep polar biomes beyond this latitude

                    const inOuterRing = (distFromCenter >= OUTER_RING_MIN && distFromCenter <= OUTER_RING_MAX);

                    if (inOuterRing) {
                        // Ashlands: Keep only in FAR south (Z < -POLAR_THRESHOLD)
                        if (biomeId === 512) {
                            if (worldZ >= -POLAR_THRESHOLD) {
                                // Not in far south → Convert to Mistlands
                                biomeId = 64;
                                polarFilterCount++;
                            }
                            // else: Keep as Ashlands (far south crescent)
                        }

                        // DeepNorth: Keep only in FAR north (Z > POLAR_THRESHOLD)
                        if (biomeId === 256) {
                            if (worldZ <= POLAR_THRESHOLD) {
                                // Not in far north → Convert to Mistlands
                                biomeId = 64;
                                polarFilterCount++;
                            }
                            // else: Keep as DeepNorth (far north crescent)
                        }
                    }
                }

                const biome = BIOMES[biomeId];
                const idx = (y * resolution + x) * 4;

                if (biome) {
                    let r = biome.color[0];
                    let g = biome.color[1];
                    let b = biome.color[2];

                    // QUALITY FIX #3: Shoreline detection and rendering
                    // Check if this is near water edge (height between shallow water and land)
                    if (height > SHORELINE_DEPTH && height < SEA_LEVEL && biomeId !== 32) {
                        // This is shoreline/shallow water - blend biome color with water
                        const waterBlue = [59, 103, 163];  // Ocean color
                        const blend = (height - SHORELINE_DEPTH) / (SEA_LEVEL - SHORELINE_DEPTH);
                        r = Math.floor(r * blend + waterBlue[0] * (1 - blend));
                        g = Math.floor(g * blend + waterBlue[1] * (1 - blend));
                        b = Math.floor(b * blend + waterBlue[2] * (1 - blend));
                    }

                    data[idx] = r;
                    data[idx + 1] = g;
                    data[idx + 2] = b;
                } else {
                    // Unknown biome - magenta
                    data[idx] = 255;
                    data[idx + 1] = 0;
                    data[idx + 2] = 255;
                }
                data[idx + 3] = 255; // Alpha
            }
        }

        return {
            polarFiltered: this.polarFilter ? polarFilterCount : 0
        };
    }

    renderHeightmap(imageData, grid, resolution) {
        const data = imageData.data;

        // Find height range
        let minHeight = Infinity;
        let maxHeight = -Infinity;

        for (let y = 0; y < resolution; y++) {
            for (let x = 0; x < resolution; x++) {
                const gridY = (resolution - 1) - y;
                const h = grid[x][gridY].Height;
                if (h < minHeight) minHeight = h;
                if (h > maxHeight) maxHeight = h;
            }
        }

        const range = maxHeight - minHeight;
        console.log(`Height range: ${minHeight.toFixed(1)}m to ${maxHeight.toFixed(1)}m`);

        for (let y = 0; y < resolution; y++) {
            for (let x = 0; x < resolution; x++) {
                const gridY = (resolution - 1) - y;
                const sample = grid[x][gridY];
                const height = sample.Height;
                const normalized = (height - minHeight) / range;

                // Grayscale heightmap
                const value = Math.floor(normalized * 255);

                const idx = (y * resolution + x) * 4;
                data[idx] = value;
                data[idx + 1] = value;
                data[idx + 2] = value;
                data[idx + 3] = 255;
            }
        }
    }

    addMouseTracking(resolution) {
        this.canvas.addEventListener('mousemove', (e) => {
            const rect = this.canvas.getBoundingClientRect();
            const canvasX = Math.floor((e.clientX - rect.left) / rect.width * resolution);
            const canvasY = Math.floor((e.clientY - rect.top) / rect.height * resolution);

            if (canvasX >= 0 && canvasX < resolution && canvasY >= 0 && canvasY < resolution) {
                // Convert samples array to grid indices
                const gridX = canvasX;
                const gridY = canvasY;
                const sampleIdx = gridX * resolution + gridY;

                const sample = this.samplesData.Samples[sampleIdx];
                if (sample) {
                    const biome = BIOMES[sample.Biome];
                    const biomeName = biome ? biome.name : `Unknown(${sample.Biome})`;

                    const coords = document.getElementById('coordinates');
                    coords.textContent =
                        `World: (${sample.X.toFixed(0)}, ${sample.Z.toFixed(0)}) | ` +
                        `Grid: (${gridX}, ${gridY}) | ` +
                        `Biome: ${biomeName} | ` +
                        `Height: ${sample.Height.toFixed(1)}m | ` +
                        `Distance: ${Math.sqrt(sample.X * sample.X + sample.Z * sample.Z).toFixed(0)}m`;
                }
            }
        });

        this.canvas.addEventListener('mouseleave', () => {
            document.getElementById('coordinates').textContent = 'Move mouse over map';
        });
    }

    downloadPNG() {
        if (!this.canvas) return;

        const link = document.createElement('a');
        const filename = `${this.samplesData.WorldName}-${this.currentMode}-${this.canvas.width}x${this.canvas.height}.png`;
        link.download = filename;
        link.href = this.canvas.toDataURL('image/png');
        link.click();
    }
}

// Initialize on page load
const renderer = new ValheimMapRenderer();
