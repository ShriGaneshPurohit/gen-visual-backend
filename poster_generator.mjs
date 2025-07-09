import { createCanvas, Image, loadImage } from 'canvas';
import fs from 'fs';
import path from 'path';

/*
poster_generator.mjs

AI-powered poster generation logic for university event posters using the Gemini API.

- Input: posterType, eventDetails, speakerImages (File[]), speakerImagePaths (string[]), universityLogo (File), universityLogoPath (string)
- Output: { posterImage: string (PNG data URL), error: string|null }
- Uses HTML5 canvas for image processing (circular crop for speakers, proportional scaling for logo)
- Integrates with Gemini 2.0 free-tier API (endpoint and API key from .env)
- Extensible for future poster types (e.g., add new types by updating validTypes in validateInput)
- Requires `canvas` package installed (npm install canvas).
*/

/**
 * Validate input for poster generation.
 * @param {Object} input
 * @returns {string|null} Error message or null if valid
 */
function validateInput(input) {
  if (!input || typeof input !== 'object') return 'Input must be an object.';
  const validTypes = ['research', 'club'];
  if (!validTypes.includes(input.posterType)) return `Poster type must be one of ${validTypes.join(', ')}.`;
  const { eventDetails, speakerImages, speakerImagePaths, universityLogo, universityLogoPath } = input;
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
  if (!Array.isArray(speakerImagePaths) || speakerImagePaths.length !== speakerImages.length) {
    return 'speakerImagePaths must be an array matching the number of speakerImages.';
  }
  for (const file of speakerImages) {
    if (!(file instanceof File)) return 'Each speaker image must be a File object.';
    if (!/^image\/(png|jpeg|jpg)$/i.test(file.type)) return 'Speaker images must be PNG or JPEG files.';
  }
  if (!(universityLogo instanceof File)) return 'universityLogo must be a File object.';
  if (!/^image\/(png|jpeg|jpg)$/i.test(universityLogo.type)) return 'University logo must be a PNG or JPEG file.';
  if (typeof universityLogoPath !== 'string' || !universityLogoPath.trim()) {
    return 'universityLogoPath must be a non-empty string.';
  }
  return null;
}

/**
 * Crop an image file into a 150x150px circle using canvas.
 * @param {File} file
 * @param {string} filePath - Full path to the file
 * @returns {Promise<string>} Resolves to base64 PNG data URL
 */
function cropImageToCircle(file, filePath) {
  return new Promise((resolve, reject) => {
    const canvas = createCanvas(150, 150);
    const ctx = canvas.getContext('2d');

    // Stream-based loading for debug and error handling
    const stream = fs.createReadStream(filePath);
    let loaded = false;
    stream.on('error', (err) => {
      console.error('Stream error for', file.name, ':', err.message);
      reject(`Failed to stream ${file.name}: ${err.message}`);
    });
    loadImage(filePath).then((image) => {
      loaded = true;
      console.log('Image loaded:', file.name, image.width, 'x', image.height);
      ctx.clearRect(0, 0, 150, 150);
      ctx.save();
      ctx.beginPath();
      ctx.arc(75, 75, 75, 0, 2 * Math.PI);
      ctx.closePath();
      ctx.clip();
      const minDim = Math.min(image.width, image.height);
      const sx = (image.width - minDim) / 2;
      const sy = (image.height - minDim) / 2;
      ctx.drawImage(image, sx, sy, minDim, minDim, 0, 0, 150, 150);
      ctx.restore();
      console.log('Image cropped:', file.name);
      resolve(canvas.toDataURL('image/png'));
    }).catch((err) => {
      if (!loaded) {
        console.error('Image load error for', file.name, ':', err.message);
        reject(`Failed to load ${file.name}: ${err.message}`);
      }
    });
  });
}

