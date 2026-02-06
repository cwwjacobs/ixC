/**
 * SQLite Exporter
 * VERSION: 2.0.0
 * 
 * Exports vault data to SQLite database using sql.js (WebAssembly)
 * Creates queryable archive of flattened JSON data
 */

export default class SQLiteExporter {
  
  static SQL_JS_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.js';
  static SQL_WASM_CDN = 'https://cdnjs.cloudflare.com/ajax/libs/sql.js/1.8.0/sql-wasm.wasm';
  
  static SQL = null;
  static initialized = false;

  /**
   * Initialize sql.js library
   */
  static async init() {
    if (this.initialized) return;

    // Load sql.js from CDN
    if (typeof initSqlJs === 'undefined') {
      await this.loadScript(this.SQL_JS_CDN);
    }

    this.SQL = await initSqlJs({
      locateFile: () => this.SQL_WASM_CDN
    });
    
    this.initialized = true;
  }

  /**
   * Load external script
   */
  static loadScript(src) {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  /**
   * Create database from vault data
   */
  static async createDatabase(vault, atlas, schema, options = {}) {
    await this.init();

    const db = new this.SQL.Database();

    // Create tables
    db.run(`
      CREATE TABLE metadata (
        key TEXT PRIMARY KEY,
        value TEXT
      );
    `);

    db.run(`
      CREATE TABLE paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT UNIQUE NOT NULL,
        value TEXT,
        type TEXT,
        pattern TEXT,
        depth INTEGER,
        cluster TEXT,
        is_outlier INTEGER DEFAULT 0
      );
    `);

    db.run(`
      CREATE TABLE clusters (
        name TEXT PRIMARY KEY,
        count INTEGER,
        types TEXT
      );
    `);

    db.run(`
      CREATE TABLE schema_patterns (
        pattern TEXT PRIMARY KEY,
        types TEXT
      );
    `);

    db.run(`
      CREATE TABLE outliers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT,
        type TEXT,
        reasons TEXT
      );
    `);

    // Create indices
    db.run(`CREATE INDEX idx_paths_cluster ON paths(cluster);`);
    db.run(`CREATE INDEX idx_paths_type ON paths(type);`);
    db.run(`CREATE INDEX idx_paths_pattern ON paths(pattern);`);
    db.run(`CREATE INDEX idx_paths_outlier ON paths(is_outlier);`);

    // Insert metadata
    const metadata = {
      format: 'ixc-sqlite',
      version: '2.0.0',
      created: new Date().toISOString(),
      source: options.filename || 'unknown',
      total_paths: Object.keys(vault).length
    };

    const metaStmt = db.prepare('INSERT INTO metadata (key, value) VALUES (?, ?)');
    Object.entries(metadata).forEach(([key, value]) => {
      metaStmt.run([key, String(value)]);
    });
    metaStmt.free();

    // Build outlier lookup
    const outlierPaths = new Set();
    const outlierReasons = {};
    (atlas?.outliers || []).forEach(o => {
      outlierPaths.add(o.path);
      outlierReasons[o.path] = o.reasons || [o.type || 'unknown'];
    });

    // Insert paths
    const pathStmt = db.prepare(`
      INSERT INTO paths (path, value, type, pattern, depth, cluster, is_outlier)
      VALUES (?, ?, ?, ?, ?, ?, ?)
    `);

    Object.entries(vault).forEach(([path, value]) => {
      const type = typeof value;
      const pattern = path.replace(/\[\d+\]/g, '[*]');
      const depth = path.split(/[.\[]/).length;
      const cluster = this.extractCluster(path);
      const isOutlier = outlierPaths.has(path) ? 1 : 0;

      pathStmt.run([
        path,
        this.serializeValue(value),
        type,
        pattern,
        depth,
        cluster,
        isOutlier
      ]);
    });
    pathStmt.free();

    // Insert clusters
    const clusterStmt = db.prepare('INSERT INTO clusters (name, count, types) VALUES (?, ?, ?)');
    Object.entries(atlas?.clusters || {}).forEach(([name, cluster]) => {
      clusterStmt.run([
        name,
        cluster.count,
        JSON.stringify(cluster.types || [])
      ]);
    });
    clusterStmt.free();

    // Insert schema patterns
    const schemaStmt = db.prepare('INSERT INTO schema_patterns (pattern, types) VALUES (?, ?)');
    Object.entries(schema || {}).forEach(([pattern, types]) => {
      schemaStmt.run([pattern, JSON.stringify(types)]);
    });
    schemaStmt.free();

    // Insert outliers
    const outlierStmt = db.prepare('INSERT INTO outliers (path, type, reasons) VALUES (?, ?, ?)');
    (atlas?.outliers || []).forEach(o => {
      outlierStmt.run([
        o.path,
        o.type || typeof vault[o.path],
        JSON.stringify(o.reasons || [o.type || 'unknown'])
      ]);
    });
    outlierStmt.free();

    return db;
  }

  /**
   * Export database to binary
   */
  static async export(vault, atlas, schema, options = {}) {
    const db = await this.createDatabase(vault, atlas, schema, options);
    const data = db.export();
    db.close();
    return new Uint8Array(data);
  }

  /**
   * Export to downloadable blob
   */
  static async toBlob(vault, atlas, schema, options = {}) {
    const data = await this.export(vault, atlas, schema, options);
    return new Blob([data], { type: 'application/x-sqlite3' });
  }

  /**
   * Serialize value for storage
   */
  static serializeValue(value) {
    if (value === null) return 'null';
    if (value === undefined) return 'undefined';
    if (typeof value === 'string') return value;
    if (typeof value === 'object') return JSON.stringify(value);
    return String(value);
  }

  /**
   * Extract cluster name from path
   */
  static extractCluster(path) {
    const match = path.match(/^root\.?([^.\[]*)/);
    return match ? match[1] || 'root' : 'root';
  }

  /**
   * Generate SQL schema documentation
   */
  static getSchemaDoc() {
    return `
-- ixC SQLite Export Schema
-- Version 2.0.0

-- Metadata table: key-value pairs for export info
-- Keys: format, version, created, source, total_paths
SELECT * FROM metadata;

-- Paths table: flattened JSON paths and values
-- Columns: id, path, value, type, pattern, depth, cluster, is_outlier
SELECT * FROM paths WHERE cluster = 'users' LIMIT 10;
SELECT * FROM paths WHERE is_outlier = 1;
SELECT DISTINCT type, COUNT(*) FROM paths GROUP BY type;

-- Clusters table: path groupings by root key
SELECT * FROM clusters ORDER BY count DESC;

-- Schema patterns table: type inference results
-- Shows what types appear at each path pattern
SELECT * FROM schema_patterns WHERE types LIKE '%string%';

-- Outliers table: detected anomalies
SELECT * FROM outliers;

-- Example queries:

-- Find all string values containing 'email'
SELECT path, value FROM paths 
WHERE type = 'string' AND value LIKE '%email%';

-- Get type distribution
SELECT type, COUNT(*) as count, 
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM paths), 2) as pct
FROM paths GROUP BY type ORDER BY count DESC;

-- Find type inconsistencies (patterns with multiple types)
SELECT pattern, types FROM schema_patterns 
WHERE types LIKE '%,%';

-- Get paths at specific depth
SELECT * FROM paths WHERE depth = 3;

-- Join outliers with their values
SELECT o.path, o.reasons, p.value, p.type
FROM outliers o
JOIN paths p ON o.path = p.path;
    `.trim();
  }
}
