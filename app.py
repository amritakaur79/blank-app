import streamlit as st
from PIL import Image
import os
import zipfile
import io

st.set_page_config(page_title="Shirt Mockup Generator", layout="centered")
st.title("👕 Shirt Mockup Generator")

st.markdown("""
Upload your **graphic PNG**, choose **shirt templates** (each in a different color), and give your design a name.

The app will overlay your design on each shirt and let you download all results in one zip file.
""")

# File upload
design_file = st.file_uploader("📌 Upload Design (PNG)", type=["png"])
shirt_files = st.file_uploader("🎨 Upload Shirt Templates (PNG)", type=["png"], accept_multiple_files=True)
graphic_name = st.text_input("📝 Enter the Graphic Name (e.g. `sunsetlogo`)")

if st.button("🚀 Generate Mockups"):
    if not (design_file and shirt_files and graphic_name):
        st.warning("Please upload a design, shirt templates, and enter a name.")
    else:
        # Load design
        design = Image.open(design_file).convert("RGBA")
        design = design.resize((400, 400))  # Resize to fit shirt

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
            for shirt_file in shirt_files:
                color_name = os.path.splitext(shirt_file.name)[0]
                shirt = Image.open(shirt_file).convert("RGBA")

                # Center design on shirt
                x = (shirt.width - design.width) // 2
                y = (shirt.height - design.height) // 2
                shirt.paste(design, (x, y), design)

                # Save to memory
                output_name = f"{graphic_name}_{color_name}_tee.png"
                img_byte_arr = io.BytesIO()
                shirt.save(img_byte_arr, format='PNG')
                zipf.writestr(output_name, img_byte_arr.getvalue())

        zip_buffer.seek(0)
        st.success("✅ Mockups generated successfully!")
        st.download_button("📦 Download All as ZIP", zip_buffer, file_name="shirt_mockups.zip", mime="application/zip")
