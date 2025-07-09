// test_poster_generator.mjs
// Node.js test script for poster_generator.mjs (Gemini 2.0 poster generation)
//
// Usage:
//   1. Install dependencies: npm install
//   2. Place your .env file in gen-visual-backend with GEMINI_API_KEY=your_actual_api_key_here
//   3. Provide image file paths when prompted (PNG/JPEG under 5MB)
//   4. Run: npm test or npm start
//
// This script tests poster generation and saves the result as output_poster.png
//
// Additional manual test cases are described at the end of this file.

import 'dotenv/config';
import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';
import { generateResearchPoster } from './poster_generator.mjs';
import readline from 'readline';

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
    await fs.access(filePath);
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
  const extMap = { '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png' };
  return extMap[ext] || 'application/octet-stream';
}

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

const ask = (question) => new Promise(resolve => rl.question(question, resolve));

(async () => {
  try {
    // Validate API key from .env
    const apiKey = process.env.GEMINI_API_KEY;
    if (!apiKey) {
      console.error('Error: GEMINI_API_KEY not found in .env. Please configure a valid key.');
      rl.close();
      process.exit(1);
    }

    // Collect user input
    const posterType = (await ask('Enter poster type (research/club): ')).trim().toLowerCase();
    if (!['research', 'club'].includes(posterType)) throw new Error('Invalid poster type.');
    const title = (await ask('Enter event title: ')).trim();
    if (!title) throw new Error('Title is required.');
    const date = (await ask('Enter date (e.g., 2025-07-15): ')).trim();
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) throw new Error('Invalid date format (YYYY-MM-DD).');
    const time = (await ask('Enter time (e.g., 10:00 AM): ')).trim();
    if (!/\d{1,2}:\d{2}\s?(AM|PM)/i.test(time)) throw new Error('Invalid time format.');
    const venue = (await ask('Enter venue: ')).trim();
    if (!venue) throw new Error('Venue is required.');
    const department = (await ask('Enter department: ')).trim();
    if (!department) throw new Error('Department is required.');
    const numSpeakers = parseInt((await ask('Enter number of speakers (1-3): ')).trim(), 10);
    if (isNaN(numSpeakers) || numSpeakers < 1 || numSpeakers > 3) throw new Error('Number of speakers must be 1-3.');
    const speakers = [];
    for (let i = 0; i < numSpeakers; i++) {
      const name = (await ask(`Enter speaker ${i + 1} name: `)).trim();
      if (!name) throw new Error(`Speaker ${i + 1} name is required.`);
      speakers.push(name);
    }

    // Collect image paths
    const speakerImages = [];
    const speakerImagePaths = [];
    for (let i = 0; i < numSpeakers; i++) {
      const filePath = (await ask(`Enter path to speaker ${i + 1} image (e.g., images/speaker${i + 1}.jpg): `)).trim();
      speakerImagePaths.push(filePath);
      speakerImages.push(await fileFromPath(filePath, getMime(filePath)));
    }
    const logoPath = (await ask('Enter path to university logo (e.g., images/logo.jpg): ')).trim();
    const universityLogo = await fileFromPath(logoPath, getMime(logoPath));

    const input = {
      posterType,
      eventDetails: { title, date, time, venue, department, speakers },
      speakerImages,
      speakerImagePaths, // New array for full paths
      universityLogo,
      universityLogoPath: logoPath, // New property for logo path
    };

    // Run test
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
  } finally {
    rl.close();
  }
})();

// === ADDITIONAL MANUAL TEST CASES ===
//
// 1. Invalid .env (empty or missing):
//    - Remove or empty GEMINI_API_KEY in .env to test API key validation.
// 2. Corrupted image:
//    - Use a non-image or corrupted file for a speaker or logo to test validation.
// 3. Missing candidates in API response:
//    - Mock the Gemini API to return { candidates: [] } to test error handling.
// 4. Mismatched speakers and images:
//    - Provide different numbers of speaker names and images to test layout adjustment.
//
// See poster_generator.mjs for further details. 