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

        this.setupEventListeners();
        this.renderLegend();
    }

    setupEventListeners() {
        document.getElementById('loadBtn').addEventListener('click', () => this.loadData());
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadPNG());
        document.getElementById('renderMode').addEventListener('change', (e) => {
            this.currentMode = e.target.value;
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

    async loadData() {
        const btn = document.getElementById('loadBtn');
        btn.disabled = true;
        btn.textContent = 'Loading...';

        const container = document.getElementById('mapContainer');
        container.innerHTML = '<div class="loading">Loading sample data...</div>';

        try {
            // Load samples data
            const response = await fetch('../output/samples/hkLycKKCMI-samples-1024.json');
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

        if (this.currentMode === 'biome') {
            this.renderBiomes(imageData, grid, resolution);
        } else {
            this.renderHeightmap(imageData, grid, resolution);
        }

        // Draw to temp canvas then scale to target
        tempCtx.putImageData(imageData, 0, 0);
        this.ctx.drawImage(tempCanvas, 0, 0, canvasSize, canvasSize);

        const renderTime = (performance.now() - startTime).toFixed(1);
        document.getElementById('stats').textContent =
            `Rendered ${this.samplesData.SampleCount.toLocaleString()} samples in ${renderTime}ms`;

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

        for (let y = 0; y < resolution; y++) {
            for (let x = 0; x < resolution; x++) {
                const sample = grid[x][y];
                const biomeId = sample.Biome;
                const biome = BIOMES[biomeId];

                const idx = (y * resolution + x) * 4;

                if (biome) {
                    data[idx] = biome.color[0];
                    data[idx + 1] = biome.color[1];
                    data[idx + 2] = biome.color[2];
                } else {
                    // Unknown biome - magenta
                    data[idx] = 255;
                    data[idx + 1] = 0;
                    data[idx + 2] = 255;
                }
                data[idx + 3] = 255; // Alpha
            }
        }
    }

    renderHeightmap(imageData, grid, resolution) {
        const data = imageData.data;

        // Find height range
        let minHeight = Infinity;
        let maxHeight = -Infinity;

        for (let y = 0; y < resolution; y++) {
            for (let x = 0; x < resolution; x++) {
                const h = grid[x][y].Height;
                if (h < minHeight) minHeight = h;
                if (h > maxHeight) maxHeight = h;
            }
        }

        const range = maxHeight - minHeight;
        console.log(`Height range: ${minHeight.toFixed(1)}m to ${maxHeight.toFixed(1)}m`);

        for (let y = 0; y < resolution; y++) {
            for (let x = 0; x < resolution; x++) {
                const sample = grid[x][y];
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
