/**
 * Valheim File Format Analysis Tools
 * 
 * Valheim world files (.db/.fwl) are NOT standard SQLite databases
 * They use a custom binary format with compression and encryption-like obfuscation
 */

const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');
const path = require('path');

class ValheimFileAnalyzer {
  constructor() {
    // Known Valheim file signatures and patterns
    this.signatures = {
      // Common compression headers
      gzip: Buffer.from([0x1f, 0x8b]),
      zlib: Buffer.from([0x78]),
      sqlite: Buffer.from('SQLite format 3', 'ascii'),
      // Valheim-specific patterns (discovered through reverse engineering)
      valheimHeader: Buffer.from([0x01, 0x00, 0x00, 0x00]), // Common at start
      unityAsset: Buffer.from('UnityFS', 'ascii')
    };
    
    this.compressionMethods = [
      'gzip',
      'deflate', 
      'raw',
      'brotli'
    ];
  }

  /**
   * Analyze a Valheim world file to determine its format
   */
  analyzeFile(filepath) {
    console.log(`\n=== Analyzing: ${filepath} ===`);
    
    if (!fs.existsSync(filepath)) {
      throw new Error(`File not found: ${filepath}`);
    }
    
    const stats = fs.statSync(filepath);
    const buffer = fs.readFileSync(filepath);

    // Prepare extraction output directory and index
    this._currentFilepath = filepath;
    this._currentOutDir = this.ensureOutDir(filepath);
    this._currentIndex = [];
    
    console.log(`File size: ${stats.size} bytes`);
    console.log(`First 32 bytes (hex): ${buffer.slice(0, 32).toString('hex')}`);
    console.log(`First 32 bytes (ascii): ${this.bufferToSafeAscii(buffer.slice(0, 32))}`);
    
    // Check for known signatures
    this.checkSignatures(buffer);
    
    // Analyze file structure
    this.analyzeStructure(buffer);
    
    // Attempt various decompression methods
    this.attemptDecompression(buffer, filepath);

    // Cluster artifacts by content type (symlinked views) and write manifest
    try {
      const clustersPath = this.clusterArtifacts();
      if (clustersPath) {
        console.log(`Clusters written: ${clustersPath}`);
      }
    } catch (e) {
      console.error('Failed clustering artifacts:', e.message);
    }

    // Persist index for this file
    try {
      const indexPath = path.join(this._currentOutDir, 'index.json');
      fs.writeFileSync(indexPath, JSON.stringify(this._currentIndex, null, 2));
      console.log(`Index written: ${indexPath}`);
    } catch (e) {
      console.error('Failed writing index:', e.message);
    }
    
    return {
      size: stats.size,
      header: buffer.slice(0, 64),
      analysis: this.getAnalysisResults(buffer)
    };
  }
  
  /**
   * Check for known file format signatures
   */
  checkSignatures(buffer) {
    console.log('\n--- Signature Analysis ---');
    
    Object.entries(this.signatures).forEach(([name, signature]) => {
      const found = this.findPattern(buffer, signature);
      if (found.length > 0) {
        console.log(`✓ ${name} signature found at offset(s): ${found.join(', ')}`);
      } else {
        console.log(`✗ ${name} signature not found`);
      }
    });
  }
  
  /**
   * Analyze the overall file structure
   */
  analyzeStructure(buffer) {
    console.log('\n--- Structure Analysis ---');
    
    // Look for repeating patterns that might indicate chunk boundaries
    const chunkSizes = [64, 128, 256, 512, 1024, 2048, 4096];
    
    chunkSizes.forEach(size => {
      if (buffer.length % size === 0) {
        console.log(`✓ File length is multiple of ${size} (potential chunk size)`);
      }
    });
    
    // Look for embedded file headers within the data
    const sqlitePattern = Buffer.from('SQLite format 3', 'ascii');
    const sqliteOffset = buffer.indexOf(sqlitePattern);
    if (sqliteOffset > 0) {
      console.log(`✓ SQLite database found embedded at offset ${sqliteOffset}`);
      return this.extractEmbeddedDatabase(buffer, sqliteOffset);
    }
    
    // Check for common compression patterns
    this.detectCompressionType(buffer);
  }
  