/**
 * Proportionally scale the university logo to fit within 100x50px (no cropping).
 * @param {File} file
 * @param {string} filePath - Full path to the file
 * @returns {Promise<string>} Resolves to base64 PNG data URL
 */
function processLogoImage(file, filePath) {
  return new Promise((resolve, reject) => {
    const canvas = createCanvas(100, 50);
    const ctx = canvas.getContext('2d');

    // Stream-based loading for debug and error handling
    const stream = fs.createReadStream(filePath);
    let loaded = false;
    stream.on('error', (err) => {
      console.error('Stream error for', file.name, ':', err.message);
      reject(`Failed to stream ${file.name}: ${err.message}`);
    });
    loadImage(filePath).then((image) => {
      loaded = true;
      console.log('Logo loaded:', file.name, image.width, 'x', image.height);
      const maxWidth = 100;
      const maxHeight = 50;
      let width = image.width;
      let height = image.height;
      const widthRatio = maxWidth / width;
      const heightRatio = maxHeight / height;
      const scale = Math.min(widthRatio, heightRatio, 1);
      width = Math.round(width * scale);
      height = Math.round(height * scale);
      canvas.width = width;
      canvas.height = height;
      ctx.clearRect(0, 0, width, height);
      ctx.drawImage(image, 0, 0, width, height);
      console.log('Logo scaled:', file.name);
      resolve(canvas.toDataURL('image/png'));
    }).catch((err) => {
      if (!loaded) {
        console.error('Image load error for', file.name, ':', err.message);
        reject(`Failed to load ${file.name}: ${err.message}`);
      }
    });
  });
}

/**
 * Main function to generate a poster using Gemini API for full layout and local rendering.
 * @param {Object} input - { posterType, eventDetails, speakerImages, speakerImagePaths, universityLogo, universityLogoPath }
 * @returns {Promise<{posterImage: string|null, error: string|null}>}
 */
