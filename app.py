import streamlit as st
from PIL import Image
import numpy as np
import zipfile
import io
import cv2
import os

st.set_page_config(page_title="Shirt Mockup Generator", layout="centered")
st.title("👕 Shirt Mockup Generator – Auto-Center and Auto-Rotate on Shirt")

st.markdown("""
Upload **multiple design PNGs** and **shirt templates**.  
Each design will be applied to every shirt, automatically **centered** and **rotated** to match the shirt's orientation.
""")

# --- Sidebar Controls ---
PADDING_RATIO = st.sidebar.slider("Padding Ratio", 0.1, 1.0, 0.45, 0.05)
vertical_shift_pct = st.sidebar.slider("Vertical Offset % (up = negative)", -20, 20, -7, 1)
angle_manual_default = st.sidebar.slider("Rotate Graphic (°)", -45, 45, 0, 1)

# Optional angle override per shirt
angle_overrides = {}
if shirt_files:
    st.sidebar.markdown("#### 🧭 Per-Shirt Angle Overrides")
    for file in shirt_files:
        name = file.name
        angle_overrides[name] = st.sidebar.slider(f"{name}", -45, 45, angle_manual_default, 1)

# --- Session Setup ---
if "zip_files_output" not in st.session_state:
    st.session_state.zip_files_output = {}
if "design_files" not in st.session_state:
    st.session_state.design_files = None
if "design_names" not in st.session_state:
    st.session_state.design_names = {}

# --- Upload Section ---
uploaded_files = st.file_uploader(
    "📌 Upload Design Images (PNG)", type=["png"], accept_multiple_files=True
)
if uploaded_files != st.session_state.design_files:
    st.session_state.design_files = uploaded_files
    st.session_state.design_names = {}

shirt_files = st.file_uploader(
    "🎨 Upload Shirt Templates (PNG)", type=["png"], accept_multiple_files=True
)

# --- Clear Design Button ---
if st.button("🔄 Start Over (Clear Generated Mockups)"):
    for key in ["design_files", "design_names", "zip_files_output"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- Design Naming ---
if st.session_state.design_files:
    st.markdown("### ✏️ Name Each Design")
    for i, file in enumerate(st.session_state.design_files):
        default_name = os.path.splitext(file.name)[0]
        custom_name = st.text_input(
            f"Name for Design {i+1} ({file.name})", 
            value=st.session_state.design_names.get(file.name, default_name),
            key=f"name_input_{file.name}"
        )
        st.session_state.design_names[file.name] = custom_name

# --- Bounding Box Detection ---
def get_shirt_bbox_and_angle(pil_image):
    img_cv = np.array(pil_image.convert("RGB"))[:, :, ::-1]
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        return (x, y, w, h), 0
    return None, 0

# --- Generate Mockups ---
preview_shown = False
if st.button("🚀 Generate Mockups") and st.session_state.design_files:
    if not (st.session_state.design_files and shirt_files):
        st.warning("Please upload at least one design and one shirt template.")
    else:
        for design_file in st.session_state.design_files:
            graphic_name = st.session_state.design_names.get(design_file.name, "graphic")
            design = Image.open(design_file).convert("RGBA")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
                for shirt_file in shirt_files:
                    color_name = os.path.splitext(shirt_file.name)[0]
                    shirt = Image.open(shirt_file).convert("RGBA")

                    bbox, angle = get_shirt_bbox_and_angle(shirt)
                    if bbox:
                        sx, sy, sw, sh = bbox
                        scale = min(sw / design.width, sh / design.height, 1.0) * PADDING_RATIO
                        new_width = int(design.width * scale)
                        new_height = int(design.height * scale)
                        resized_design = design.resize((new_width, new_height))

                        angle_for_this = angle_overrides.get(shirt_file.name, angle_manual_default)
                        rotated_design = resized_design.rotate(angle_for_this, expand=True)

                        y_offset = int(sh * vertical_shift_pct / 100)
                        x = sx + (sw - rotated_design.width) // 2
                        y = sy + (sh - rotated_design.height) // 2 + y_offset
                    else:
                        rotated_design = design
                        x = (shirt.width - design.width) // 2
                        y = (shirt.height - design.height) // 2

                    shirt_copy = shirt.copy()
                    shirt_copy.paste(rotated_design, (x, y), rotated_design)

                    if not preview_shown:
                        st.image(shirt_copy, caption=f"Preview: {graphic_name} on {color_name}", use_column_width=True)
                        preview_shown = True

                    output_name = f"{graphic_name}_{color_name}_tee.png"
                    img_byte_arr = io.BytesIO()
                    shirt_copy.save(img_byte_arr, format='PNG')
                    img_byte_arr.seek(0)
                    zipf.writestr(output_name, img_byte_arr.getvalue())

            zip_buffer.seek(0)
            st.session_state.zip_files_output[graphic_name] = zip_buffer

        st.success("✅ All mockups generated, centered, and aligned!")

# --- Download Buttons ---
if st.session_state.zip_files_output:
    for name, zip_data in st.session_state.zip_files_output.items():
        st.download_button(
            label=f"📦 Download {name}_mockups.zip",
            data=zip_data,
            file_name=f"{name}_mockups.zip",
            mime="application/zip",
            key=f"download_{name}"
        )
