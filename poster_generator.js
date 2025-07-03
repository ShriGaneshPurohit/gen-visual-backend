/*
poster_generator.js

AI-powered poster generation logic for research event posters (university events) using the Gemini API.

- Input: posterType, eventDetails, speakerImages (File[]), universityLogo (File)
- Output: { posterImage: string (PNG data URL), error: string|null }
- Uses HTML5 canvas for image processing (circular crop for speakers, proportional scaling for logo)
- Integrates with Gemini 2.0 free-tier API (endpoint and API key from .env)
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
    speakers: ['Dr. Alice Smith', 'Prof. Bob Lee'] // Optional: array of speaker names
  },
  speakerImages: [File, File], // 1–3 File objects (PNG/JPEG)
  universityLogo: File // PNG/JPEG File object
};

const result = await generateResearchPoster(input);
// result: { posterImage: 'data:image/png;base64,...', error: null } or { posterImage: null, error: '...' }

---

Note:
- Uses Gemini 2.0 endpoint: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
- API key is read from process.env.GEMINI_API_KEY (see .env file); fallback is 'YOUR_GEMINI_API_KEY' (replace or ensure .env is loaded).
- API key is sent as a query parameter (?key=...).
- Ensure .env is loaded in your environment (e.g., using dotenv for Node.js testing).
- This module does not include UI code.
- Only browser-compatible JS and canvas API are used.

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
  if (eventDetails.speakers && !Array.isArray(eventDetails.speakers)) {
    return 'eventDetails.speakers must be an array of strings if provided.';
  }
  if (!Array.isArray(speakerImages) || speakerImages.length < 1 || speakerImages.length > 3) {
    return 'speakerImages must be an array of 1–3 image files.';
  }
  for (const file of speakerImages) {
    if (!(file instanceof File)) return 'Each speaker image must be a File object.';
    if (!/^image\/(png|jpeg|jpg)$/i.test(file.type)) return 'Speaker images must be PNG or JPEG files.';
  }
  if (!(universityLogo instanceof File)) return 'universityLogo must be a File object.';
  if (!/^image\/(png|jpeg|jpg)$/i.test(universityLogo.type)) return 'University logo must be a PNG or JPEG file.';
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
 * Proportionally scale the university logo to fit within 100x50px (no cropping).
 * @param {File} file
 * @returns {Promise<string>} Resolves to base64 PNG data URL
 */
function processLogoImage(file) {
  return new Promise((resolve, reject) => {
    const img = new window.Image();
    img.onload = () => {
      const maxWidth = 100;
      const maxHeight = 50;
      let width = img.width;
      let height = img.height;
      // Scale proportionally
      const widthRatio = maxWidth / width;
      const heightRatio = maxHeight / height;
      const scale = Math.min(widthRatio, heightRatio, 1); // Don't upscale
      width = Math.round(width * scale);
      height = Math.round(height * scale);
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, width, height);
      ctx.drawImage(img, 0, 0, width, height);
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
 * Adds a 'Speakers' bullet if eventDetails.speakers is provided.
 * @param {Object} eventDetails
 * @param {number} numSpeakers
 * @returns {string}
 */
function buildGeminiPrompt(eventDetails, numSpeakers) {
  let prompt = `Create a high-resolution A4 poster (300 DPI, PNG) for a university research event.\n- Place the university logo (max 100x50px) in the top-right corner.\n- Center ${numSpeakers} circular speaker images (150x150px each) in a horizontal row.\n- Below the images, display event details in Arial font with a blue-and-white color scheme:\n  • Title: ${eventDetails.title}\n  • Date: ${eventDetails.date}\n  • Time: ${eventDetails.time}\n  • Venue: ${eventDetails.venue}\n  • Department: ${eventDetails.department}`;
  if (eventDetails.speakers && Array.isArray(eventDetails.speakers) && eventDetails.speakers.length > 0) {
    prompt += `\n  • Speakers: ${eventDetails.speakers.join(', ')}`;
  }
  prompt += '\n- Ensure a clean, professional layout similar to university event posters.';
  return prompt;
}

/**
 * Main function to generate a research event poster using Gemini API.
 * Includes robust error handling and image data validation.
 * @param {Object} input - { posterType, eventDetails, speakerImages, universityLogo }
 * @returns {Promise<{posterImage: string|null, error: string|null}>}
 */
export async function generateResearchPoster(input) {
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

  // 3. Process university logo (proportional scale to max 100x50px)
  let processedLogo;
  try {
    processedLogo = await processLogoImage(input.universityLogo);
  } catch (e) {
    return { posterImage: null, error: typeof e === 'string' ? e : 'University logo processing failed.' };
  }

  // 4. Validate base64 image data before sending to Gemini API
  const getBase64 = (dataUrl) => {
    if (typeof dataUrl !== 'string' || !dataUrl.startsWith('data:image/png;base64,')) {
      throw new Error('Invalid image data URL.');
    }
    const base64 = dataUrl.split(',')[1];
    if (!base64 || base64.length < 10) throw new Error('Invalid base64 image data.');
    return base64;
  };

  let logoBase64, speakerBase64Arr;
  try {
    logoBase64 = getBase64(processedLogo);
    speakerBase64Arr = processedSpeakerImages.map(getBase64);
  } catch (e) {
    return { posterImage: null, error: 'Image data validation failed: ' + (e.message || e) };
  }

  // 5. Build Gemini API prompt
  const prompt = buildGeminiPrompt(input.eventDetails, processedSpeakerImages.length);

  // 6. Prepare Gemini API request (Gemini 2.0, API key as query param)
  const apiKey = (typeof process !== 'undefined' && process.env && process.env.GEMINI_API_KEY) ? process.env.GEMINI_API_KEY : 'YOUR_GEMINI_API_KEY';
  const GEMINI_API_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

  // Prepare 'contents' array: prompt as text part, images as inlineData parts
  const contents = [
    {
      parts: [
        { text: prompt },
        { inlineData: { mimeType: 'image/png', data: logoBase64 } },
        ...speakerBase64Arr.map(base64 => ({ inlineData: { mimeType: 'image/png', data: base64 } })),
      ]
    }
  ];

  // Gemini 2.0: generationConfig
  const generationConfig = {
    temperature: 0.7,
    maxOutputTokens: 2048,
    responseMimeType: 'image/png'
  };

  let response;
  try {
    response = await fetch(GEMINI_API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ contents, generationConfig }),
    });
  } catch (err) {
    return { posterImage: null, error: 'Failed to connect to Gemini API.' };
  }

  let data;
  try {
    data = await response.json();
  } catch {
    return { posterImage: null, error: 'Invalid response from Gemini API.' };
  }

  // Defensive response parsing with detailed error messages
  if (!response.ok) {
    let msg = `Gemini API error: ${response.status}`;
    if (data && data.error && data.error.message) msg += ` - ${data.error.message}`;
    return { posterImage: null, error: msg };
  }

  try {
    const base64Data = data?.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    if (!base64Data || typeof base64Data !== 'string' || base64Data.length < 10) {
      return { posterImage: null, error: 'Gemini API did not return a valid poster image.' };
    }
    const dataUrl = `data:image/png;base64,${base64Data}`;
    return { posterImage: dataUrl, error: null };
  } catch (e) {
    return { posterImage: null, error: 'Failed to parse Gemini API response: ' + (e.message || e) };
  }
}

// --- End of poster_generator.js --- 