  /**
   * Attempt various decompression methods
   */
  attemptDecompression(buffer, originalPath) {
    console.log('\n--- Decompression Attempts ---');
    
    const methods = [
      { name: 'gzip', fn: (buf) => zlib.gunzipSync(buf) },
      { name: 'deflate', fn: (buf) => zlib.inflateSync(buf) },
      { name: 'deflate-raw', fn: (buf) => zlib.inflateRawSync(buf) },
      { name: 'brotli', fn: (buf) => zlib.brotliDecompressSync(buf) }
    ];
    
    // Try decompressing the entire file
    methods.forEach(method => {
      try {
        console.log(`Trying ${method.name} on full file...`);
        const decompressed = method.fn(buffer);
        console.log(`✓ ${method.name} SUCCESS! Decompressed size: ${decompressed.length}`);
        
        // Save decompressed data (legacy path and structured path)
        const outputPath = `${originalPath}.${method.name}.extracted`;
        fs.writeFileSync(outputPath, decompressed);
        console.log(`  Saved to: ${outputPath}`);

        const outName = `${method.name}_full.bin`;
        const outPath = this.writeArtifact(this._currentOutDir, outName, decompressed);
        const analysis = this.analyzeDecompressedData(decompressed);
        this._currentIndex.push({ kind: 'full', method: method.name, offset: 0, size: decompressed.length, path: outPath, analysis });
        this.maybeExportStructuredArtifacts(decompressed, outPath, analysis);
        this.tryTransformsOnData(decompressed, outPath, { method: method.name, offset: 0 });
        
      } catch (error) {
        console.log(`✗ ${method.name} failed: ${error.message.split('\n')[0]}`);
      }
    });
    
    // Try decompressing chunks of the file
    this.attemptChunkedDecompression(buffer, originalPath);

    // Try signature-based decompression from embedded offsets
    this.attemptSignatureBasedDecompression(buffer, originalPath);
  }
  
  /**
   * Try decompressing the file in chunks
   */
  attemptChunkedDecompression(buffer, originalPath) {
    console.log('\n--- Chunked Decompression Attempts ---');
    
    // Common chunk sizes in Valheim
    const chunkSizes = [1024, 2048, 4096, 8192, 16384, 32768, 65536];
    
    chunkSizes.forEach(chunkSize => {
      if (buffer.length < chunkSize) return;
      
      console.log(`\nTrying chunks of ${chunkSize} bytes...`);
      
      for (let offset = 0; offset <= buffer.length - chunkSize; offset += chunkSize) {
        const chunk = buffer.slice(offset, offset + chunkSize);
        
        try {
          const decompressed = zlib.inflateSync(chunk);
          console.log(`✓ Chunk at offset ${offset} decompressed! Size: ${decompressed.length}`);
          
          // Save successful chunk (legacy path and structured path)
          const chunkPath = `${originalPath}.chunk_${offset}_${chunkSize}.extracted`;
          fs.writeFileSync(chunkPath, decompressed);

          const outName = `chunk_${offset}_${chunkSize}.bin`;
          const outPath = this.writeArtifact(this._currentOutDir, outName, decompressed);
          const analysis = this.analyzeDecompressedData(decompressed);
          this._currentIndex.push({ kind: 'chunk', method: 'inflate', offset, chunkSize, size: decompressed.length, path: outPath, analysis });
          this.maybeExportStructuredArtifacts(decompressed, outPath, analysis);
          this.tryTransformsOnData(decompressed, outPath, { method: 'inflate', offset });

          // Quick analysis of chunk content
          this.quickAnalyzeChunk(decompressed, offset);
          
        } catch (error) {
          // Silently continue - most chunks won't decompress
        }
      }
    });
  }

