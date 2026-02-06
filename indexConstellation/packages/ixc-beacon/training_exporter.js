/**
 * Training Data Exporter
 * VERSION: 2.0.0
 * 
 * Converts structured data into various training formats:
 * - OpenAI fine-tuning JSONL
 * - Anthropic messages format
 * - Alpaca instruction format
 * - ShareGPT conversation format
 * - Custom schema mapping
 */

export default class TrainingExporter {
  
  /**
   * Standard format templates
   */
  static FORMATS = {
    // OpenAI fine-tuning format
    openai: {
      name: 'OpenAI Fine-tuning',
      structure: {
        messages: [
          { role: 'system', content: '{system}' },
          { role: 'user', content: '{user}' },
          { role: 'assistant', content: '{assistant}' }
        ]
      }
    },
    
    // Anthropic format
    anthropic: {
      name: 'Anthropic Messages',
      structure: {
        system: '{system}',
        messages: [
          { role: 'user', content: '{user}' },
          { role: 'assistant', content: '{assistant}' }
        ]
      }
    },
    
    // Alpaca instruction format
    alpaca: {
      name: 'Alpaca Instruction',
      structure: {
        instruction: '{instruction}',
        input: '{input}',
        output: '{output}'
      }
    },
    
    // ShareGPT format
    sharegpt: {
      name: 'ShareGPT',
      structure: {
        conversations: [
          { from: 'system', value: '{system}' },
          { from: 'human', value: '{user}' },
          { from: 'gpt', value: '{assistant}' }
        ]
      }
    }
  };

  /**
   * Detect conversation structure in data
   */
  static detectStructure(data) {
    const detected = {
      hasMessages: false,
      hasConversations: false,
      hasInstructions: false,
      messagePathPattern: null,
      fields: new Set()
    };

    const scan = (obj, path = '') => {
      if (!obj || typeof obj !== 'object') return;
      
      Object.entries(obj).forEach(([key, value]) => {
        const currentPath = path ? `${path}.${key}` : key;
        detected.fields.add(key.toLowerCase());
        
        if (key === 'messages' && Array.isArray(value)) {
          detected.hasMessages = true;
          detected.messagePathPattern = currentPath;
        }
        if (key === 'conversations' && Array.isArray(value)) {
          detected.hasConversations = true;
        }
        if (['instruction', 'input', 'output'].includes(key.toLowerCase())) {
          detected.hasInstructions = true;
        }
        
        if (typeof value === 'object') {
          scan(value, currentPath);
        }
      });
    };

    // Scan first item if array, otherwise scan object
    const sample = Array.isArray(data) ? data[0] : data;
    scan(sample);

    return detected;
  }

  /**
   * Extract conversations from various data structures
   */
  static extractConversations(data, mapping = {}) {
    const conversations = [];
    const items = Array.isArray(data) ? data : [data];

    items.forEach((item, idx) => {
      try {
        const conv = this.extractSingleConversation(item, mapping);
        if (conv && conv.messages.length > 0) {
          conv.id = idx;
          conversations.push(conv);
        }
      } catch (e) {
        console.warn(`Failed to extract conversation ${idx}:`, e.message);
      }
    });

    return conversations;
  }

  /**
   * Extract a single conversation from an item
   */
  static extractSingleConversation(item, mapping) {
    const conv = { messages: [], metadata: {} };

    // Try to find messages array
    const messagesPath = mapping.messages || this.findPath(item, 'messages');
    const messages = messagesPath ? this.getByPath(item, messagesPath) : null;

    if (messages && Array.isArray(messages)) {
      messages.forEach(msg => {
        const role = msg.role || msg.from || msg.author || 'unknown';
        const content = msg.content || msg.value || msg.text || msg.message || '';
        
        if (content) {
          conv.messages.push({
            role: this.normalizeRole(role),
            content: String(content)
          });
        }
      });
    }

    // Try instruction format if no messages found
    if (conv.messages.length === 0) {
      const instruction = this.getByPath(item, mapping.instruction || 'instruction');
      const input = this.getByPath(item, mapping.input || 'input');
      const output = this.getByPath(item, mapping.output || 'output');

      if (instruction || input) {
        conv.messages.push({
          role: 'user',
          content: [instruction, input].filter(Boolean).join('\n\n')
        });
      }
      if (output) {
        conv.messages.push({
          role: 'assistant',
          content: String(output)
        });
      }
    }

    // Extract system prompt if present
    const system = this.getByPath(item, mapping.system || 'system') ||
                   this.getByPath(item, 'system_prompt');
    if (system) {
      conv.system = String(system);
    }

    // Extract metadata
    ['id', 'title', 'created_at', 'model', 'source'].forEach(field => {
      const val = this.getByPath(item, mapping[field] || field);
      if (val !== undefined) {
        conv.metadata[field] = val;
      }
    });

    return conv;
  }

  /**
   * Normalize role names
   */
  static normalizeRole(role) {
    const roleMap = {
      'human': 'user',
      'user': 'user',
      'customer': 'user',
      'gpt': 'assistant',
      'assistant': 'assistant',
      'bot': 'assistant',
      'ai': 'assistant',
      'claude': 'assistant',
      'system': 'system'
    };
    return roleMap[role.toLowerCase()] || role.toLowerCase();
  }

