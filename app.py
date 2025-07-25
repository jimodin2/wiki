import streamlit as st
import requests
import pandas as pd

# Set Streamlit page config
st.set_page_config(page_title="Wikipedia Section Link Extractor", layout="wide")

st.title("🔗 Wikipedia Section Link Extractor (via API)")
st.markdown("""
This tool fetches links from specific sections of Wikipedia articles using the official Wikipedia API.
""")

# User inputs
url = st.text_input("Enter Wikipedia URL:")
sections = st.multiselect("Select Sections to Extract:", ["Events", "Births", "Deaths", "Holidays and observances"])

# Extract page title from URL
def extract_page_title(wiki_url):
    if not wiki_url.startswith("https://en.wikipedia.org/wiki/"):
        return None
    return wiki_url.split("/wiki/")[-1].replace(" ", "_")

# Call Wikipedia API and extract links
def fetch_section_links_api(page_title, section_name):
    endpoint = f"https://en.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "sections"
    }
    sec_response = requests.get(endpoint, params=params).json()
    section_index = None
    for sec in sec_response.get("parse", {}).get("sections", []):
        if sec['line'].lower() == section_name.lower():
            section_index = sec['index']
            break

    if not section_index:
        return []

    content_params = {
        "action": "parse",
        "page": page_title,
        "format": "json",
        "prop": "text",
        "section": section_index
    }
    content_response = requests.get(endpoint, params=content_params).json()
    html_text = content_response.get("parse", {}).get("text", {}).get("*", "")

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html_text, "html.parser")
    links_data = []
    for link in soup.find_all("a", href=True):
        anchor = link.get_text(strip=True)
        href = link['href']
        if not anchor or href.startswith("#"):
            continue
        full_link = f"https://en.wikipedia.org{href}" if href.startswith("/wiki/") else href
        link_type = "internal" if href.startswith("/wiki/") else "external"
        links_data.append({
            "Section": section_name,
            "Anchor": anchor,
            "Link": full_link,
            "Type": link_type
        })
    return links_data

if url and sections:
    page_title = extract_page_title(url)
    if not page_title:
        st.error("❌ Please enter a valid Wikipedia URL.")
    else:
        all_links = []
        for section in sections:
            section_links = fetch_section_links_api(page_title, section)
            all_links.extend(section_links)

        if all_links:
            df = pd.DataFrame(all_links)
            st.success(f"✅ Found {len(df)} links.")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download CSV", csv, "wikipedia_links.csv", "text/csv")
        else:
            st.warning("No links found in the selected sections.")
