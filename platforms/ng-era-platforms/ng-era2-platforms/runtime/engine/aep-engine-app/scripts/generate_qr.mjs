/**
 * @GL-governed
 * @GL-layer: aep-engine-app
 * @GL-semantic: qr-code-generator
 * @GL-audit-trail: ../governance/GL_SEMANTIC_ANCHOR.json
 *
 * GL Unified Charter Activated
 * QR Code Generator Script
 */

import QRCode from 'qrcode';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const QR_OPTIONS = {
  width: 300,
  margin: 2,
  color: {
    dark: '#000000',
    light: '#FFFFFF'
  }
};

async function generateQRCode(text, filename) {
  try {
    const outputPath = path.join(__dirname, '..', 'public', 'qrcodes', filename);
    const dir = path.dirname(outputPath);
    
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    await QRCode.toFile(outputPath, text, QR_OPTIONS);
    console.log(`✅ QR Code generated: ${outputPath}`);
    return outputPath;
  } catch (error) {
    console.error(`❌ Error generating QR code: ${error.message}`);
    throw error;
  }
}

async function generateSampleQRCodes() {
  console.log('🎨 Generating sample QR codes...\n');
  
  try {
    await generateQRCode(
      'https://aep-engine.app/auth?token=abc123xyz789',
      'auth-sample.png'
    );
    
    await generateQRCode(
      'PAIR-DEVICE:AEP-ENGINE:UUID-550e8400-e29b-41d4-a716-446655440000',
      'pairing-sample.png'
    );
    
    await generateQRCode(
      'AUDIT-REPORT:2026-01-28:GL-AUDIT-001',
      'audit-report-sample.png'
    );
    
    console.log('\n✨ All sample QR codes generated successfully!');
    
  } catch (error) {
    console.error('❌ Error generating sample QR codes:', error);
    process.exit(1);
  }
}

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--sample') {
  generateSampleQRCodes();
} else {
  const text = args[0];
  const filename = args[1] || `qr-${Date.now()}.png`;
  
  try {
    const outputPath = await generateQRCode(text, filename);
    console.log(`\n✅ QR code saved to: ${outputPath}`);
  } catch (error) {
    console.error('\n❌ Failed to generate QR code:', error.message);
    process.exit(1);
  }
}