  /**
   * Attempt decompression from embedded signature offsets (gzip/zlib)
   */
  attemptSignatureBasedDecompression(buffer, originalPath) {
    console.log('\n--- Signature-based Decompression Attempts ---');
    
    // GZIP streams
    const gzipSig = Buffer.from([0x1f, 0x8b]);
    let searchOffset = 0;
    while (searchOffset < buffer.length) {
      const idx = buffer.indexOf(gzipSig, searchOffset);
      if (idx === -1) break;
      try {
        console.log(`Trying gunzip from offset ${idx}...`);
        const decompressed = zlib.gunzipSync(buffer.slice(idx));
        console.log(`✓ gunzip from ${idx} SUCCESS! Decompressed size: ${decompressed.length}`);
        const out = `${originalPath}.gzip_at_${idx}.extracted`;
        fs.writeFileSync(out, decompressed);
        const outName = `gzip_at_${idx}.bin`;
        const outPath = this.writeArtifact(this._currentOutDir, outName, decompressed);
        const analysis = this.analyzeDecompressedData(decompressed);
        this._currentIndex.push({ kind: 'signature', method: 'gzip', offset: idx, size: decompressed.length, path: outPath, analysis });
        this.maybeExportStructuredArtifacts(decompressed, outPath, analysis);
        this.tryTransformsOnData(decompressed, outPath, { method: 'gzip', offset: idx });
      } catch (e) {
        console.log(`✗ gunzip from ${idx} failed: ${e.message.split('\n')[0]}`);
      }
      searchOffset = idx + 1;
    }
    
    // ZLIB streams (0x78 + common flags)
    const zlibSecondBytes = [0x01, 0x5e, 0x9c, 0xda];
    searchOffset = 0;
    while (searchOffset < buffer.length) {
      const idx = buffer.indexOf(0x78, searchOffset);
      if (idx === -1 || idx + 1 >= buffer.length) break;
      if (!zlibSecondBytes.includes(buffer[idx + 1])) {
        searchOffset = idx + 1;
        continue;
      }
      try {
        console.log(`Trying inflate from offset ${idx}...`);
        const decompressed = zlib.inflateSync(buffer.slice(idx));
        console.log(`✓ inflate from ${idx} SUCCESS! Decompressed size: ${decompressed.length}`);
        const out = `${originalPath}.zlib_at_${idx}.extracted`;
        fs.writeFileSync(out, decompressed);
        const outName = `zlib_at_${idx}.bin`;
        const outPath = this.writeArtifact(this._currentOutDir, outName, decompressed);
        const analysis = this.analyzeDecompressedData(decompressed);
        this._currentIndex.push({ kind: 'signature', method: 'zlib', offset: idx, size: decompressed.length, path: outPath, analysis });
        this.maybeExportStructuredArtifacts(decompressed, outPath, analysis);
        this.tryTransformsOnData(decompressed, outPath, { method: 'zlib', offset: idx });
      } catch (e) {
        // ignore
      }
      searchOffset = idx + 1;
    }
  }
  
  /**
   * Analyze decompressed data to see if it contains a database
   */
  analyzeDecompressedData(data) {
    console.log('\n  --- Decompressed Data Analysis ---');
    const previewHex = data.slice(0, 64).toString('hex');
    const previewAscii = this.bufferToSafeAscii(data.slice(0, 64));
    console.log(`  First 64 bytes (hex): ${previewHex}`);
    console.log(`  First 64 bytes (ascii): ${previewAscii}`);

    const isSQLite = data.slice(0, 15).toString('ascii') === 'SQLite format 3';
    if (isSQLite) {
      console.log('  ✓ FOUND SQLITE DATABASE!');
    }

    // Log other structured data hints and compute details
    this.checkForStructuredData(data);
    const info = this.checkForStructuredDataGet(data);

    return {
      isSQLite,
      hasJSON: info.json,
      hasXML: info.xml,
      previewHex,
      previewAscii,
      terrainPatterns: info.terrainPatterns,
      heightLikePct: info.heightLikePct
    };
  }
  
  /**
   * Quick analysis of extracted chunks
   */
  quickAnalyzeChunk(chunk, offset) {
    const preview = chunk.slice(0, 32);
    console.log(`    Offset ${offset}: ${this.bufferToSafeAscii(preview)}`);
    
    // Check for SQLite
    if (chunk.slice(0, 15).toString('ascii') === 'SQLite format 3') {
      console.log(`    ✓ SQLite database found in chunk at offset ${offset}!`);
    }
  }
  
  /**
   * Extract embedded SQLite database
   */
  extractEmbeddedDatabase(buffer, offset) {
    console.log(`\nExtracting embedded SQLite database from offset ${offset}...`);
    
    const dbData = buffer.slice(offset);
    const outputPath = 'extracted_database.db';
    
    fs.writeFileSync(outputPath, dbData);
    console.log(`✓ Database extracted to: ${outputPath}`);
    
    return outputPath;
  }
  
  /**
   * Detect compression type based on header analysis
   */
  detectCompressionType(buffer) {
    const header = buffer.slice(0, 16);
    
    // GZIP magic number
    if (header[0] === 0x1f && header[1] === 0x8b) {
      console.log('✓ GZIP compression detected');
      return 'gzip';
    }
    
    // ZLIB magic number combinations
    if (header[0] === 0x78) {
      if ([0x01, 0x9c, 0xda, 0x5e].includes(header[1])) {
        console.log('✓ ZLIB compression detected');
        return 'zlib';
      }
    }
    
    // Check for custom Valheim compression patterns
    if (this.detectValheimCompression(header)) {
      console.log('✓ Possible Valheim custom compression detected');
      return 'valheim';
    }
    
    console.log('✗ No standard compression format detected');
    return 'unknown';
  }
  
