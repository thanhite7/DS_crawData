import json
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

link = 'https://en.tutiempo.net/climate/{month}-{year}/ws-488200.html'
filename = "air_quality.json"
span_dict = {}

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")  
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-javascript") 
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-infobars")


driver = webdriver.Chrome(options=chrome_options)

with open(filename, "r", encoding="utf-8") as f:
    existing_data = json.load(f)

def run_selenium(url, results):
    driver.get(url)
    WebDriverWait(driver,40).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.medias.mensuales.numspan")))
    

    span_elements = driver.find_elements(By.CSS_SELECTOR, "span")
    for span in span_elements:
        class_name = span.get_attribute("class")
        if class_name and class_name.startswith("n"):
            after_content = driver.execute_script(
                "return window.getComputedStyle(arguments[0], '::after').getPropertyValue('content');",
                span,
            ).strip('"')

            if after_content:
                span_dict[class_name] = after_content

    content = driver.page_source
    results.append(content) 
async def get_span_text(spans):
    result = ""
    for span in spans:
        class_name = span.get('class')[0] if span.get('class') else ''
        if class_name in span_dict:
            result += span_dict[class_name]
    return result

async def crawl_data(month, year):
    global span_dict
    results = []

    await asyncio.to_thread(run_selenium, link.format(month=month, year=year), results)
    
    content = results[0]
    
    soup = BeautifulSoup(content, "html.parser")
    table = soup.find_all("table", class_="medias mensuales numspan")

    slide_data = []
    rows = table[0].find_all('tr')

    for i in range(2, len(rows) - 2):
        row = rows[i]
        cols = row.find_all('td')
        spans = row.find_all('span')
        dt ='0' + cols[0].get_text(strip=True) if len(cols[0].get_text(strip=True)) == 1 else cols[0].get_text(strip=True)
        if len(spans) == 0:
            slide_data.append({
                "datetime": f'{dt}/{month}/{year}',
                "T": cols[1].get_text(strip=True),
                "TM": cols[2].get_text(strip=True),
                "Tm": cols[3].get_text(strip=True),
                "H": cols[5].get_text(strip=True),
                "PP": cols[6].get_text(strip=True),
                "VV": cols[7].get_text(strip=True),
                "V": cols[8].get_text(strip=True),
                "VM": cols[9].get_text(strip=True),
            })
        else:
            slide_data.append({
                "datetime": f'{dt}/{month}/{year}',
                "T": await get_span_text(cols[1].find_all('span')),
                "TM": await get_span_text(cols[2].find_all('span')),
                "Tm": await get_span_text(cols[3].find_all('span')),
                "H": await get_span_text(cols[5].find_all('span')),
                "PP": await get_span_text(cols[6].find_all('span')),
                "VV": await get_span_text(cols[7].find_all('span')),
                "V": await get_span_text(cols[8].find_all('span')),
                "VM": await get_span_text(cols[9].find_all('span')),
            })

    existing_data.extend(slide_data)

async def main():
    for year in range(2020, 2025):
        for month in range(1, 13):
            if (year == 2020 and month < 11) or (year == 2024 and month > 10):
                continue
            month_str = f"{month:02d}"  
            print(f"Crawling data for {month_str}-{year}")
            await crawl_data(month_str, str(year))
            print(f"Data crawled for {month_str}-{year}")

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)

asyncio.run(main())

driver.quit()
