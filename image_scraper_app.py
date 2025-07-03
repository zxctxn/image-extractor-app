import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
from io import BytesIO
import zipfile
import re

st.title("🖼️ Multi-URL High-Quality Image Extractor")

if "all_results" not in st.session_state:
    st.session_state.all_results = []

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", name)[:100]

urls_input = st.text_area("Paste webpage URLs (comma separated):")

min_width = st.slider("Minimum image width", 50, 2000, 300)
min_height = st.slider("Minimum image height", 50, 2000, 300)

if st.button("Extract Images from All URLs"):
    if not urls_input.strip():
        st.warning("Please enter at least one URL.")
    else:
        st.session_state.all_results = []
        urls = [u.strip() for u in urls_input.split(",") if u.strip()]

        for url in urls:
            if not url.lower().startswith(("http://", "https://")):
                url = "https://" + url

            st.write(f"🔎 Processing: {url}")

            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if response.status_code != 200:
                    st.warning(f"Skipping URL {url} — server returned status code {response.status_code}")
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')

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

# Show all download buttons first (at the top)
if st.session_state.all_results:
    st.markdown("## Download ZIP Files")
    for product_name, images in st.session_state.all_results:
        if images:
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

    st.markdown("---")
    # Then show images below the buttons
    for product_name, images in st.session_state.all_results:
        st.write(f"### Images for **{product_name}**")
        for name, img_buf in images:
            img_buf.seek(0)
            st.image(img_buf.read(), caption=name, use_column_width=True)
            img_buf.seek(0)
