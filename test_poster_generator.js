// test_poster_generator.js
// Node.js test script for poster_generator.js (Gemini 2.0 poster generation)
//
// Usage:
//   1. Install dependencies: npm install dotenv
//   2. Place your .env file in gen-visual-backend with GEMINI_API_KEY=your_actual_api_key_here
//   3. Update the image file paths below to point to real PNG/JPEG files
//   4. Run: node test_poster_generator.js (works with Node.js v16+; no flags needed)
//
// This script tests poster generation and saves the result as output_poster.png
//
// Additional manual test cases are described at the end of this file.

const dotenv = require('dotenv').config();
const fs = require('fs').promises;
const path = require('path');
const { generateResearchPoster } = require('./poster_generator.js');

// Polyfill File for Node.js (if not available)
if (typeof global.File === 'undefined') {
  global.File = class File extends Blob {
    constructor(chunks, name, opts = {}) {
      super(chunks, opts);
      this.name = name;
      this.lastModified = opts.lastModified || Date.now();
      this.type = opts.type || '';
    }
  };
}

// Helper to create a File object from disk with validation
async function fileFromPath(filePath, mimeType) {
  try {
    await fs.access(filePath); // Check if file exists
    const stats = await fs.stat(filePath);
    if (stats.size > 5 * 1024 * 1024) throw new Error('File too large (>5MB)');
    const data = await fs.readFile(filePath);
    const name = path.basename(filePath);
    return new File([data], name, { type: mimeType });
  } catch (err) {
    throw new Error(`Failed to load ${filePath}: ${err.message}`);
  }
}

// Enhanced MIME type detection
function getMime(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const extMap = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png'
  };
  return extMap[ext] || 'application/octet-stream'; // Fallback for unknown types
}

(async () => {
  try {
    // Validate API key from .env
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      console.error('Error: GEMINI_API_KEY not found in .env. Please configure a valid key.');
      process.exit(1);
    }

    // === SETUP: Update these paths to your actual image files ===
    const speaker1Path = 'gen-visual-backend/images/speaker1.jpg'; // <-- Replace with real path
    const speaker2Path = 'gen-visual-backend/images/speaker2.jpg'; // <-- Replace with real path
    const logoPath = 'gen-visual-backend/images/logo.jpg';         // <-- Replace with real path

    // === PREPARE INPUT ===
    const speakerImages = [
      await fileFromPath(speaker1Path, getMime(speaker1Path)),
      await fileFromPath(speaker2Path, getMime(speaker2Path)),
    ];
    const universityLogo = await fileFromPath(logoPath, getMime(logoPath));

    const input = {
      posterType: 'research',
      eventDetails: {
        title: 'AI Symposium',
        date: '2025-07-15',
        time: '10:00 AM',
        venue: 'Main Hall',
        department: 'Computer Science',
        speakers: ['Dr. Alice Smith', 'Prof. Bob Lee'], // Optional
      },
      speakerImages,
      universityLogo,
    };

    // === RUN TEST ===
    console.log('Generating research poster...');
    const result = await generateResearchPoster(input);
    if (result.error) {
      console.error('Poster generation failed:', result.error);
    } else {
      const base64 = result.posterImage.split(',')[1];
      if (!base64 || base64.length < 100) throw new Error('Invalid poster data');
      await fs.writeFile('output_poster.png', Buffer.from(base64, 'base64'));
      console.log('Poster saved as output_poster.png');
    }
  } catch (err) {
    console.error('Unexpected error during test:', err.message);
  }
})();

// === ADDITIONAL MANUAL TEST CASES ===
//
// 1. Invalid .env (empty or missing):
//    - Remove or empty GEMINI_API_KEY in .env to test API key validation and error handling.
// 2. Corrupted image:
//    - Use a non-image or corrupted file (e.g., text file) for a speaker or logo to test image validation in poster_generator.js.
// 3. Missing candidates in API response:
//    - Mock the Gemini API (e.g., with Postman) to return a response without candidates (e.g., { candidates: [] }) to test error handling.
// 4. Mismatched speakers and images:
//    - Provide more/less speaker names than images (e.g., 1 speaker, 2 images) to test prompt and warning handling.
//
// See poster_generator.js for further details on input validation and error handling. 