  /**
   * Get value by dot-notation path
   */
  static getByPath(obj, path) {
    if (!path) return undefined;
    return path.split('.').reduce((o, k) => o?.[k], obj);
  }

  /**
   * Find a path containing a key
   */
  static findPath(obj, targetKey, currentPath = '') {
    if (!obj || typeof obj !== 'object') return null;
    
    for (const [key, value] of Object.entries(obj)) {
      const newPath = currentPath ? `${currentPath}.${key}` : key;
      if (key === targetKey) return newPath;
      
      if (typeof value === 'object') {
        const found = this.findPath(value, targetKey, newPath);
        if (found) return found;
      }
    }
    return null;
  }

  /**
   * Export to OpenAI fine-tuning JSONL format
   */
  static toOpenAI(conversations, options = {}) {
    const lines = [];

    conversations.forEach(conv => {
      const messages = [];
      
      if (conv.system) {
        messages.push({ role: 'system', content: conv.system });
      }
      
      conv.messages.forEach(msg => {
        if (msg.role === 'user' || msg.role === 'assistant') {
          messages.push({ role: msg.role, content: msg.content });
        }
      });

      if (messages.length >= 2) {
        lines.push(JSON.stringify({ messages }));
      }
    });

    return lines.join('\n');
  }

  /**
   * Export to Anthropic messages format
   */
  static toAnthropic(conversations, options = {}) {
    const lines = [];

    conversations.forEach(conv => {
      const entry = {
        messages: []
      };
      
      if (conv.system) {
        entry.system = conv.system;
      }
      
      conv.messages.forEach(msg => {
        if (msg.role === 'user' || msg.role === 'assistant') {
          entry.messages.push({ role: msg.role, content: msg.content });
        }
      });

      if (entry.messages.length >= 2) {
        lines.push(JSON.stringify(entry));
      }
    });

    return lines.join('\n');
  }

  /**
   * Export to Alpaca instruction format
   */
  static toAlpaca(conversations, options = {}) {
    const lines = [];

    conversations.forEach(conv => {
      // Find user-assistant pairs
      for (let i = 0; i < conv.messages.length - 1; i++) {
        if (conv.messages[i].role === 'user' && 
            conv.messages[i + 1].role === 'assistant') {
          
          const entry = {
            instruction: conv.system || '',
            input: conv.messages[i].content,
            output: conv.messages[i + 1].content
          };
          
          lines.push(JSON.stringify(entry));
        }
      }
    });

    return lines.join('\n');
  }

  /**
   * Export to ShareGPT format
   */
  static toShareGPT(conversations, options = {}) {
    const lines = [];

    conversations.forEach(conv => {
      const entry = {
        conversations: []
      };
      
      if (conv.system) {
        entry.conversations.push({ from: 'system', value: conv.system });
      }
      
      conv.messages.forEach(msg => {
        const from = msg.role === 'user' ? 'human' : 'gpt';
        entry.conversations.push({ from, value: msg.content });
      });

      if (entry.conversations.length >= 2) {
        lines.push(JSON.stringify(entry));
      }
    });

    return lines.join('\n');
  }

  /**
   * Export to custom schema
   */
  static toCustom(conversations, schema) {
    const lines = [];

    conversations.forEach(conv => {
      const entry = {};
      
      // Apply schema mapping
      Object.entries(schema).forEach(([outputKey, sourceSpec]) => {
        if (sourceSpec === '{system}') {
          entry[outputKey] = conv.system || '';
        } else if (sourceSpec === '{user}') {
          const userMsg = conv.messages.find(m => m.role === 'user');
          entry[outputKey] = userMsg?.content || '';
        } else if (sourceSpec === '{assistant}') {
          const assistantMsg = conv.messages.find(m => m.role === 'assistant');
          entry[outputKey] = assistantMsg?.content || '';
        } else if (sourceSpec === '{messages}') {
          entry[outputKey] = conv.messages;
        } else if (sourceSpec === '{all_user}') {
          entry[outputKey] = conv.messages
            .filter(m => m.role === 'user')
            .map(m => m.content)
            .join('\n\n');
        } else if (sourceSpec === '{all_assistant}') {
          entry[outputKey] = conv.messages
            .filter(m => m.role === 'assistant')
            .map(m => m.content)
            .join('\n\n');
        } else {
          entry[outputKey] = sourceSpec;
        }
      });

      lines.push(JSON.stringify(entry));
    });

    return lines.join('\n');
  }

  /**
   * Get export statistics
   */
  static getStats(conversations) {
    let totalMessages = 0;
    let totalTokensEstimate = 0;
    let userMessages = 0;
    let assistantMessages = 0;
    let systemPrompts = 0;

    conversations.forEach(conv => {
      totalMessages += conv.messages.length;
      if (conv.system) systemPrompts++;
      
      conv.messages.forEach(msg => {
        // Rough token estimate: ~4 chars per token
        totalTokensEstimate += Math.ceil(msg.content.length / 4);
        if (msg.role === 'user') userMessages++;
        if (msg.role === 'assistant') assistantMessages++;
      });
    });

    return {
      conversations: conversations.length,
      totalMessages,
      userMessages,
      assistantMessages,
      systemPrompts,
      estimatedTokens: totalTokensEstimate
    };
  }
}
