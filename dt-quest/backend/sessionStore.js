/**
 * File-based session persistence for DT-QUEST
 * Stores session data as JSON files in a sessions/ directory
 */
const fs = require('fs');
const path = require('path');

const SESSIONS_DIR = path.join(__dirname, 'sessions');

// Ensure sessions directory exists
if (!fs.existsSync(SESSIONS_DIR)) {
  fs.mkdirSync(SESSIONS_DIR, { recursive: true });
}

/**
 * Save session data to a JSON file
 * @param {string} sessionId 
 * @param {object} sessionData - full session object (data, mapping, pipelineResults, etc.)
 */
function saveSession(sessionId, sessionData) {
  try {
    const filepath = path.join(SESSIONS_DIR, `${sessionId}.json`);
    // Clone and strip large arrays for storage efficiency
    const toStore = {
      sessionId,
      filename: sessionData.filename,
      columns: sessionData.columns,
      mapping: sessionData.mapping || {},
      domainId: sessionData.domainId || 'its-v2x',
      pipelineResults: sessionData.pipelineResults || {},
      appliedCorrections: sessionData.appliedCorrections || null,
      customEquations: sessionData.customEquations || [],
      createdAt: sessionData.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      rowCount: sessionData.data ? sessionData.data.length : 0,
      // Store full data so sessions survive server restarts
      data: sessionData.data || [],
      // Store cleaned data sample too
      cleanedDataSample: sessionData.cleanedData ? sessionData.cleanedData.slice(0, 100) : [],
      cleanedColumns: sessionData.cleanedColumns || null,
    };
    fs.writeFileSync(filepath, JSON.stringify(toStore, null, 2));
    return true;
  } catch (err) {
    console.error(`Failed to save session ${sessionId}:`, err.message);
    return false;
  }
}

/**
 * Load session metadata (without full data) for listing
 * @returns {Array} list of session summaries
 */
function listSessions() {
  try {
    const files = fs.readdirSync(SESSIONS_DIR).filter(f => f.endsWith('.json'));
    return files.map(f => {
      try {
        const data = JSON.parse(fs.readFileSync(path.join(SESSIONS_DIR, f), 'utf8'));
        return {
          sessionId: data.sessionId,
          filename: data.filename,
          domainId: data.domainId,
          rowCount: data.rowCount,
          columnCount: data.columns ? data.columns.length : 0,
          mappedParams: Object.keys(data.mapping || {}).length,
          pipelineSteps: Object.keys(data.pipelineResults || {}).length,
          createdAt: data.createdAt,
          updatedAt: data.updatedAt,
        };
      } catch (e) {
        return null;
      }
    }).filter(Boolean);
  } catch (err) {
    console.error('Failed to list sessions:', err.message);
    return [];
  }
}

/**
 * Load a full session from file
 * @param {string} sessionId
 * @returns {object|null}
 */
function loadSession(sessionId) {
  try {
    const filepath = path.join(SESSIONS_DIR, `${sessionId}.json`);
    if (!fs.existsSync(filepath)) return null;
    return JSON.parse(fs.readFileSync(filepath, 'utf8'));
  } catch (err) {
    console.error(`Failed to load session ${sessionId}:`, err.message);
    return null;
  }
}

/**
 * Delete a session file
 * @param {string} sessionId
 */
function deleteSession(sessionId) {
  try {
    const filepath = path.join(SESSIONS_DIR, `${sessionId}.json`);
    if (fs.existsSync(filepath)) {
      fs.unlinkSync(filepath);
      return true;
    }
    return false;
  } catch (err) {
    console.error(`Failed to delete session ${sessionId}:`, err.message);
    return false;
  }
}

module.exports = { saveSession, loadSession, listSessions, deleteSession };