  /**
   * Look for Valheim-specific compression patterns
   */
  detectValheimCompression(header) {
    // Common patterns found in Valheim files (reverse engineered)
    const patterns = [
      [0x01, 0x00, 0x00, 0x00], // Common header
      [0x02, 0x00, 0x00, 0x00], // Version variant
      [0x00, 0x00, 0x00, 0x01], // Endian variant
    ];
    
    return patterns.some(pattern => 
      pattern.every((byte, index) => header[index] === byte)
    );
  }
  
  /**
   * Check for structured data patterns
   */
  checkForStructuredData(data) {
    const info = this.checkForStructuredDataGet(data);
    if (info.json) console.log('  ✓ JSON data detected');
    if (info.xml) console.log('  ✓ XML data detected');
    if (info.terrainPatterns) console.log('  ✓ Regular grid patterns detected (possible terrain data)');
    if (typeof info.heightLikePct === 'number') console.log(`  ✓ Height-like float32 data detected (${(info.heightLikePct * 100).toFixed(1)}% valid)`);
  }

  checkForStructuredDataGet(data) {
    const jsonStart = data.indexOf(Buffer.from('{'));
    const xmlStart = data.indexOf(Buffer.from('<'));
    const terrainPatterns = this.detectTerrainDataGet(data);
    const heightLikePct = this.detectHeightDataGet(data);
    return {
      json: jsonStart >= 0 && jsonStart < 1000,
      xml: xmlStart >= 0 && xmlStart < 1000,
      terrainPatterns,
      heightLikePct
    };
  }
  
  /**
   * Look for patterns that might be Valheim terrain data
   */
  detectTerrainData(data) {
    // Terrain chunks typically contain:
    // - Height values (float32 arrays)
    // - Biome IDs (uint8 arrays)
    // - Regular patterns due to grid structure
    
    // Check for repeating patterns every 64 bytes (potential grid data)
    let patternCount = 0;
    for (let i = 0; i < Math.min(data.length - 64, 1000); i += 64) {
      const chunk1 = data.slice(i, i + 4);
      const chunk2 = data.slice(i + 64, i + 68);
      if (chunk1.equals(chunk2)) patternCount++;
    }
    
    if (patternCount > 3) {
      console.log('  ✓ Regular grid patterns detected (possible terrain data)');
    }
    
    // Check for float32 ranges typical of Valheim heights (-200 to +200)
    this.detectHeightData(data);
  }

  detectTerrainDataGet(data) {
    let patternCount = 0;
    for (let i = 0; i < Math.min(data.length - 64, 1000); i += 64) {
      const chunk1 = data.slice(i, i + 4);
      const chunk2 = data.slice(i + 64, i + 68);
      if (chunk1.equals(chunk2)) patternCount++;
    }
    return patternCount > 3;
  }
  
  /**
   * Look for height data patterns
   */
  detectHeightData(data) {
    const pct = this.detectHeightDataGet(data);
    if (pct > 0.5) {
      console.log(`  ✓ Height-like float32 data detected (${(pct * 100).toFixed(1)}% valid)`);
    }
  }

  detectHeightDataGet(data) {
    let validHeights = 0;
    for (let i = 0; i < Math.min(data.length - 4, 1000); i += 4) {
      const value = data.readFloatLE(i);
      if (!isNaN(value) && value > -300 && value < 300) {
        validHeights++;
      }
    }
    const validPercentage = validHeights / (Math.min(data.length, 1000) / 4);
    return validPercentage;
  }
  
  /**
   * Utility functions
   */
  findPattern(buffer, pattern) {
    const found = [];
    let offset = 0;
    
    while (offset < buffer.length) {
      const index = buffer.indexOf(pattern, offset);
      if (index === -1) break;
      found.push(index);
      offset = index + 1;
    }
    
    return found;
  }
  
  bufferToSafeAscii(buffer) {
    return buffer.toString('ascii').replace(/[^\x20-\x7E]/g, '.');
  }
  
  getAnalysisResults(buffer) {
    return {
      isPotentialDatabase: buffer.indexOf(Buffer.from('SQLite format 3', 'ascii')) >= 0,
      isCompressed: this.detectCompressionType(buffer) !== 'unknown',
      hasRegularPatterns: this.hasRegularPatterns(buffer),
      estimatedFormat: this.estimateFormat(buffer)
    };
  }
  
  hasRegularPatterns(buffer) {
    // Simple check for repeating byte patterns
    const samples = Math.min(buffer.length, 1024);
    let patterns = 0;
    
    for (let i = 0; i < samples - 8; i += 8) {
      const chunk = buffer.slice(i, i + 4);
      if (buffer.indexOf(chunk, i + 4) > i) {
        patterns++;
      }
    }
    
    return patterns > samples / 32;
  }
  