export async function generateResearchPoster(input) {
  // 1. Validate input
  const error = validateInput(input);
  if (error) return { posterImage: null, error };

  // 2. Process speaker images (crop to circles)
  let processedSpeakerImages;
  try {
    console.log('Processing speaker images:', input.speakerImages.length);
    processedSpeakerImages = await Promise.all(
      input.speakerImages.map((file, index) => cropImageToCircle(file, input.speakerImagePaths[index]))
    );
    console.log('Speaker images processed:', processedSpeakerImages.length);
  } catch (e) {
    console.error('Speaker image processing error:', e.message);
    return { posterImage: null, error: typeof e === 'string' ? e : 'Speaker image processing failed.' };
  }

  // 3. Process university logo (proportional scale to max 100x50px)
  let processedLogo;
  try {
    console.log('Processing university logo:', input.universityLogo.name);
    processedLogo = await processLogoImage(input.universityLogo, input.universityLogoPath);
    console.log('University logo processed');
  } catch (e) {
    console.error('University logo processing error:', e.message);
    return { posterImage: null, error: typeof e === 'string' ? e : 'University logo processing failed.' };
  }

  // 4. Build and send Gemini API request for full poster layout
  const prompt = `You are an expert graphic designer tasked with creating a complete layout for a high-resolution A4 poster (2480x3508 pixels at 300 DPI) for a university ${input.posterType} event. Use the following details to design the poster:\n- Event details: Title: ${input.eventDetails.title}, Date: ${input.eventDetails.date}, Time: ${input.eventDetails.time}, Venue: ${input.eventDetails.venue}, Department: ${input.eventDetails.department}${(input.eventDetails.speakers && input.eventDetails.speakers.length > 0) ? `, Speakers: ${input.eventDetails.speakers.join(', ')}` : ''}\n- The poster includes ${processedSpeakerImages.length} speaker images (each 150x150px, circular) and a university logo (max 100x50px).\n- Design a professional layout with a blue-and-white color scheme using Arial, Helvetica, or Times New Roman fonts (bold for titles, regular for details). Ensure balanced spacing, avoid overlapping, use a grid-based layout with 100px margins on all sides, and place the logo in the top-right, speakers in a centered horizontal row, and text below in a clean, organized manner. Tailor the design to the ${input.posterType} type (e.g., research posters emphasize academic details, club posters highlight event visuals).\n- Return a JSON object with the following structure:\n  {\n    "layout": {\n      "backgroundColor": "hex code (e.g., #ffffff)",\n      "logo": {"x": number, "y": number, "width": number, "height": number},\n      "speakers": [{"x": number, "y": number, "width": number, "height": number}, ...],\n      "text": {\n        "title": {"x": number, "y": number, "fontSize": number, "color": "hex code", "fontWeight": "bold or normal"},\n        "details": [{"text": "string", "x": number, "y": number, "fontSize": number, "color": "hex code", "fontWeight": "bold or normal"}, ...]\n      }\n    }\n  }\n- Ensure all coordinates and sizes are in pixels, fitting within the 2480x3508px canvas.`;

  const apiKey = process.env.GEMINI_API_KEY || 'YOUR_GEMINI_API_KEY';
  if (apiKey === 'YOUR_GEMINI_API_KEY') console.warn('Using fallback API key; configure .env for production.');
  const GEMINI_API_ENDPOINT = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`;

  const contents = [{ parts: [{ text: prompt }] }];
  const generationConfig = {
    temperature: 0.7,
    maxOutputTokens: 2048,
    responseMimeType: 'text/plain'
  };

  let response;
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000); // 10-second timeout
    response = await fetch(GEMINI_API_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents, generationConfig }),
      signal: controller.signal
    });
    clearTimeout(timeout);
  } catch (err) {
    return { posterImage: null, error: `Failed to connect to Gemini API: ${err.message}` };
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
    let cleanResponse = textResponse.replace(/```json\n([\s\S]*?)```/g, '$1').trim();
    if (!cleanResponse) cleanResponse = textResponse.replace(/```([\s\S]*?)```/g, '$1').trim(); // Fallback
    layout = JSON.parse(cleanResponse).layout;
  } catch (e) {
    console.error('Failed to parse layout response:', textResponse, 'Error:', e.message);
    return { posterImage: null, error: 'Failed to parse layout from Gemini response.' };
  }

  // Create A4 canvas (2480x3508px at 300 DPI)
  const canvas = createCanvas(2480, 3508);
  const ctx = canvas.getContext('2d');

  // Draw background
  ctx.fillStyle = layout.backgroundColor || '#ffffff';
  ctx.fillRect(0, 0, 2480, 3508);

  // Draw logo
  const logoImg = await loadImage(processedLogo);
  ctx.drawImage(logoImg, layout.logo.x, layout.logo.y, layout.logo.width, layout.logo.height);

  // Draw speaker images
  for (let i = 0; i < layout.speakers.length; i++) {
    const speaker = layout.speakers[i];
    const speakerImg = await loadImage(processedSpeakerImages[i]);
    ctx.drawImage(speakerImg, speaker.x, speaker.y, speaker.width, speaker.height);
  }

  // Draw text
  ctx.font = `${layout.text.title.fontWeight || 'bold'} ${layout.text.title.fontSize || 40}px Arial`;
  ctx.fillStyle = layout.text.title.color || '#0000ff';
  ctx.textAlign = 'center';
  ctx.fillText(input.eventDetails.title, layout.text.title.x, layout.text.title.y);

  ctx.font = `${layout.text.details[0].fontWeight || 'normal'} ${layout.text.details[0].fontSize || 30}px Arial`;
  layout.text.details.forEach(detail => {
    ctx.fillStyle = detail.color || '#0000ff';
    ctx.fillText(detail.text, detail.x, detail.y);
  });

  // Convert to base64 PNG
  const posterImage = canvas.toDataURL('image/png');
  return { posterImage, error: null };
} 