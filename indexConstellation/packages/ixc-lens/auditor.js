/**
 * ixC_iA - Individual Audit Engine
 * VERSION: 2.0.0
 * STATUS: Production-Ready
 * 
 * CAPABILITIES:
 * - 100% exhaustion with cycle detection
 * - Depth limiting for pathological inputs
 * - Schema inference with type tracking
 * - Smart outlier detection
 * - Cluster grouping by root keys
 * - Provenance tracking
 */

export default class IxC_iA_Auditor {
  constructor(config = {}) {
    // Configuration with sensible defaults
    this.config = {
      maxDepth: config.maxDepth ?? 2000,
      maskIdentities: config.maskIdentities ?? false,
      captureUndefined: config.captureUndefined ?? true,
      skipNulls: config.skipNulls ?? false,
      ...config
    };

    // Reset state
    this.reset();
  }

  /**
   * Reset all internal state for fresh audit
   */
  reset() {
    this.vault = {};              // Flat path → value map
    this.schema = {};             // Path pattern → Set of types
    this.seen = new WeakSet();    // Cycle detection
    
    this.atlas = {
      nodesExhausted: 0,
      terminalNodes: 0,
      maxDepthReached: 0,
      clusters: {},
      outliers: [],
      typeDistribution: {},
      timestamp: new Date().toISOString()
    };

    this.provenance = {
      source: null,
      hash: null,
      byteSize: null,
      processor: {
        name: 'ixC_iA',
        version: '2.0.0'
      },
      configSnapshot: { ...this.config },
      startTime: null,
      endTime: null
    };
  }

  /**
   * CORE: Exhaustion Engine
   * Recursively drills until every node is spent
   */
  audit(node, path = 'root', depth = 0, onProgress = null) {
    this.atlas.nodesExhausted++;

    // Progress callback for large datasets
    if (onProgress && this.atlas.nodesExhausted % 1000 === 0) {
      onProgress({
        exhausted: this.atlas.nodesExhausted,
        currentPath: path,
        depth
      });
    }

    // Depth limit check
    if (depth > this.config.maxDepth) {
      this.vault[path] = '[MAX_DEPTH_EXCEEDED]';
      this.atlas.maxDepthReached++;
      this.atlas.outliers.push({
        path,
        type: 'depth_exceeded',
        depth
      });
      return;
    }

    // Handle objects and arrays
    if (node !== null && typeof node === 'object') {
      // Cycle detection
      if (this.seen.has(node)) {
        this.vault[path] = '[CIRCULAR_REF]';
        this.atlas.outliers.push({
          path,
          type: 'circular_reference'
        });
        return;
      }
      this.seen.add(node);

      const isArray = Array.isArray(node);
      const keys = Object.keys(node);

      // Empty container handling
      if (keys.length === 0) {
        this.vault[path] = isArray ? '[]' : '{}';
        this.atlas.terminalNodes++;
        this.recordType(path, isArray ? 'empty_array' : 'empty_object');
        return;
      }

      // Recurse into children
      keys.forEach(key => {
        const nextPath = isArray ? `${path}[${key}]` : `${path}.${key}`;
        this.audit(node[key], nextPath, depth + 1, onProgress);
      });

    } else {
      // Terminal node reached
      this.processTerminal(path, node);
    }
  }

  /**
   * Process terminal (leaf) nodes
   */
  processTerminal(path, value) {
    const type = this.getType(value);
    
    // Skip nulls if configured
    if (this.config.skipNulls && value === null) {
      return;
    }

    // Skip undefined unless configured to capture
    if (!this.config.captureUndefined && value === undefined) {
      return;
    }

    // Apply masking if configured
    const processedValue = this.config.maskIdentities 
      ? this.mask(value) 
      : value;

    this.vault[path] = processedValue;
    this.atlas.terminalNodes++;
    
    // Record type for schema inference
    this.recordType(path, type);
    
    // Smart outlier detection
    this.detectOutliers(path, value, type);
  }

  /**
   * Record type for schema inference
   * Normalizes array indices to [*] for pattern matching
   */
  recordType(path, type) {
    const pathPattern = path.replace(/\[\d+\]/g, '[*]');
    
    if (!this.schema[pathPattern]) {
      this.schema[pathPattern] = new Set();
    }
    this.schema[pathPattern].add(type);

    // Track type distribution
    this.atlas.typeDistribution[type] = (this.atlas.typeDistribution[type] || 0) + 1;
  }

