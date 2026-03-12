/**
 * DT-QUEST Domain Registry
 * Auto-discovers domain configs from the domains/ directory,
 * parses YAML, validates, and exports accessor functions.
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

const DOMAINS_DIR = path.join(__dirname);
const SKIP_DIRS = ['_template', 'node_modules'];

// Loaded domain configs keyed by domain id
const domains = {};

/**
 * Load all domain configs on startup
 */
function loadDomains() {
  const entries = fs.readdirSync(DOMAINS_DIR, { withFileTypes: true });

  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    if (SKIP_DIRS.includes(entry.name)) continue;
    if (entry.name.startsWith('.')) continue;

    const configPath = path.join(DOMAINS_DIR, entry.name, 'config.yaml');
    if (!fs.existsSync(configPath)) {
      console.warn(`[Registry] Skipping '${entry.name}' — no config.yaml found`);
      continue;
    }

    try {
      const raw = fs.readFileSync(configPath, 'utf-8');
      const config = yaml.load(raw);

      // Validate required fields
      if (!config.domain || !config.domain.id || !config.domain.name) {
        console.warn(`[Registry] Skipping '${entry.name}' — missing domain.id or domain.name`);
        continue;
      }
      if (!config.parameters || !Array.isArray(config.parameters) || config.parameters.length === 0) {
        console.warn(`[Registry] Skipping '${entry.name}' — no parameters defined`);
        continue;
      }

      // Normalize: build a parameter_ranges object (key → {min, max, unit}) for backward compat
      const parameterRanges = {};
      for (const p of config.parameters) {
        if (p.range) {
          const rangeMin = (p.range.min === null || p.range.min === undefined) ? -Infinity : p.range.min;
          const rangeMax = (p.range.max === null || p.range.max === undefined) ? Infinity : p.range.max;
          parameterRanges[p.key] = {
            min: rangeMin,
            max: rangeMax,
            unit: p.unit || ''
          };
        }
      }
      config._parameterRanges = parameterRanges;

      // Normalize: ensure optional arrays/objects exist
      config.presets = config.presets || {};
      config.consistency_rules = config.consistency_rules || [];
      config.unit_detection = config.unit_detection || [];
      config.reference_models = config.reference_models || [];
      config.readiness_weights = config.readiness_weights || {
        range_compliance: 0.25,
        cross_param_consistency: 0.25,
        no_placeholders: 0.15,
        completeness: 0.25,
        unit_consistency: 0.10
      };

      domains[config.domain.id] = config;
      console.log(`[Registry] ✓ Loaded domain: ${config.domain.name} (${config.domain.id}) — ${config.parameters.length} params, ${Object.keys(config.presets).length} presets`);

    } catch (err) {
      console.error(`[Registry] ✗ Failed to load '${entry.name}':`, err.message);
    }
  }

  const count = Object.keys(domains).length;
  console.log(`[Registry] ${count} domain(s) loaded.`);
  if (count === 0) {
    console.warn('[Registry] WARNING: No domains loaded. The pipeline will not work.');
  }
}

// Load on module init
loadDomains();

/**
 * Get all loaded domains (summary for API listing)
 */
function getAllDomains() {
  return Object.values(domains).map(d => ({
    id: d.domain.id,
    name: d.domain.name,
    description: d.domain.description || '',
    icon: d.domain.icon || '📦',
    version: d.domain.version || '1.0.0',
    parameter_count: d.parameters.length,
    preset_count: Object.keys(d.presets).length,
    has_reference_models: d.reference_models.length > 0,
    has_consistency_rules: d.consistency_rules.length > 0
  }));
}

/**
 * Get a specific domain config by id
 * @param {string} domainId
 * @returns {object|null} full domain config or null if not found
 */
function getDomain(domainId) {
  return domains[domainId] || null;
}

/**
 * Get the default domain (its-v2x, or the first loaded)
 * @returns {object|null}
 */
function getDefaultDomain() {
  return domains['its-v2x'] || Object.values(domains)[0] || null;
}

/**
 * Get parameter ranges in the legacy format { key: { min, max, unit } }
 * for backward compatibility with existing pipeline code
 * @param {string} domainId
 * @returns {object}
 */
function getParameterRanges(domainId) {
  const domain = getDomain(domainId) || getDefaultDomain();
  return domain ? domain._parameterRanges : {};
}

/**
 * Get presets for a domain
 * @param {string} domainId
 * @returns {object}
 */
function getPresets(domainId) {
  const domain = getDomain(domainId) || getDefaultDomain();
  return domain ? domain.presets : {};
}

module.exports = {
  getAllDomains,
  getDomain,
  getDefaultDomain,
  getParameterRanges,
  getPresets,
  loadDomains  // exposed for testing / hot-reload
};