  estimateFormat(buffer) {
    const compression = this.detectCompressionType(buffer);
    if (compression !== 'unknown') return compression;
    
    if (buffer.indexOf(Buffer.from('SQLite format 3', 'ascii')) >= 0) {
      return 'embedded-sqlite';
    }
    
    if (this.hasRegularPatterns(buffer)) {
      return 'structured-binary';
    }
    
    return 'unknown-binary';
  }

  // Output helpers
  ensureOutDir(filepath) {
    const base = path.basename(filepath);
    const outDir = path.resolve(process.cwd(), 'extracted', base);
    try { fs.mkdirSync(outDir, { recursive: true }); } catch (_) {}
    return outDir;
  }

  writeArtifact(outDir, filename, data) {
    const outPath = path.join(outDir, filename);
    fs.writeFileSync(outPath, data);
    return outPath;
  }

  tryTransformsOnData(data, originalOutPath, context) {
    // Try simple XOR keys and bit-rotations to reveal headers
    const testSlice = data.slice(0, Math.min(4096, data.length));
    const xorKeys = [0x01, 0x10, 0x20, 0x40, 0x55, 0x69, 0x7F, 0xAA, 0xC3, 0xFF];
    const rotations = [1, 2, 3, 4, 7];

    const checkAndRecord = (buf, label) => {
      const isSQLite = buf.slice(0, 15).toString('ascii') === 'SQLite format 3';
      const looksJSON = buf[0] === 0x7b || buf[0] === 0x5b; // { or [
      const looksXML = buf[0] === 0x3c; // <
      if (isSQLite || looksJSON || looksXML) {
        const outName = path.basename(originalOutPath) + `.${label}.decoded`;
        const outPath = this.writeArtifact(this._currentOutDir, outName, buf);
        console.log(`  ✓ Transform ${label} revealed structured content -> ${outPath}`);
        const analysis = this.analyzeDecompressedData(buf);
        this._currentIndex.push({ kind: 'transform', transform: label, from: originalOutPath, size: buf.length, path: outPath, analysis, context });
      }
    };

    // XOR keys
    for (const key of xorKeys) {
      const transformed = Buffer.alloc(testSlice.length);
      for (let i = 0; i < testSlice.length; i++) transformed[i] = testSlice[i] ^ key;
      checkAndRecord(Buffer.concat([transformed, data.slice(testSlice.length)]), `xor_${key.toString(16)}`);
    }

    // Bit rotations
    const rol = (byte, n) => ((byte << n) | (byte >>> (8 - n))) & 0xFF;
    for (const r of rotations) {
      const transformed = Buffer.alloc(testSlice.length);
      for (let i = 0; i < testSlice.length; i++) transformed[i] = rol(testSlice[i], r);
      checkAndRecord(Buffer.concat([transformed, data.slice(testSlice.length)]), `rol${r}`);
    }
  }

  // Create content-type clusters with symlinks for easier browsing
  clusterArtifacts() {
    const clustersDir = path.join(this._currentOutDir, 'clusters');
    try { fs.mkdirSync(clustersDir, { recursive: true }); } catch (_) {}
    const clusters = {
      sqlite: [],
      xml: [],
      json: [],
      terrain: [],
      unknown: []
    };

    const classify = (entry) => {
      const a = entry.analysis || {};
      if (a.isSQLite) return 'sqlite';
      if (a.hasXML) return 'xml';
      if (a.hasJSON) return 'json';
      if (a.terrainPatterns || (typeof a.heightLikePct === 'number' && a.heightLikePct > 0.5)) return 'terrain';
      return 'unknown';
    };

    for (const entry of this._currentIndex) {
      if (!entry || !entry.path) continue;
      const type = classify(entry);
      const targetDir = path.join(clustersDir, type);
      try { fs.mkdirSync(targetDir, { recursive: true }); } catch (_) {}
      const linkPath = path.join(targetDir, path.basename(entry.path));
      try { try { fs.unlinkSync(linkPath); } catch (_) {} fs.symlinkSync(entry.path, linkPath); } catch (_) {}
      clusters[type].push({ source: entry.path, link: linkPath, meta: { kind: entry.kind, method: entry.method, offset: entry.offset, size: entry.size } });
    }

    const manifest = { generatedAt: new Date().toISOString(), counts: Object.fromEntries(Object.entries(clusters).map(([k, v]) => [k, v.length])), clusters };
    const clustersPath = path.join(this._currentOutDir, 'clusters.json');
    fs.writeFileSync(clustersPath, JSON.stringify(manifest, null, 2));
    return clustersPath;
  }

