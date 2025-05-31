import streamlit as st
from PIL import Image
import os
import zipfile
import io

st.set_page_config(page_title="Shirt Mockup Generator", layout="centered")
st.title("👕 Shirt Mockup Generator – Multiple Graphics with Custom Names")

st.markdown("""
Upload **multiple design PNGs** and **shirt templates**.  
Assign a name to each design. Each one will be applied to every shirt and zipped separately.
""")

# Upload graphics and shirt templates
design_files = st.file_uploader("📌 Upload Design Images (PNG)", type=["png"], accept_multiple_files=True)
shirt_files = st.file_uploader("🎨 Upload Shirt Templates (PNG)", type=["png"], accept_multiple_files=True)

# Collect custom names for each uploaded design
design_names = {}

if design_files:
    st.markdown("### ✏️ Name Each Design")
    for i, file in enumerate(design_files):
        default_name = os.path.splitext(file.name)[0]
        design_name = st.text_input(f"Name for Design {i+1} ({file.name})", value=default_name)
        design_names[file.name] = design_name

if st.button("🚀 Generate Mockups"):
    if not (design_files and shirt_files):
        st.warning("Please upload at least one design and one shirt template.")
    else:
        zip_files_output = {}

        for design_file in design_files:
            # Get custom name
            graphic_name = design_names.get(design_file.name, "graphic")

            design = Image.open(design_file).convert("RGBA")
            design = design.resize((400, 400))  # Resize to fit shirt

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED) as zipf:
                for shirt_file in shirt_files:
                    color_name = os.path.splitext(shirt_file.name)[0]
                    shirt = Image.open(shirt_file).convert("RGBA")

                    x = (shirt.width - design.width) // 2
                    y = (shirt.height - design.height) // 2
                    shirt.paste(design, (x, y), design)

                    output_name = f"{graphic_name}_{color_name}_tee.png"
                    img_byte_arr = io.BytesIO()
                    shirt.save(img_byte_arr, format='PNG')
                    zipf.writestr(output_name, img_byte_arr.getvalue())

            zip_buffer.seek(0)
            zip_files_output[graphic_name] = zip_buffer

        st.success("✅ All mockups generated!")
        for name, zip_bytes in zip_files_output.items():
            st.download_button(
                label=f"📦 Download {name}_mockups.zip",
                data=zip_bytes,
                file_name=f"{name}_mockups.zip",
                mime="application/zip"
            )
