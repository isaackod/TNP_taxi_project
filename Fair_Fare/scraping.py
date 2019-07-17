import selenium

from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC



ESTIMATE_PARAMS = {"lyft": {"URL":"https://www.lyft.com/rider/fare-estimate",
                           "box1":"fare-start","box2":"fare-end"},
                 "uber": {"URL":"https://www.uber.com/us/en/price-estimate",
                          "box1":"pickup","box2":"destination"}}


def uber_scraper(start,stop,browser):
    company = 'uber'
    p = ESTIMATE_PARAMS[company]
    browser.get(p["URL"])
    
    start_field = browser.find_element_by_name(p['box1'])
    end_field = browser.find_element_by_name(p['box2'])
  
    start_field.send_keys(start)
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "li"))
    )
    time.sleep(2)
    start_field.send_keys(Keys.RETURN)
    time.sleep(2)
    end_field.send_keys(stop)
    WebDriverWait(browser, 5).until(
        EC.presence_of_element_located((By.TAG_NAME, "li"))
    )
    time.sleep(2)
    end_field.send_keys(Keys.RETURN)
    XPATH = "//div/div[@role='radio']" # unique radio buttons
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, XPATH))
    )
    tags = browser.find_elements_by_xpath(XPATH)
    return tags


def uber_parser(tags):
    out = {}
    for tag in tags:
        name, price = tag.text.split()
        out[name] = float(price.replace('$',''))
    return out

    
def serial_scraper(start_coded,stop_coded,kind = 'uber'):
    opts =Options()
    opts.headless = True
    browser = Chrome(options=opts)
    browser.implicitly_wait(0)
    
    try:
        if kind == "lyft":
            tags = lyft_scraper(start_coded, stop_coded,browser)
            parsed = lyft_parser(tags)

        else:
            tags = uber_scraper(start_coded,stop_coded, browser)
            parsed = uber_parser(tags)
    except:
        tags = None
        parsed = None
    
    browser.close()
    
    return parsed