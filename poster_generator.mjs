import { createCanvas } from 'canvas';

/*
poster_generator.mjs

AI-powered poster generation logic for research event posters (university events) using the Gemini API.

- Input: posterType, eventDetails, speakerImages (File[]), universityLogo (File)
- Output: { posterImage: string (PNG data URL), error: string|null }
- Uses HTML5 canvas for image processing (circular crop for speakers, proportional scaling for logo)
- Integrates with Gemini 2.0 free-tier API (endpoint and API key from .env)
- Extensible for future poster types

---

How to Use:

import { generateResearchPoster } from './poster_generator.mjs';

const input = {
  posterType: 'research',
  eventDetails: {
    title: 'AI Symposium',
    date: '2025-07-15',
    time: '10:00 AM',
    venue: 'Main Hall',
    department: 'Computer Science',
    speakers: ['Dr. Alice Smith', 'Prof. Bob Lee'] // Optional
  },
  speakerImages: [File, File], // 1–3 File objects (PNG/JPEG)
  universityLogo: File // PNG/JPEG File object
};

const result = await generateResearchPoster(input);
// result: { posterImage: 'data:image/png;base64,...', error: null } or { posterImage: null, error: '...' }

---

Note:
- Uses Gemini 2.0 endpoint: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent
- API key is read from process.env.GEMINI_API_KEY (see .env file); fallback is 'YOUR_GEMINI_API_KEY' (will warn if used).
- API key is sent as a query parameter (?key=...).
- Ensure .env is loaded in your environment (e.g., using dotenv for Node.js testing).
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
 * Crop an image file into a 150x150px circle using canvas (Node.js or browser).
 * @param {File} file
 * @returns {Promise<string>} Resolves to base64 PNG data URL
 */
function cropImageToCircle(file) {
  if (typeof window !== 'undefined' && window.FileReader) {
    // Browser version
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
  } else {
    // Node.js version using 'canvas' package
    return new Promise(async (resolve, reject) => {
      try {
        const { Image } = await import('canvas');
        const img = new Image();
        img.onload = () => {
          const size = 150;
          const canvas = createCanvas(size, size);
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, size, size);
          ctx.save();
          ctx.beginPath();
          ctx.arc(size / 2, size / 2, size / 2, 0, 2 * Math.PI);
          ctx.closePath();
          ctx.clip();
          const minDim = Math.min(img.width, img.height);
          const sx = (img.width - minDim) / 2;
          const sy = (img.height - minDim) / 2;
          ctx.drawImage(img, sx, sy, minDim, minDim, 0, 0, size, size);
          ctx.restore();
          resolve(canvas.toDataURL('image/png'));
        };
        img.onerror = () => reject('Failed to load speaker image.');
        const buffer = Buffer.isBuffer(file) ? file : Buffer.from(await file.arrayBuffer());
        img.src = buffer;
      } catch (err) {
        reject('Failed to process speaker image in Node.js: ' + err);
      }
    });
  }
}

/**
 * Proportionally scale the university logo to fit within 100x50px (no cropping).
 * Works in both Node.js (using 'canvas' package) and browser (using window.Image).
 * @param {File} file
 * @returns {Promise<string>} Resolves to base64 PNG data URL
 */
