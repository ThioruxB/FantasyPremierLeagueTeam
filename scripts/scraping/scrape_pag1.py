import re
from bs4 import BeautifulSoup
import json

def scrape_pag1_html(file_path="pag1.html"):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. Extract Metadata
    metadata = {
        "title": soup.title.string.strip() if soup.title else "No Title",
        "meta_tags": []
    }
    for meta in soup.find_all('meta'):
        meta_info = {}
        if meta.get('name'):
            meta_info['name'] = meta.get('name')
        if meta.get('property'):
            meta_info['property'] = meta.get('property')
        if meta.get('content'):
            meta_info['content'] = meta.get('content')
        if meta.get('charset'):
            meta_info['charset'] = meta.get('charset')
        if meta.get('http-equiv'):
            meta_info['http-equiv'] = meta.get('http-equiv')
        if meta_info:
            metadata["meta_tags"].append(meta_info)

    # 2. Identify and Remove Dashboard/Ad Content
    # Remove the specific JSON script block
    script_to_remove = soup.find('script', string=re.compile(r'require\.config\.params\["args"\]'))
    if script_to_remove:
        script_to_remove.decompose()

    # Remove identified dashboard sections by ID
    dashboard_ids = ['match-centre', 'match-centre-header', 'leftsticky', 'rightsticky', 'chatbot-container']
    for id_name in dashboard_ids:
        element = soup.find(id=id_name)
        if element:
            element.decompose()
            
    # Remove elements related to ads/tracking by ID or class patterns
    ad_elements_to_remove = soup.find_all(class_=re.compile(r'adm-ad-loading|sticky-unit-wrapper|snack-section|snack-sidebar'))
    for element in ad_elements_to_remove:
        element.decompose()

    # Remove specific script tags that are likely ads/tracking
    for script in soup.find_all('script'):
        script_src = script.get('src')
        script_string = script.string

        if script_string and ('googletag' in script_string or 'xtremepush' in script_string or 'fbq' in script_string):
            script.decompose()
        elif script_src and ('googletag' in script_src or 'xtremepush' in script_src or 'facebook' in script_src):
            script.decompose()

    # Remove noscript tags for GTM
    noscript_gtm = soup.find('noscript', string=re.compile(r'GTM-K2NSL35'))
    if noscript_gtm:
        noscript_gtm.decompose()

    # 3. Extract Visible Text
    # Get text from the body after removing unwanted elements
    body_content = soup.find('body')
    text_content = body_content.get_text(separator=' ', strip=True) if body_content else ""

    # 4. Extract Links
    links = []
    for a_tag in soup.find_all('a', href=True):
        link_text = a_tag.get_text(strip=True)
        if link_text: # Only include links with visible text
            links.append({"text": link_text, "href": a_tag['href']})

    # 5. Extract Image Sources
    images = []
    for img_tag in soup.find_all('img', src=True):
        images.append({"src": img_tag['src'], "alt": img_tag.get('alt', '')})

    result = {
        "metadata": metadata,
        "text_content": text_content,
        "links": links,
        "images": images
    }

    return result

if __name__ == "__main__":
    scraped_data = scrape_pag1_html()
    print(json.dumps(scraped_data, indent=2, ensure_ascii=False))
