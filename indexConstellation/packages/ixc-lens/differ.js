/**
 * ixC Diff Engine
 * VERSION: 2.0.0
 * 
 * Compare two vaults/monoliths and produce a detailed diff
 */

export default class DiffEngine {
  
  /**
   * Compare two vaults and produce a diff report
   */
  static diff(vaultA, vaultB, options = {}) {
    const keysA = new Set(Object.keys(vaultA));
    const keysB = new Set(Object.keys(vaultB));

    const diff = {
      added: [],      // In B but not A
      removed: [],    // In A but not B
      changed: [],    // In both but different values
      unchanged: [],  // In both with same values
      summary: {
        totalA: keysA.size,
        totalB: keysB.size,
        addedCount: 0,
        removedCount: 0,
        changedCount: 0,
        unchangedCount: 0
      }
    };

    // Find added and unchanged/changed
    keysB.forEach(key => {
      if (!keysA.has(key)) {
        diff.added.push({
          path: key,
          value: vaultB[key]
        });
      } else {
        const valA = vaultA[key];
        const valB = vaultB[key];
        
        if (DiffEngine.valuesEqual(valA, valB)) {
          if (!options.excludeUnchanged) {
            diff.unchanged.push({ path: key, value: valA });
          }
        } else {
          diff.changed.push({
            path: key,
            oldValue: valA,
            newValue: valB,
            typeChanged: typeof valA !== typeof valB
          });
        }
      }
    });

    // Find removed
    keysA.forEach(key => {
      if (!keysB.has(key)) {
        diff.removed.push({
          path: key,
          value: vaultA[key]
        });
      }
    });

    // Update summary
    diff.summary.addedCount = diff.added.length;
    diff.summary.removedCount = diff.removed.length;
    diff.summary.changedCount = diff.changed.length;
    diff.summary.unchangedCount = options.excludeUnchanged 
      ? keysA.size - diff.removed.length - diff.changed.length
      : diff.unchanged.length;

    return diff;
  }

  /**
   * Deep equality check
   */
  static valuesEqual(a, b) {
    if (a === b) return true;
    if (typeof a !== typeof b) return false;
    
    // Handle special string markers
    if (typeof a === 'string' && typeof b === 'string') {
      return a === b;
    }

    return JSON.stringify(a) === JSON.stringify(b);
  }

  /**
   * Generate a human-readable diff report
   */
  static formatReport(diff) {
    const lines = [];
    
    lines.push('═══════════════════════════════════════');
    lines.push('  ixC DIFF REPORT');
    lines.push('═══════════════════════════════════════');
    lines.push('');
    lines.push(`Summary:`);
    lines.push(`  Source A: ${diff.summary.totalA} entries`);
    lines.push(`  Source B: ${diff.summary.totalB} entries`);
    lines.push(`  Added:    +${diff.summary.addedCount}`);
    lines.push(`  Removed:  -${diff.summary.removedCount}`);
    lines.push(`  Changed:  ~${diff.summary.changedCount}`);
    lines.push(`  Same:     =${diff.summary.unchangedCount}`);
    lines.push('');

    if (diff.added.length > 0) {
      lines.push('───────────────────────────────────────');
      lines.push('ADDED (+)');
      lines.push('───────────────────────────────────────');
      diff.added.forEach(item => {
        lines.push(`  + ${item.path}`);
        lines.push(`    → ${DiffEngine.truncate(String(item.value), 60)}`);
      });
      lines.push('');
    }

    if (diff.removed.length > 0) {
      lines.push('───────────────────────────────────────');
      lines.push('REMOVED (-)');
      lines.push('───────────────────────────────────────');
      diff.removed.forEach(item => {
        lines.push(`  - ${item.path}`);
        lines.push(`    → ${DiffEngine.truncate(String(item.value), 60)}`);
      });
      lines.push('');
    }

    if (diff.changed.length > 0) {
      lines.push('───────────────────────────────────────');
      lines.push('CHANGED (~)');
      lines.push('───────────────────────────────────────');
      diff.changed.forEach(item => {
        lines.push(`  ~ ${item.path}`);
        lines.push(`    old: ${DiffEngine.truncate(String(item.oldValue), 50)}`);
        lines.push(`    new: ${DiffEngine.truncate(String(item.newValue), 50)}`);
        if (item.typeChanged) {
          lines.push(`    ⚠ TYPE CHANGED`);
        }
      });
      lines.push('');
    }

    lines.push('═══════════════════════════════════════');
    
    return lines.join('\n');
  }

  /**
   * Truncate string for display
   */
  static truncate(str, maxLen) {
    if (str.length <= maxLen) return str;
    return str.slice(0, maxLen - 3) + '...';
  }

  /**
   * Group diff results by cluster/root key
   */
  static groupByCluster(diff) {
    const grouped = {
      added: {},
      removed: {},
      changed: {}
    };

    const extractRoot = (path) => {
      const match = path.match(/^root\.?([^.\[]*)/);
      return match ? match[1] || 'root' : 'root';
    };

    diff.added.forEach(item => {
      const root = extractRoot(item.path);
      if (!grouped.added[root]) grouped.added[root] = [];
      grouped.added[root].push(item);
    });

    diff.removed.forEach(item => {
      const root = extractRoot(item.path);
      if (!grouped.removed[root]) grouped.removed[root] = [];
      grouped.removed[root].push(item);
    });

    diff.changed.forEach(item => {
      const root = extractRoot(item.path);
      if (!grouped.changed[root]) grouped.changed[root] = [];
      grouped.changed[root].push(item);
    });

    return grouped;
  }

  /**
   * Filter diff to only show paths matching a pattern
   */
  static filter(diff, pattern) {
    const regex = new RegExp(
      '^' + pattern
        .replace(/[.+^${}()|[\]\\]/g, '\\$&')
        .replace(/\*/g, '.*')
        .replace(/\?/g, '.')
      + '$'
    );

    return {
      added: diff.added.filter(i => regex.test(i.path)),
      removed: diff.removed.filter(i => regex.test(i.path)),
      changed: diff.changed.filter(i => regex.test(i.path)),
      unchanged: diff.unchanged?.filter(i => regex.test(i.path)) || [],
      summary: diff.summary  // Keep original summary
    };
  }
}