  maybeExportStructuredArtifacts(data, outPath, analysis) {
    try {
      const base = path.basename(outPath, path.extname(outPath));
      const dir = path.dirname(outPath);
      // Export XML if present
      if (analysis && analysis.hasXML) {
        const firstLt = data.indexOf(0x3c);
        if (firstLt >= 0) {
          const xmlOut = path.join(dir, `${base}.xml`);
          fs.writeFileSync(xmlOut, data.slice(firstLt));
          console.log(`  Saved XML view: ${xmlOut}`);
          this._currentIndex.push({ kind: 'xml', from: outPath, path: xmlOut });
        }
      }
      // Export CSV preview for float32 grids
      if (analysis && analysis.terrainPatterns && typeof analysis.heightLikePct === 'number' && analysis.heightLikePct > 0.5) {
        const csvOut = path.join(dir, `${base}.float32_preview.csv`);
        const rows = [];
        const sampleLen = Math.min(1024, data.length - (data.length % 4));
        const colCount = 16;
        for (let i = 0; i < sampleLen; i += 4 * colCount) {
          const cols = [];
          for (let c = 0; c < colCount && (i + c * 4 + 3) < data.length; c++) {
            cols.push(data.readFloatLE(i + c * 4).toFixed(3));
          }
          if (cols.length > 0) rows.push(cols.join(','));
        }
        fs.writeFileSync(csvOut, rows.join('\n'));
        console.log(`  Saved float32 CSV preview: ${csvOut}`);
        this._currentIndex.push({ kind: 'csv_preview', from: outPath, path: csvOut, rows: rows.length });

        // Full float32 export (best-effort grid inference)
        const fullMeta = this.exportFullFloat32Grid(data, dir, base);
        if (fullMeta) {
          this._currentIndex.push({ kind: 'float32_full', from: outPath, meta: fullMeta });
        }
      }
    } catch (e) {
      console.error('  Failed exporting structured artifacts:', e.message);
    }
  }

  // Attempt to extract the largest plausible float32 region and export as 1D and 2D (if shape inferred)
  exportFullFloat32Grid(data, dir, baseName) {
    const region = this.findBestFloat32Region(data);
    if (!region || region.count < 64) return null;

    const { start, count, alignment, values, min, max, mean } = region;
    // Write raw bin of float32 region
    const rawSlice = data.slice(start, start + count * 4);
    const rawPath = path.join(dir, `${baseName}.float32.raw.bin`);
    fs.writeFileSync(rawPath, rawSlice);

    // Write 1D CSV
    const csv1dPath = path.join(dir, `${baseName}.float32_1d.csv`);
    fs.writeFileSync(csv1dPath, values.map(v => Number.isFinite(v) ? v.toFixed(6) : 'NaN').join('\n'));

    // Try to infer 2D grid dimensions
    const dims = this.inferGridDims(count);
    let csv2dPath = null;
    if (dims) {
      const { width, height } = dims;
      csv2dPath = path.join(dir, `${baseName}.float32_grid_w${width}_h${height}.csv`);
      const outRows = [];
      for (let r = 0; r < height; r++) {
        const row = values.slice(r * width, (r + 1) * width).map(v => Number.isFinite(v) ? v.toFixed(6) : 'NaN');
        outRows.push(row.join(','));
      }
      fs.writeFileSync(csv2dPath, outRows.join('\n'));
      console.log(`  Saved float32 2D grid CSV (${width}x${height}): ${csv2dPath}`);
    } else {
      console.log('  Could not infer 2D grid dims; saved 1D CSV only');
    }

    // Write metadata JSON
    const meta = { start, count, alignment, min, max, mean, rawPath, csv1dPath, csv2dPath };
    const metaPath = path.join(dir, `${baseName}.float32.meta.json`);
    fs.writeFileSync(metaPath, JSON.stringify(meta, null, 2));
    console.log(`  Saved float32 metadata: ${metaPath}`);
    return meta;
  }

  findBestFloat32Region(data) {
    const maxScan = data.length - (data.length % 4);
    let best = null;
    for (let align = 0; align < 4; align++) {
      let runStart = null;
      let runCount = 0;
      const vals = [];
      for (let i = align; i + 3 < maxScan; i += 4) {
        const v = data.readFloatLE(i);
        const isValid = Number.isFinite(v) && v > -1000 && v < 1000; // relaxed range
        if (isValid) {
          if (runStart === null) runStart = i;
          runCount++;
          vals.push(v);
        } else {
          // finalize current run
          if (runStart !== null) {
            if (!best || runCount > best.count) {
              const stat = this.computeStats(vals);
              best = { start: runStart, count: runCount, alignment: align, values: vals.slice(0), ...stat };
            }
          }
          runStart = null;
          runCount = 0;
          vals.length = 0;
        }
      }
      // tail run
      if (runStart !== null && runCount > (best ? best.count : 0)) {
        const stat = this.computeStats(vals);
        best = { start: runStart, count: runCount, alignment: align, values: vals.slice(0), ...stat };
      }
    }
    return best;
  }

