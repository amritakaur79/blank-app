import streamlit as st
from PIL import Image
import os
import zipfile
import io

st.set_page_config(page_title="Shirt Mockup Generator", layout="centered")
st.title("👕 Shirt Mockup Generator – Multiple Graphics")

st.markdown("""
Upload **multiple design graphics (PNG)** and **shirt templates (PNG)**.  
Each design will be applied to **every shirt**, and a separate ZIP file will be created for each design.
""")

# Upload multiple designs and shirt templates
design_files = st.file_uploader("📌 Upload Design Images (up to 5 PNGs)", type=["png"], accept_multiple_files=True)
shirt_files = st.file_uploader("🎨 Upload Shirt Templates (PNG)", type=["png"], accept_multiple_files=True)

if st.button("🚀 Generate Mockups"):
    if not (design_files and shirt_files):
        st.warning("Please upload at least one design and one shirt template.")
    else:
        # Collect all ZIPs in memory
        zip_files_output = {}

        for design_file in design_files:
            graphic_name = os.path.splitext(design_file.name)[0]
            design = Image.open(design_file).convert("RGBA")
            design = design.resize((400, 400))  # Resize to fit shirt

            # Prepare in-memory zip for this design
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

            # Save final zip buffer
            zip_buffer.seek(0)
            zip_files_output[graphic_name] = zip_buffer

        # Show download buttons for each ZIP
        st.success("✅ All mockups generated!")
        for name, zip_bytes in zip_files_output.items():
            st.download_button(
                label=f"📦 Download {name}_mockups.zip",
                data=zip_bytes,
                file_name=f"{name}_mockups.zip",
                mime="application/zip"
            )
