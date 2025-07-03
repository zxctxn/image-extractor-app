import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import zipfile
import re

st.title("🖼️ High-Quality Image Extractor")

url = st.text_input("Paste the webpage URL below:")

# Store images for zipping
download_images = []

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)[:100]

if st.button("Extract Images"):
    if not url:
        st.warning("Please enter a valid URL.")
    else:
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, 'html.parser')

            # Try to get the product name from <h1>, <title>, or meta tags
            product_name = (
                soup.find("h1").text.strip() if soup.find("h1") else
                soup.title.string.strip() if soup.title else
                soup.find("meta", property="og:title")["content"].strip()
                if soup.find("meta", property="og:title") else "product"
            )
            product_name = clean_filename(product_name)

            st.subheader(f"📝 Product Name: `{product_name}`")

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

                        img_buffer = BytesIO()
                        ext = image.format.lower() if image.format else "jpg"
                        image.save(img_buffer, format=image.format or "JPEG")
                        img_buffer.seek(0)

                        filename = f"{product_name}_{i+1}.{ext}"
                        download_images.append((filename, img_buffer))
                        found += 1
                except:
                    continue

            if found == 0:
                st.info("No suitable high-res images found.")
        except Exception as e:
            st.error(f"Error fetching the page: {e}")

# Download zip
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