  computeStats(arr) {
    let min = Infinity, max = -Infinity, sum = 0;
    for (const v of arr) { if (v < min) min = v; if (v > max) max = v; sum += v; }
    const mean = arr.length ? sum / arr.length : 0;
    return { min, max, mean };
  }

  inferGridDims(count) {
    // Prefer near-square grids and common widths
    const candidates = [32, 48, 64, 96, 128, 160, 192, 256, 320, 384];
    const options = [];
    for (const w of candidates) {
      if (count % w === 0) {
        const h = Math.floor(count / w);
        const ratio = w > h ? w / h : h / w;
        if (h >= 8 && ratio <= 2.5) options.push({ width: w, height: h, ratio });
      }
    }
    if (options.length === 0) {
      // fallback to nearest square
      const side = Math.floor(Math.sqrt(count));
      if (side >= 8) {
        const width = side;
        const height = Math.floor(count / width);
        if (width * height >= 64) return { width, height };
      }
      return null;
    }
    options.sort((a, b) => (a.ratio - b.ratio) || (b.width * b.height - a.width * a.height));
    return options[0];
  }
}

/**
 * Advanced extraction attempts for specific Valheim patterns
 */
class ValheimExtractor {
  constructor() {
    this.analyzer = new ValheimFileAnalyzer();
  }
  
  /**
   * Try various Valheim-specific extraction methods
   */
  async extractValheimData(filepath) {
    console.log(`\n=== Valheim Data Extraction: ${filepath} ===`);
    
    const buffer = fs.readFileSync(filepath);
    const results = [];
    
    // Method 1: Try XOR decryption (Valheim sometimes uses simple XOR)
    results.push(await this.tryXorDecryption(buffer, filepath));
    
    // Method 2: Try skipping headers of various sizes
    results.push(await this.tryHeaderSkipping(buffer, filepath));
    
    // Method 3: Try Unity asset bundle extraction
    results.push(await this.tryUnityExtraction(buffer, filepath));
    
    // Method 4: Try reverse byte order
    results.push(await this.tryByteOrderVariants(buffer, filepath));
    
    return results.filter(r => r.success);
  }
  
  async tryXorDecryption(buffer, filepath) {
    console.log('\n--- XOR Decryption Attempts ---');
    
    // Common XOR keys found in game files
    const xorKeys = [
      0x00, 0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80,
      0x42, 0x55, 0x69, 0x7F, 0xAA, 0xC3, 0xCC, 0xDF, 0xF0, 0xFF
    ];
    
    for (const key of xorKeys) {
      try {
        const decrypted = Buffer.alloc(buffer.length);
        for (let i = 0; i < buffer.length; i++) {
          decrypted[i] = buffer[i] ^ key;
        }
        
        // Check if result looks like a database
        if (decrypted.slice(0, 15).toString('ascii') === 'SQLite format 3') {
          const outputPath = `${filepath}.xor_${key.toString(16)}.extracted`;
          fs.writeFileSync(outputPath, decrypted);
          console.log(`✓ XOR key 0x${key.toString(16)} SUCCESS! Database found.`);
          return { success: true, method: 'xor', key, path: outputPath };
        }
      } catch (error) {
        // Continue with next key
      }
    }
    
    console.log('✗ No XOR keys worked');
    return { success: false, method: 'xor' };
  }
  
