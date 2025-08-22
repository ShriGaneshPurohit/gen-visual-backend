from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
import shutil
import os
from script1 import generate_poster
from script2 import populate_poster_slots

app = FastAPI()

@app.post("/full-process")
async def full_process(
    base_template_path: str = Form(...),
    mapping_file_path: str = Form(...),
    font_file_path: str = Form(...),
    logo_paths: str = Form(...),
    venue_icon_file_path: str = Form(...),
    calendar_icon_file_path: str = Form(...),
    poster_text_content: str = Form(...),
    custom_font_sizes: str = Form(...),
    face_image_paths: str = Form(...),
    custom_colors: str = Form(None)
):
    import json
    text_content = json.loads(poster_text_content)
    font_sizes = json.loads(custom_font_sizes)
    # handle empty strings gracefully
    logo_list = [p for p in (logo_paths or "").split(",") if p.strip()]
    faces = [p for p in (face_image_paths or "").split(",") if p.strip()]
    color_dict = json.loads(custom_colors) if custom_colors else None

    # Step 1: Generate poster
    temp_poster = "generated_poster.png"
    poster_path = generate_poster(
        base_image_path=base_template_path,
        text_content=text_content,
        output_filename=temp_poster,
        mapping_json_path=mapping_file_path,
        font_path=font_file_path,
        logo_paths=logo_list,
        logo_scale=2.0,
        font_sizes=font_sizes,
        venue_icon_path=venue_icon_file_path,
        calendar_icon_path=calendar_icon_file_path,
        icon_scale=2.0,
        custom_colors=color_dict
    )

    # Step 2: Populate slots
    final_path = populate_poster_slots(
        template_path=poster_path,
        face_image_paths=faces,
        output_filename="final_poster.png",
        slots_json_path="slot_cache.json"
    )

    # If populate_poster_slots failed or returned None, fall back to the poster generated earlier.
    if not final_path:
        final_path = poster_path

    return FileResponse(final_path, media_type="image/png")