  /**
   * Smart outlier detection
   */
  detectOutliers(path, value, type) {
    const outlier = { path, reasons: [] };

    // Sparse value detection
    if (value === null || value === undefined || value === '') {
      outlier.reasons.push('sparse');
    }

    // Suspiciously long strings
    if (typeof value === 'string' && value.length > 10000) {
      outlier.reasons.push('long_string');
    }

    // Very short paths (unusual structure)
    if (path.split('.').length <= 2 && !path.includes('[')) {
      outlier.reasons.push('shallow');
    }

    // Type inconsistency (check if this path pattern has multiple types)
    const pathPattern = path.replace(/\[\d+\]/g, '[*]');
    if (this.schema[pathPattern] && this.schema[pathPattern].size > 1) {
      outlier.reasons.push('type_inconsistent');
    }

    if (outlier.reasons.length > 0) {
      outlier.type = type;
      this.atlas.outliers.push(outlier);
    }
  }

  /**
   * Get precise type of value
   */
  getType(value) {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (Array.isArray(value)) return 'array';
    return typeof value;
  }

  /**
   * Identity masking for PII protection
   */
  mask(value) {
    if (typeof value === 'string') {
      // Preserve type info while masking
      if (value.includes('@')) return '[MASKED_EMAIL]';
      if (/^\d{3}-\d{2}-\d{4}$/.test(value)) return '[MASKED_SSN]';
      if (/^\d{10,}$/.test(value)) return '[MASKED_PHONE]';
      return '[MASKED_STRING]';
    }
    return value;
  }

  /**
   * Build clusters by grouping paths under common roots
   */
  buildClusters() {
    Object.keys(this.vault).forEach(path => {
      // Extract root key (first segment after 'root')
      const segments = path.replace(/^\root\.?/, '').split(/[.\[]/);
      const root = segments[0] || 'root';
      
      if (!this.atlas.clusters[root]) {
        this.atlas.clusters[root] = {
          paths: [],
          count: 0,
          types: new Set()
        };
      }
      
      this.atlas.clusters[root].paths.push(path);
      this.atlas.clusters[root].count++;
      
      const type = this.getType(this.vault[path]);
      this.atlas.clusters[root].types.add(type);
    });

    // Convert Sets to arrays for JSON serialization
    Object.values(this.atlas.clusters).forEach(cluster => {
      cluster.types = Array.from(cluster.types);
    });
  }

  /**
   * Run full audit with provenance tracking
   */
  run(data, sourceInfo = {}, onProgress = null) {
    this.reset();
    
    this.provenance.startTime = new Date().toISOString();
    this.provenance.source = sourceInfo.filename || 'unknown';
    this.provenance.byteSize = sourceInfo.byteSize || null;
    
    // Compute hash if raw text provided
    if (sourceInfo.rawText) {
      this.provenance.hash = this.simpleHash(sourceInfo.rawText);
    }

    // Run exhaustion
    this.audit(data, 'root', 0, onProgress);
    
    // Build clusters
    this.buildClusters();
    
    // Finalize provenance
    this.provenance.endTime = new Date().toISOString();
    
    // Convert schema Sets to arrays
    const schemaSerializable = {};
    Object.entries(this.schema).forEach(([pattern, types]) => {
      schemaSerializable[pattern] = Array.from(types);
    });

    return {
      success: true,
      vault: this.vault,
      schema: schemaSerializable,
      atlas: this.atlas,
      provenance: this.provenance
    };
  }

  /**
   * Simple hash for provenance (not cryptographic)
   */
  simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return 'h' + Math.abs(hash).toString(16);
  }

  /**
   * Query the vault with glob-like patterns
   */
  query(pattern) {
    const regex = new RegExp(
      '^' + pattern
        .replace(/[.+^${}()|[\]\\]/g, '\\$&')
        .replace(/\*/g, '.*')
        .replace(/\?/g, '.')
      + '$'
    );

    const results = {};
    Object.entries(this.vault).forEach(([path, value]) => {
      if (regex.test(path)) {
        results[path] = value;
      }
    });
    return results;
  }

  /**
   * Get paths with type inconsistencies
   */
  getTypeInconsistencies() {
    const inconsistent = {};
    Object.entries(this.schema).forEach(([pattern, types]) => {
      if (types.length > 1) {
        inconsistent[pattern] = types;
      }
    });
    return inconsistent;
  }
}

/**
 * Configuration presets
 */
export const PRESETS = {
  paranoid: { 
    maxDepth: 200, 
    maskIdentities: true 
  },
  performance: { 
    maxDepth: 1000, 
    skipNulls: true,
    captureUndefined: false
  },
  forensic: { 
    maxDepth: 5000, 
    captureUndefined: true,
    skipNulls: false
  },
  unlimited: {
    maxDepth: Infinity,
    captureUndefined: true,
    skipNulls: false
  }
};
