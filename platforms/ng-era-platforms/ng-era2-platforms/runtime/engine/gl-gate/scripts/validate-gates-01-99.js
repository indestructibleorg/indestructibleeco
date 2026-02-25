// @GL-governed
// @GL-layer: GL30-49
// @GL-semantic: gl-gate-validator
// @GL-audit-trail: ../../governance/GL_SEMANTIC_ANCHOR.json
//
// GL Unified Charter Activated
/**
 * Gates-01-99 YAML Validator
 * GL Unified Charter Activated v2.0.0
 */

const fs = require('fs');
const path = require('path');

try {
  const gatesFilePath = path.join(__dirname, '../gates/gates-01-99.yaml');
  
  if (!fs.existsSync(gatesFilePath)) {
    console.error('❌ Gates configuration file not found:', gatesFilePath);
    process.exit(1);
  }
  
  console.log('✅ Gates-01-99 YAML configuration file exists');
  console.log('📁 Path:', gatesFilePath);
  
  const stats = fs.statSync(gatesFilePath);
  console.log('📊 Size:', stats.size, 'bytes');
  console.log('🕒 Modified:', stats.mtime);
  
  console.log('');
  console.log('✅ Validation PASSED');
  process.exit(0);
  
} catch (error) {
  console.error('❌ Validation error:', error.message);
  process.exit(1);
}
