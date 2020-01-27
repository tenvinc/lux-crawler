import time
import os
from settings import *
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

def record_links_fr_page(links, driver, max_link_cnt):
    results = driver.find_elements_by_xpath("//*[@id='dataTable']/tbody/tr")
    print("{} results obtained".format(len(results)))
    for result in results:
        if len(links) >= max_link_cnt:
            print("Maximum no. of link results obtained. Ignoring subsequent results.")
            break
        try:
            ahref = result.find_element_by_tag_name("a")
            link = ahref.get_attribute("href")
            print("Gotten {}".format(link))
            links.append(link)
        except Exception as e:
            print("Skipping element..")
    return links

def next_page(driver):
    next_page_elem = driver.find_element_by_id("dataTable_next")
    next_page_elem.click()
    try:
        element = WebDriverWait(driver, 10).until(
            absence_of_element_located((By.CSS_SELECTOR, "td.dataTables_empty"))
        )
    except TimeoutException as te:
        print("Please try again later.")
        driver.close()

# process individually
def visit_and_download(url):
    print("visiting {}".format(url))
    driver.get(url)
    qlbar = driver.find_element_by_css_selector("div.quickLinksBar")
    clickable = qlbar.find_elements_by_tag_name("a")
    for c in clickable:
        if c.get_attribute("text") == "Download PDF":
            print("Found download button. Downloading now...")
            c.click()

s_time = time.time()
# Set up download directory
if not os.path.exists("lux_downloads"):
    print("Setting up downloads for LUX reports...")
    os.mkdir("lux_downloads")

# Configure download options
fp = webdriver.FirefoxProfile()
fp.set_preference("browser.download.folderList", 2) # 2 means to use the directory 
fp.set_preference("browser.helperApps.alwaysAsk.force", False)
fp.set_preference("browser.download.manager.showWhenStarting",False)
fp.set_preference("browser.download.dir", os.path.join(os.getcwd(), "lux_downloads"))
fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
fp.set_preference("pdfjs.disabled", True)

# Configure headless
options = webdriver.FirefoxOptions()
# options.add_argument("--headless")

driver = webdriver.Firefox(firefox_profile=fp, options=options)
driver.get("https://members.luxresearchinc.com/users/sign_in")

def screenshot():   
    html = driver.page_source
    with open("loading.html", "w+") as fp:
        fp.write(html)

# Login page
username_elem = driver.find_element_by_id("user_email")
password_elem = driver.find_element_by_id("user_password")

username_elem.send_keys(USER_ID)
password_elem.send_keys(PASSWORD)

class absence_of_element_located(object):
  """An expectation for checking that an element is absent.
  """
  def __init__(self, locator):
    self.locator = locator

  def __call__(self, driver):
    elements = driver.find_elements(*self.locator)   # Finding the referenced element
    return len(elements) == 0

driver.find_element_by_name("commit").click()
try:
    element = WebDriverWait(driver, 20).until(
        absence_of_element_located((By.NAME, "commit"))
    )
except TimeoutException as te:
    print("Please try again later.")
    driver.close()

print("Main page loaded ready for queries")
time.sleep(1)
searchbar_elem = driver.find_element_by_id("searchbar")
dropdown_btn_elem = searchbar_elem.find_element_by_xpath("//div[@class='searchOpts input-group-btn']")
dropdown_btn_elem.click()
dropdown_elem = searchbar_elem.find_element_by_xpath("//ul[@class='dropdown-menu']")
dropdown_options = dropdown_elem.find_elements_by_xpath("//li")
for option in dropdown_options:
    if option.text == "Reports":
        option.click() 
        break

searchtext_elem = searchbar_elem.find_element_by_id("search_text")
searchtext_elem.send_keys("Robotics")
searchbar_elem.submit()

# Wait for page to populate entries
time.sleep(3)
try:
    element = WebDriverWait(driver, 10).until(
        absence_of_element_located((By.CSS_SELECTOR, "td.dataTables_empty"))
    )
except TimeoutException as te:
    print("Please try again later.")
    driver.close()
time.sleep(1)

links = []
record_links_fr_page(links, driver, MAX_LINK_CNT)
while len(links) < MAX_LINK_CNT:
    print("Clicking next page")
    next_page(driver)
    record_links_fr_page(links, driver, MAX_LINK_CNT)

print("Link count total: {}".format(len(links)))
for link in links:
    try_count = 0
    while try_count < 5:
        try:
            visit_and_download(link)
            break
        except TimeoutException as te:
            try_count += 1
            print("Timeout has occurred. Trying again {}".format(try_count))
    if try_count == 5:
        print("Skipping this page. Going on to next page")

print("Finished what I wanted to do. Closing now..")
driver.close()

print("Total time: {}".format(time.time() - s_time))