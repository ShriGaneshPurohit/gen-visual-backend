/*
poster_generator.js

AI-powered poster generation logic for research event posters (university events) using the Gemini API.

- Input: posterType, eventDetails, speakerImages (File[]), universityLogo (File)
- Output: { posterImage: string (PNG URL), error: string|null }
- Uses HTML5 canvas for image processing (circular crop for speakers, resize/crop for logo)
- Integrates with Gemini free-tier API (replace endpoint and API key as needed)
- Extensible for future poster types

---

How to Use:

import { generateResearchPoster } from './poster_generator';

const input = {
  posterType: 'research',
  eventDetails: {
    title: 'AI Symposium',
    date: '2025-07-15',
    time: '10:00 AM',
    venue: 'Main Hall',
    department: 'Computer Science',
  },
  speakerImages: [File, File], // 1–3 File objects (PNG/JPEG)
  universityLogo: File // PNG/JPEG File object
};

const apiKey = 'YOUR_GEMINI_API_KEY'; // Replace with your Gemini API key

const result = await generateResearchPoster(input, apiKey);
// result: { posterImage: 'https://...', error: null } or { posterImage: null, error: '...' }

---

Note:
- Replace the Gemini API endpoint and API key with actual values from the Gemini free-tier API documentation.
- This module does not include UI code.
- Only browser-compatible JS and canvas API are used.
*/

/**
 * Validate input for research poster generation.
 * @param {Object} input
 * @returns {string|null} Error message or null if valid
 */
function validateInput(input) {
  if (!input || typeof input !== 'object') return 'Input must be an object.';
  if (input.posterType !== 'research') return 'Only research posterType is supported.';
  const { eventDetails, speakerImages, universityLogo } = input;
  if (!eventDetails || typeof eventDetails !== 'object') return 'Missing eventDetails.';
  const requiredFields = ['title', 'date', 'time', 'venue', 'department'];
  for (const field of requiredFields) {
    if (!eventDetails[field] || typeof eventDetails[field] !== 'string' || !eventDetails[field].trim()) {
      return `Missing or invalid eventDetails field: ${field}`;
    }
  }
  if (!Array.isArray(speakerImages) || speakerImages.length < 1 || speakerImages.length > 3) {
    return 'speakerImages must be an array of 1–3 image files.';
  }
  for (const file of speakerImages) {
    if (!(file instanceof File)) return 'Each speaker image must be a File object.';
    if (!/^image\/(png|jpeg|jpg)$/i.test(file.type)) return 'Speaker images must be PNG or JPEG files.';
  }
  if (!(universityLogo instanceof File)) return 'universityLogo must be a File object.';
  if (!/^image\/(png|jpeg|jpg)$/i.test(universityLogo.type)) return 'universityLogo must be a PNG or JPEG file.';
  return null;
}

/**
 * Crop an image file into a 150x150px circle using canvas.
 * @param {File} file
 * @returns {Promise<string>} Resolves to base64 PNG data URL
 */
function cropImageToCircle(file) {
  return new Promise((resolve, reject) => {
    const img = new window.Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const size = 150;
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, size, size);
      ctx.save();
      ctx.beginPath();
      ctx.arc(size / 2, size / 2, size / 2, 0, 2 * Math.PI);
      ctx.closePath();
      ctx.clip();
      // Center-crop the image
      const minDim = Math.min(img.width, img.height);
      const sx = (img.width - minDim) / 2;
      const sy = (img.height - minDim) / 2;
      ctx.drawImage(img, sx, sy, minDim, minDim, 0, 0, size, size);
      ctx.restore();
      resolve(canvas.toDataURL('image/png'));
    };
    img.onerror = () => reject('Failed to load speaker image.');
    const reader = new FileReader();
    reader.onload = e => {
      img.src = e.target.result;
    };
    reader.onerror = () => reject('Failed to read speaker image file.');
    reader.readAsDataURL(file);
  });
}

/**
 * Resize/crop the university logo to 100x50px using canvas.
 * @param {File} file
 * @returns {Promise<string>} Resolves to base64 PNG data URL
 */
