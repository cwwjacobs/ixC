/**
 * ixC Monolith Format Handler
 * VERSION: 2.0.0
 * 
 * Handles the .ixc monolith format:
 * - Generation from audit results
 * - Parsing/validation
 * - Reconstitution to original structure
 */

export default class MonolithHandler {
  
  /**
   * Generate a monolith package from audit results
   */
  static generate(auditResult, options = {}) {
    const { vault, schema, atlas, provenance } = auditResult;

    // Integrity check
    const vaultSize = Object.keys(vault).length;
    const expectedSize = atlas.terminalNodes;
    
    if (vaultSize !== expectedSize) {
      console.warn(`[Monolith] Integrity warning: vault has ${vaultSize} entries, expected ${expectedSize}`);
    }

    const monolith = {
      header: {
        format: 'ixc-monolith',
        version: '2.0.0',
        created: new Date().toISOString(),
        provenance,
        atlas: {
          ...atlas,
          // Remove paths array from clusters to reduce size
          clusters: Object.fromEntries(
            Object.entries(atlas.clusters).map(([key, cluster]) => [
              key,
              { count: cluster.count, types: cluster.types }
            ])
          )
        },
        schema,
        integrity: {
          vaultEntries: vaultSize,
          checksum: MonolithHandler.checksum(vault)
        }
      },
      body: vault
    };

    // Optional compression info
    if (options.includeStats) {
      monolith.header.stats = {
        originalPaths: vaultSize,
        schemaPatterns: Object.keys(schema).length,
        clusterCount: Object.keys(atlas.clusters).length,
        outlierCount: atlas.outliers.length
      };
    }

    return monolith;
  }

  /**
   * Serialize monolith to string
   */
  static serialize(monolith, pretty = true) {
    return JSON.stringify(monolith, null, pretty ? 2 : 0);
  }

  /**
   * Parse a monolith from string
   */
  static parse(text) {
    try {
      const monolith = JSON.parse(text);
      
      // Validate structure
      if (!monolith.header || !monolith.body) {
        return { success: false, error: 'Invalid monolith structure: missing header or body' };
      }

      if (monolith.header.format !== 'ixc-monolith') {
        return { success: false, error: `Unknown format: ${monolith.header.format}` };
      }

      // Verify integrity
      const currentChecksum = MonolithHandler.checksum(monolith.body);
      if (monolith.header.integrity?.checksum !== currentChecksum) {
        console.warn('[Monolith] Checksum mismatch - data may have been modified');
      }

      return {
        success: true,
        monolith,
        header: monolith.header,
        vault: monolith.body,
        schema: monolith.header.schema,
        atlas: monolith.header.atlas
      };

    } catch (err) {
      return { success: false, error: `Parse error: ${err.message}` };
    }
  }

  /**
   * Reconstitute original nested structure from vault
   */
  static reconstitute(vault) {
    const result = {};

    Object.entries(vault).forEach(([path, value]) => {
      // Skip special markers
      if (typeof value === 'string' && value.startsWith('[') && value.endsWith(']')) {
        return;
      }

      MonolithHandler.setNestedValue(result, path, value);
    });

    return result.root;
  }

  /**
   * Set a value at a nested path
   */
  static setNestedValue(obj, path, value) {
    const segments = MonolithHandler.parsePath(path);
    let current = obj;

    for (let i = 0; i < segments.length - 1; i++) {
      const segment = segments[i];
      const nextSegment = segments[i + 1];
      
      if (current[segment] === undefined) {
        // Determine if next level should be array or object
        current[segment] = typeof nextSegment === 'number' ? [] : {};
      }
      
      current = current[segment];
    }

    const lastSegment = segments[segments.length - 1];
    current[lastSegment] = value;
  }

  /**
   * Parse a path string into segments
   * Handles both dot notation and bracket notation
   */
  static parsePath(path) {
    const segments = [];
    let current = '';
    let inBracket = false;

    for (let i = 0; i < path.length; i++) {
      const char = path[i];

      if (char === '[') {
        if (current) {
          segments.push(current);
          current = '';
        }
        inBracket = true;
      } else if (char === ']') {
        if (current) {
          // Try to parse as number for array indices
          const num = parseInt(current, 10);
          segments.push(isNaN(num) ? current : num);
          current = '';
        }
        inBracket = false;
      } else if (char === '.' && !inBracket) {
        if (current) {
          segments.push(current);
          current = '';
        }
      } else {
        current += char;
      }
    }

    if (current) {
      segments.push(current);
    }

    return segments;
  }

  /**
   * Simple checksum for integrity verification
   */
  static checksum(vault) {
    const keys = Object.keys(vault).sort();
    let hash = 0;
    
    keys.forEach(key => {
      const value = String(vault[key]);
      for (let i = 0; i < key.length + value.length; i++) {
        const char = i < key.length 
          ? key.charCodeAt(i) 
          : value.charCodeAt(i - key.length);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
      }
    });

    return 'c' + Math.abs(hash).toString(16);
  }

  /**
   * Export vault to CSV format
   */
  static toCSV(vault) {
    const lines = ['path,type,value'];
    
    Object.entries(vault).forEach(([path, value]) => {
      const type = typeof value;
      const escapedValue = String(value)
        .replace(/"/g, '""')
        .replace(/\n/g, '\\n');
      lines.push(`"${path}","${type}","${escapedValue}"`);
    });

    return lines.join('\n');
  }

  /**
   * Export vault to NDJSON format
   */
  static toNDJSON(vault) {
    return Object.entries(vault)
      .map(([path, value]) => JSON.stringify({ path, value, type: typeof value }))
      .join('\n');
  }

  /**
   * Export vault to NDJSON with full metadata
   */
  static toNDJSONFull(vault, atlas, schema) {
    const lines = [];
    
    // Header line with metadata
    lines.push(JSON.stringify({
      _meta: true,
      format: 'ixc-ndjson',
      version: '2.0.0',
      timestamp: new Date().toISOString(),
      totalPaths: Object.keys(vault).length,
      clusters: Object.keys(atlas?.clusters || {}).length
    }));

    // Data lines
    Object.entries(vault).forEach(([path, value]) => {
      const pathPattern = path.replace(/\[\d+\]/g, '[*]');
      lines.push(JSON.stringify({
        path,
        value,
        type: typeof value,
        pattern: pathPattern,
        types: schema?.[pathPattern] || [typeof value]
      }));
    });

    return lines.join('\n');
  }

  /**
   * Get vault statistics
   */
  static getStats(vault) {
    const stats = {
      totalEntries: Object.keys(vault).length,
      byType: {},
      maxPathDepth: 0,
      avgPathDepth: 0,
      pathLengths: []
    };

    let totalDepth = 0;

    Object.entries(vault).forEach(([path, value]) => {
      const type = typeof value;
      stats.byType[type] = (stats.byType[type] || 0) + 1;

      const depth = path.split(/[.\[]/).length;
      stats.pathLengths.push(depth);
      totalDepth += depth;
      
      if (depth > stats.maxPathDepth) {
        stats.maxPathDepth = depth;
      }
    });

    stats.avgPathDepth = totalDepth / stats.totalEntries;

    return stats;
  }
}