  async tryHeaderSkipping(buffer, filepath) {
    console.log('\n--- Header Skipping Attempts ---');
    
    // Try skipping various header sizes
    const headerSizes = [4, 8, 12, 16, 24, 32, 40, 48, 56, 64, 96, 128, 160, 192, 224, 256, 384, 512, 768, 1024, 2048, 4096];
    
    for (const headerSize of headerSizes) {
      if (buffer.length <= headerSize) continue;
      
      const withoutHeader = buffer.slice(headerSize);
      
      // Check if it's now a SQLite database
      if (withoutHeader.slice(0, 15).toString('ascii') === 'SQLite format 3') {
        const outputPath = `${filepath}.skip_${headerSize}.extracted`;
        fs.writeFileSync(outputPath, withoutHeader);
        console.log(`✓ Skipping ${headerSize} bytes SUCCESS! Database found.`);
        return { success: true, method: 'header_skip', headerSize, path: outputPath };
      }
      
      // Try decompressing after skipping header
      try {
        const decompressed = zlib.inflateSync(withoutHeader);
        if (decompressed.slice(0, 15).toString('ascii') === 'SQLite format 3') {
          const outputPath = `${filepath}.skip_${headerSize}_inflated.extracted`;
          fs.writeFileSync(outputPath, decompressed);
          console.log(`✓ Skip ${headerSize} + inflate SUCCESS! Database found.`);
          return { success: true, method: 'header_skip_inflate', headerSize, path: outputPath };
        }
      } catch (error) {
        // Continue
      }
    }
    
    console.log('✗ Header skipping failed');
    return { success: false, method: 'header_skip' };
  }
  
  async tryUnityExtraction(buffer, filepath) {
    console.log('\n--- Unity Asset Bundle Check ---');
    
    // Check for Unity asset bundle signature
    const unityFS = Buffer.from('UnityFS', 'ascii');
    if (buffer.indexOf(unityFS) >= 0) {
      console.log('✓ Unity asset bundle detected - requires specialized tools');
      return { success: false, method: 'unity', note: 'Unity bundle detected but not extracted' };
    }
    
    return { success: false, method: 'unity' };
  }
  
  async tryByteOrderVariants(buffer, filepath) {
    console.log('\n--- Byte Order Variants ---');
    
    // Try reversing byte order in 4-byte chunks (endianness)
    try {
      const swapped = Buffer.alloc(buffer.length);
      for (let i = 0; i < buffer.length - 3; i += 4) {
        swapped[i] = buffer[i + 3];
        swapped[i + 1] = buffer[i + 2];
        swapped[i + 2] = buffer[i + 1];
        swapped[i + 3] = buffer[i];
      }
      
      if (swapped.slice(0, 15).toString('ascii') === 'SQLite format 3') {
        const outputPath = `${filepath}.endian_swapped.extracted`;
        fs.writeFileSync(outputPath, swapped);
        console.log('✓ Endian swap SUCCESS! Database found.');
        return { success: true, method: 'endian_swap', path: outputPath };
      }
    } catch (error) {
      // Continue
    }
    
    return { success: false, method: 'endian_swap' };
  }
}

// CLI usage function
async function analyzeValheimFiles(filepaths) {
  const analyzer = new ValheimFileAnalyzer();
  const extractor = new ValheimExtractor();
  
  for (const filepath of filepaths) {
    try {
      // Basic analysis
      const analysis = analyzer.analyzeFile(filepath);
      
      // Advanced extraction attempts
      const extractions = await extractor.extractValheimData(filepath);
      
      if (extractions.length > 0) {
        console.log('\n✓ SUCCESSFUL EXTRACTIONS:');
        extractions.forEach(ext => {
          console.log(`  - ${ext.method}: ${ext.path}`);
        });
      } else {
        console.log('\n✗ No successful extractions found');
        console.log('This file may require additional reverse engineering');
      }
      
    } catch (error) {
      console.error(`Error analyzing ${filepath}:`, error.message);
    }
    
    console.log('\n' + '='.repeat(60));
  }
}

module.exports = { ValheimFileAnalyzer, ValheimExtractor, analyzeValheimFiles };

// Example usage:
if (require.main === module) {
  const files = process.argv.slice(2);
  if (files.length === 0) {
    console.log('Usage: node file_analyzer.js <path_to_seed.db> [path_to_seed.fwl]');
    console.log('Example: node file_analyzer.js ./seed.db ./seed.fwl');
    process.exit(1);
  }

  // Capture console output to per-file logs while still printing to stdout
  (async () => {
    for (const file of files) {
      const logPath = `${file}.analysis.txt`;
      const originalLog = console.log;
      const originalError = console.error;
      const writeStream = fs.createWriteStream(logPath, { flags: 'w' });

      const forward = (method, args) => {
        try { writeStream.write(args.map(a => (typeof a === 'string' ? a : JSON.stringify(a))).join(' ') + '\n'); } catch (_) {}
        try { method.apply(console, args); } catch (_) {}
      };

      console.log = (...args) => forward(originalLog, args);
      console.error = (...args) => forward(originalError, args);

      try {
        await analyzeValheimFiles([file]);
        originalLog(`Saved analysis log: ${logPath}`);
      } finally {
        console.log = originalLog;
        console.error = originalError;
        try { writeStream.end(); } catch (_) {}
      }
    }
  })();
}