function processLogoImage(file) {
  return new Promise((resolve, reject) => {
    const img = new window.Image();
    img.onload = () => {
      const width = 100;
      const height = 50;
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, width, height);
      // Center-crop or fit the logo
      const aspectRatio = img.width / img.height;
      const targetAspect = width / height;
      let sx, sy, sw, sh;
      if (aspectRatio > targetAspect) {
        // Image is wider than target: crop sides
        sh = img.height;
        sw = sh * targetAspect;
        sx = (img.width - sw) / 2;
        sy = 0;
      } else {
        // Image is taller than target: crop top/bottom
        sw = img.width;
        sh = sw / targetAspect;
        sx = 0;
        sy = (img.height - sh) / 2;
      }
      ctx.drawImage(img, sx, sy, sw, sh, 0, 0, width, height);
      resolve(canvas.toDataURL('image/png'));
    };
    img.onerror = () => reject('Failed to load university logo image.');
    const reader = new FileReader();
    reader.onload = e => {
      img.src = e.target.result;
    };
    reader.onerror = () => reject('Failed to read university logo file.');
    reader.readAsDataURL(file);
  });
}

/**
 * Generate a text prompt for the Gemini API based on event details.
 * @param {Object} eventDetails
 * @param {number} numSpeakers
 * @returns {string}
 */
function buildGeminiPrompt(eventDetails, numSpeakers) {
  return `Create a high-resolution A4 poster (300 DPI, PNG) for a university research event.\n- Place the university logo (100x50px) in the top-right corner.\n- Center ${numSpeakers} circular speaker images (150x150px each) in a horizontal row.\n- Below the images, display event details in Arial font with a blue-and-white color scheme:\n  • Title: ${eventDetails.title}\n  • Date: ${eventDetails.date}\n  • Time: ${eventDetails.time}\n  • Venue: ${eventDetails.venue}\n  • Department: ${eventDetails.department}\n- Ensure a clean, professional layout similar to university event posters.`;
}

/**
 * Main function to generate a research event poster using Gemini API.
 * @param {Object} input - { posterType, eventDetails, speakerImages, universityLogo }
 * @param {string} apiKey - Gemini API key
 * @returns {Promise<{posterImage: string|null, error: string|null}>}
 */
export async function generateResearchPoster(input, apiKey) {
  // 1. Validate input
  const error = validateInput(input);
  if (error) return { posterImage: null, error };

  // 2. Process speaker images (crop to circles)
  let processedSpeakerImages;
  try {
    processedSpeakerImages = await Promise.all(
      input.speakerImages.map(file => cropImageToCircle(file))
    );
  } catch (e) {
    return { posterImage: null, error: typeof e === 'string' ? e : 'Speaker image processing failed.' };
  }

  // 3. Process university logo (resize/crop to 100x50px)
  let processedLogo;
  try {
    processedLogo = await processLogoImage(input.universityLogo);
  } catch (e) {
    return { posterImage: null, error: typeof e === 'string' ? e : 'University logo processing failed.' };
  }

  // 4. Build Gemini API prompt
  const prompt = buildGeminiPrompt(input.eventDetails, processedSpeakerImages.length);

  // 5. Prepare Gemini API request
  // NOTE: Replace endpoint and API key with actual values from Gemini free-tier API documentation.
  const GEMINI_API_ENDPOINT = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent'; // Placeholder

  // Prepare images: logo + speaker images (as base64 data URLs)
  const images = [
    { name: 'logo', dataUrl: processedLogo },
    ...processedSpeakerImages.map((dataUrl, i) => ({ name: `speaker${i + 1}`, dataUrl })),
  ];

  // If Gemini API supports image inputs, send as JSON with prompt and images[]
  // Otherwise, include image URLs/data in the prompt as needed

  let response;
  try {
    response = await fetch(GEMINI_API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        prompt,
        images, // [{ name, dataUrl }]
        outputFormat: 'png',
        resolution: 'a4-300dpi',
      }),
    });
  } catch (err) {
    return { posterImage: null, error: 'Failed to connect to Gemini API.' };
  }

  if (!response.ok) {
    let msg = `Gemini API error: ${response.status}`;
    try {
      const errData = await response.json();
      if (errData && errData.error) msg += ` - ${errData.error}`;
    } catch {}
    return { posterImage: null, error: msg };
  }

  let data;
  try {
    data = await response.json();
  } catch {
    return { posterImage: null, error: 'Invalid response from Gemini API.' };
  }

  if (!data || !data.posterImageUrl) {
    return { posterImage: null, error: 'Gemini API did not return a poster image URL.' };
  }

  return { posterImage: data.posterImageUrl, error: null };
}

// --- End of poster_generator.js --- 