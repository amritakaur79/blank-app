import streamlit as st
from PIL import Image
import numpy as np
import zipfile
import io
import cv2

st.set_page_config(page_title="Shirt Mockup Generator", layout="centered")
st.title("👕 Shirt Mockup Generator – Auto-Center on Shirt")

st.markdown("""
Upload **multiple design PNGs** and **shirt templates**.  
Assign a name to each design. Each one will be applied to every shirt, automatically centered, and zipped separately.
""")

# Upload files
design_files = st.file_uploader("📌 Upload Design Images (PNG)", type=["png"], accept_multiple_files=True)
shirt_files = st.file_uploader("🎨 Upload Shirt Templates (PNG)", type=["png"], accept_multiple_files=True)

# Collect names for each design
design_names = {}
if design_files:
    st.markdown("### ✏️ Name Each Design")
    for i, file in enumerate(design_files):
        default_name = os.path.splitext(file.name)[0]
        custom_name = st.text_input(f"Name for Design {i+1} ({file.name})", value=default_name)
        design_names[file.name] = custom_name

# OpenCV shirt bounding box detection
def get_shirt_bbox(pil_image):
    """Detect shirt area in the image and return bounding box (x, y, w, h)"""
    img_cv = np.array(pil_image.convert("RGB"))[:, :, ::-1]  # Convert to BGR
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 240, 255, cv2.THRESH_BINARY_INV)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest)
        return x, y, w, h
    else:
        return None

if st.button("🚀 Generate Mockups"):
    if not (design_files and shirt_files):
        st.warning("Please upload at least one design and one shirt template.")
    else:
        zip_files_output = {}

        for design_file in design_files:
            graphic_name = design_names.get(design_file.name, "graphic")
            design = Image.open(design_file).convert("RGBA")

            # Keep original size
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
                for shirt_file in shirt_files:
                    color_name = os.path.splitext(shirt_file.name)[0]
                    shirt = Image.open(shirt_file).convert("RGBA")

                    # Detect shirt bounding box
                    bbox = get_shirt_bbox(shirt)
                    if bbox:
                        sx, sy, sw, sh = bbox
                        x = sx + (sw - design.width) // 2
                        y = sy + (sh - design.height) // 2
                    else:
                        x = (shirt.width - design.width) // 2
                        y = (shirt.height - design.height) // 2

                    # Overlay design
                    shirt_copy = shirt.copy()
                    shirt_copy.paste(design, (x, y), design)

                    output_name = f"{graphic_name}_{color_name}_tee.png"
                    img_byte_arr = io.BytesIO()
                    shirt_copy.save(img_byte_arr, format='PNG')
                    zipf.writestr(output_name, img_byte_arr.getvalue())

            zip_buffer.seek(0)
            zip_files_output[graphic_name] = zip_buffer

        st.success("✅ All mockups generated and centered!")

        for name, zip_data in zip_files_output.items():
            st.download_button(
                label=f"📦 Download {name}_mockups.zip",
                data=zip_data,
                file_name=f"{name}_mockups.zip",
                mime="application/zip"
            )
