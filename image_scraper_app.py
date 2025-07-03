import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import zipfile
import os

st.title("🖼️ High-Quality Image Extractor")

url = st.text_input("Paste the webpage URL below:")

# Temp storage for images
download_images = []

if st.button("Extract Images"):
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tags = soup.find_all("img")
            found = 0

            for i, img in enumerate(img_tags):
                img_url = img.get("src") or img.get("data-src")
                if not img_url:
                    continue

                full_url = urljoin(url, img_url)

                try:
                    img_response = requests.get(full_url, timeout=5)
                    image = Image.open(BytesIO(img_response.content))
                    width, height = image.size

                    if width >= 300 and height >= 300:
                        st.image(image, caption=f"{width}x{height}", use_column_width=True)

                        # Save image to list for download
                        img_buffer = BytesIO()
                        ext = image.format.lower() if image.format else "jpg"
                        image.save(img_buffer, format=image.format or "JPEG")
                        img_buffer.seek(0)
                        download_images.append((f"image_{i}.{ext}", img_buffer))
                        found += 1
                except:
                    continue

            if found == 0:
                st.info("No suitable high-res images found.")
        except Exception as e:
            st.error(f"Error fetching the page: {e}")

# Zip and download
if download_images:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for name, img in download_images:
            zip_file.writestr(name, img.read())
    zip_buffer.seek(0)
    st.download_button(
        label="📦 Download All Images as ZIP",
        data=zip_buffer,
        file_name="images.zip",
        mime="application/zip"
    )