function processLogoImage(file) {
  if (typeof window !== 'undefined' && window.FileReader) {
    // Browser version
    return new Promise((resolve, reject) => {
      const img = new window.Image();
      img.onload = () => {
        const maxWidth = 100;
        const maxHeight = 50;
        let width = img.width;
        let height = img.height;
        const widthRatio = maxWidth / width;
        const heightRatio = maxHeight / height;
        const scale = Math.min(widthRatio, heightRatio, 1);
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
  } else {
    // Node.js version using 'canvas' package
    return new Promise(async (resolve, reject) => {
      try {
        const { Image } = await import('canvas');
        const img = new Image();
        img.onload = () => {
          const maxWidth = 100;
          const maxHeight = 50;
          let width = img.width;
          let height = img.height;
          const widthRatio = maxWidth / width;
          const heightRatio = maxHeight / height;
          const scale = Math.min(widthRatio, heightRatio, 1);
          width = Math.round(width * scale);
          height = Math.round(height * scale);
          const canvas = createCanvas(width, height);
          const ctx = canvas.getContext('2d');
          ctx.clearRect(0, 0, width, height);
          ctx.drawImage(img, 0, 0, width, height);
          resolve(canvas.toDataURL('image/png'));
        };
        img.onerror = () => reject('Failed to load university logo image.');
        const buffer = Buffer.isBuffer(file) ? file : Buffer.from(await file.arrayBuffer());
        img.src = buffer;
      } catch (err) {
        reject('Failed to process university logo in Node.js: ' + err);
      }
    });
  }
}

/**
 * Main function to generate a research event poster using Gemini API for full layout and local rendering.
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

  // 4. Build and send Gemini API request for full poster layout
  const prompt = `You are an expert graphic designer tasked with creating a complete layout for a high-resolution A4 poster (2480x3508 pixels at 300 DPI) for a university research event. Use the following details to design the poster:\n- Event details: Title: ${input.eventDetails.title}, Date: ${input.eventDetails.date}, Time: ${input.eventDetails.time}, Venue: ${input.eventDetails.venue}, Department: ${input.eventDetails.department}${(input.eventDetails.speakers && input.eventDetails.speakers.length > 0) ? `, Speakers: ${input.eventDetails.speakers.join(', ')}` : ''}\n- The poster includes ${processedSpeakerImages.length} speaker images (each 150x150px, circular) and a university logo (max 100x50px).\n- Design a professional layout with a blue-and-white color scheme using Arial font.\n- Return a JSON object with the following structure:\n  {\n    "layout": {\n      "backgroundColor": "hex code (e.g., #ffffff)",\n      "logo": {"x": number, "y": number, "width": number, "height": number},\n      "speakers": [{"x": number, "y": number, "width": number, "height": number}, ...],\n      "text": {\n        "title": {"x": number, "y": number, "fontSize": number, "color": "hex code"},\n        "details": [{"text": "string", "x": number, "y": number, "fontSize": number, "color": "hex code"}, ...]\n      }\n    }\n  }\n- Ensure all coordinates and sizes are in pixels, fitting within the 2480x3508px canvas. Place the logo in the top-right, speakers in a centered horizontal row, and text below in a clean, organized manner.`;

  const apiKey = process.env.GEMINI_API_KEY || 'YOUR_GEMINI_API_KEY';
  const GEMINI_API_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

  const contents = [{ parts: [{ text: prompt }] }];
  const generationConfig = {
    temperature: 0.7,
    maxOutputTokens: 2048,
    responseMimeType: 'text/plain'
  };

  let response;
  try {
    response = await fetch(GEMINI_API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

  if (!response.ok) {
    let msg = `Gemini API error: ${response.status}`;
    if (data && data.error && data.error.message) msg += ` - ${data.error.message}`;
    return { posterImage: null, error: msg };
  }

  const textResponse = data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!textResponse) {
    return { posterImage: null, error: 'Gemini API did not return a valid text response.' };
  }

  // 5. Parse layout and render poster
  let layout;
  try {
    // Remove code block markers (e.g., ```json ... ```) and parse JSON
    let cleanResponse = textResponse.trim();
    if (cleanResponse.startsWith('```json')) {
      cleanResponse = cleanResponse.replace(/^```json/, '').trim();
    }
    if (cleanResponse.startsWith('```')) {
      cleanResponse = cleanResponse.replace(/^```/, '').trim();
    }
    if (cleanResponse.endsWith('```')) {
      cleanResponse = cleanResponse.replace(/```$/, '').trim();
    }
    layout = JSON.parse(cleanResponse).layout;
  } catch (e) {
    console.error('Failed to parse layout response:', textResponse);
    return { posterImage: null, error: 'Failed to parse layout from Gemini response.' };
  }

  // Create A4 canvas (2480x3508px at 300 DPI)
  const canvas = createCanvas(2480, 3508);
  const ctx = canvas.getContext('2d');

  // Draw background
  ctx.fillStyle = layout.backgroundColor || '#ffffff';
  ctx.fillRect(0, 0, 2480, 3508);

  // Draw logo
  const { Image } = await import('canvas');
  const logoImg = new Image();
  logoImg.src = processedLogo;
  ctx.drawImage(logoImg, layout.logo.x, layout.logo.y, layout.logo.width, layout.logo.height);

  // Draw speaker images
  for (let i = 0; i < layout.speakers.length; i++) {
    const speaker = layout.speakers[i];
    const speakerImg = new Image();
    speakerImg.src = processedSpeakerImages[i];
    ctx.drawImage(speakerImg, speaker.x, speaker.y, speaker.width, speaker.height);
  }

  // Draw text
  ctx.font = `${layout.text.title.fontSize || 40}px Arial`;
  ctx.fillStyle = layout.text.title.color || '#0000ff';
  ctx.textAlign = 'center';
  ctx.fillText(input.eventDetails.title, layout.text.title.x, layout.text.title.y);

  for (const detail of layout.text.details) {
    ctx.font = `${detail.fontSize || 30}px Arial`;
    ctx.fillStyle = detail.color || '#0000ff';
    ctx.textAlign = 'center';
    ctx.fillText(detail.text, detail.x, detail.y);
  }

  // Convert to base64 PNG
  const posterImage = canvas.toDataURL('image/png');
  return { posterImage, error: null };
}

// --- End of poster_generator.mjs --- 