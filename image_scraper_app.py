import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import zipfile
import re

st.title("🖼️ Multi-URL High-Quality Image Extractor")

# Initialize session state to store extraction results
if "all_results" not in st.session_state:
    st.session_state.all_results = []

def clean_filename(name):
    # Clean filename to avoid illegal characters
    return re.sub(r'[\\/*?:"<>|]', "_", name)[:100]

# Input for multiple URLs, comma separated
urls_input = st.text_area("Paste webpage URLs (comma separated):")

min_width = st.slider("Minimum image width", 50, 2000, 300)
min_height = st.slider("Minimum image height", 50, 2000, 300)

if st.button("Extract Images from All URLs"):
    if not urls_input.strip():
        st.warning("Please enter at least one URL.")
    else:
        st.session_state.all_results = []  # Clear previous results
        urls = [u.strip() for u in urls_input.split(",") if u.strip()]

        for url in urls:
            st.write(f"🔎 Processing: {url}")
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract product name from <h1>, <title>, or og:title meta tag
                product_name = (
                    soup.find("h1").text.strip() if soup.find("h1") else
                    soup.title.string.strip() if soup.title else
                    (soup.find("meta", property="og:title")["content"].strip()
                     if soup.find("meta", property="og:title") else "product")
                )
                product_name = clean_filename(product_name)
                st.write(f"📝 Product Name: `{product_name}`")

                img_tags = soup.find_all("img")
                images_for_zip = []
                found = 0

                for i, img in enumerate(img_tags):
                    # Try src, data-src, srcset, data-srcset for lazy loading
                    img_url = (
                        img.get("src") or img.get("data-src") or
                        (img.get("srcset").split(",")[0].strip().split(" ")[0] if img.get("srcset") else None) or
                        (img.get("data-srcset").split(",")[0].strip().split(" ")[0] if img.get("data-srcset") else None)
                    )
                    if not img_url:
                        continue

                    full_url = urljoin(url, img_url)

                    try:
                        img_response = requests.get(full_url, timeout=5)
                        image = Image.open(BytesIO(img_response.content))
                        width, height = image.size

                        if width >= min_width and height >= min_height:
                            st.image(image, caption=f"{width}x{height}", use_column_width=True)

                            img_buffer = BytesIO()
                            ext = image.format.lower() if image.format else "jpg"
                            image.save(img_buffer, format=image.format or "JPEG")
                            img_buffer.seek(0)

                            filename = f"{product_name}_{i+1}.{ext}"
                            images_for_zip.append((filename, img_buffer))
                            found += 1
                    except Exception:
                        continue

                if found == 0:
                    st.info(f"No suitable images found for {product_name}.")

                st.session_state.all_results.append((product_name, images_for_zip))

            except Exception as e:
                st.error(f"Error processing {url}: {e}")

# Display images and download buttons from session state
if st.session_state.all_results:
    st.markdown("---")
    for product_name, images in st.session_state.all_results:
        st.write(f"### Images for **{product_name}**")

        for name, img_buf in images:
            img_buf.seek(0)
            st.image(img_buf.read(), caption=name, use_column_width=True)
            img_buf.seek(0)

        # Prepare ZIP file for download
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for name, img in images:
                img.seek(0)
                zip_file.writestr(name, img.read())
        zip_buffer.seek(0)

        st.download_button(
            label=f"📦 Download {product_name} Images ZIP",
            data=zip_buffer,
            file_name=f"{product_name}_images.zip",
            mime="application/zip"
        )
