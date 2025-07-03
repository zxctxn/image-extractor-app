import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import zipfile
import re

st.title("🖼️ Multi-URL High-Quality Image Extractor")

urls_text = st.text_area(
    "Paste one or more webpage URLs (one per line):",
    height=150,
)

min_width = st.slider("Minimum image width", 100, 2000, 300)
min_height = st.slider("Minimum image height", 100, 2000, 300)

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)[:100]

def extract_images_from_url(url, min_w, min_h):
    images = []
    try:
        response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to get product name
        product_name = (
            soup.find("h1").text.strip() if soup.find("h1") else
            soup.title.string.strip() if soup.title else
            soup.find("meta", property="og:title")["content"].strip()
            if soup.find("meta", property="og:title") else "product"
        )
        product_name = clean_filename(product_name)

        img_tags = soup.find_all("img")
        count = 0
        for i, img in enumerate(img_tags):
            img_url = img.get("src") or img.get("data-src")
            if not img_url:
                continue

            full_url = urljoin(url, img_url)
            try:
                img_response = requests.get(full_url, timeout=5)
                image = Image.open(BytesIO(img_response.content))
                width, height = image.size

                if width >= min_w and height >= min_h:
                    # Save image to buffer
                    img_buffer = BytesIO()
                    ext = image.format.lower() if image.format else "jpg"
                    image.save(img_buffer, format=image.format or "JPEG")
                    img_buffer.seek(0)
                    filename = f"{product_name}_{i+1}.{ext}"
                    images.append((filename, img_buffer))
                    count += 1
            except:
                continue
        return product_name, images, count
    except Exception as e:
        st.error(f"Error fetching {url}: {e}")
        return None, [], 0

if st.button("Extract Images from All URLs"):
    if not urls_text.strip():
        st.warning("Please enter at least one URL.")
    else:
        urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
        all_results = []
        for url in urls:
            st.write(f"🔍 Extracting images from: {url}")
            product_name, images, count = extract_images_from_url(url, min_width, min_height)
            if count == 0:
                st.info(f"No suitable images found for {url}")
            else:
                st.write(f"Found {count} images for **{product_name}**")
                # Show images inline (optional)
                for name, img_buf in images:
                    img_buf.seek(0)
                    st.image(img_buf.read(), caption=name, use_column_width=True)
                    img_buf.seek(0)

                all_results.append((product_name, images))

        # Create download buttons per URL
        for product_name, images in all_results:
            if images:
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                    for name, img in images:
                        zip_file.writestr(name, img.read())
                        img.seek(0)
                zip_buffer.seek(0)
                st.download_button(
                    label=f"📦 Download {product_name} Images ZIP",
                    data=zip_buffer,
                    file_name=f"{product_name}_images.zip",
                    mime="application/zip"
                )
