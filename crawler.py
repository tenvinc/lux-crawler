import time
import os
from settings import *
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class absence_of_element_located(object):
  """An expectation for checking that an element is absent.
  """
  def __init__(self, locator):
    self.locator = locator

  def __call__(self, driver):
    elements = driver.find_elements(*self.locator)   # Finding the referenced element
    return len(elements) == 0


class LuxCrawler():
    '''
    WebCrawler to crawl and scrape the LUX website for essential information
    '''
    def __init__(self, max_link_cnt=100, dl_path=None, is_headless=None):
        '''
        Initializes the settings that LuxCrawler will run on
        '''
        self.max_link_cnt = max_link_cnt
        self.dl_path = os.path.join("lux_downloads") if dl_path is None else dl_path
        if not os.path.exists(self.dl_path):
            print("Directory not found. Making one now at {}".format(self.dl_path))
            os.mkdir(self.dl_path)
        else:
            print("Directory found. Using it as lux download directory.")

        # Configure download options
        fp = webdriver.FirefoxProfile()
        fp.set_preference("browser.download.folderList", 2) # 2 means to use the directory 
        fp.set_preference("browser.helperApps.alwaysAsk.force", False)
        fp.set_preference("browser.download.manager.showWhenStarting",False)
        fp.set_preference("browser.download.dir", self.dl_path)
        fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
        fp.set_preference("pdfjs.disabled", True)

        # Configure headless
        options = webdriver.FirefoxOptions()
        if is_headless:
            print("Running Lux Crawler in headless mode...")
            options.add_argument("--headless")

        self._driver = webdriver.Firefox(firefox_profile=fp, options=options)
    
    
    def sign_in(self, username=None, password=None):
        '''
        Signs LuxCrawler into LUX Research Portal, returns when next page loads
        '''
        assert self._driver is not None
        if username is None or password is None:
            print("Please provide a username and password.")
        self._driver.get("https://members.luxresearchinc.com/users/sign_in")

        # login page
        username_elem = self._driver.find_element_by_id("user_email")
        password_elem = self._driver.find_element_by_id("user_password")
        username_elem.send_keys(username)
        password_elem.send_keys(password)

        self._driver.find_element_by_name("commit").click()
        try:
            element = WebDriverWait(self._driver, 20).until(
                absence_of_element_located((By.NAME, "commit"))
            )
        except TimeoutException as te:
            print("Please try again later.")
            self._driver.close()
        
        # add extra 0.5s for page to load fully
        time.sleep(0.5)

    
    def search_n_dl_reports(self, query):
        '''
        High level method to search for a @query under REPORTS mode and download the first @max_link_cnt
        reports in the search results
        '''
        self.search_reports(query)
        time.sleep(3)
        try:
            element = WebDriverWait(self._driver, 10).until(
                absence_of_element_located((By.CSS_SELECTOR, "td.dataTables_empty"))
            )
        except TimeoutException as te:
            print("Please try again later.")
            self._driver.close()
        time.sleep(1)

        links = self.parse_reports()
        self.visit_and_dl_all(links)


    def search_reports(self, query):
        '''
        Goes into REPORTS mode, then search for query in searchbar
        '''
        assert self._driver is not None
        searchbar_elem = self._driver.find_element_by_id("searchbar")
        # Change to REPORTS mode
        dropdown_btn_elem = searchbar_elem.find_element_by_xpath("//div[@class='searchOpts input-group-btn']")
        dropdown_btn_elem.click()
        dropdown_elem = searchbar_elem.find_element_by_xpath("//ul[@class='dropdown-menu']")
        dropdown_options = dropdown_elem.find_elements_by_xpath("//li")
        for option in dropdown_options:
            if option.text == "Reports":
                option.click() 
                break
        # Enter query in search bar
        searchtext_elem = searchbar_elem.find_element_by_id("search_text")
        searchtext_elem.send_keys(query)
        searchbar_elem.submit()

        time.sleep(3)

    def parse_reports(self):
        '''
        Retrieves all to links to the reports given by search results up to a count of 
        @max_link_cnt
        '''
        links = []
        self._record_links_fr_page(links)
        while len(links) < self.max_link_cnt:
            print("Clicking next page")
            self._next_page()
            self._record_links_fr_page(links)
        return links


    def visit_and_dl_all(self, links):
        '''
        Visit all the links and downloads the report
        '''
        for link in links:
            try_count = 0
            while try_count < 5:
                try:
                    self._visit_and_download(link)
                    break
                except TimeoutException as te:
                    try_count += 1
                    print("Timeout has occurred. Trying again {}".format(try_count))
            if try_count == 5:
                print("Skipping this page. Going on to next page")
    
    
    def _record_links_fr_page(self, links):
        '''
        Record down the links in the search results for the current page under REPORTS mode
        '''
        results = self._driver.find_elements_by_xpath("//*[@id='dataTable']/tbody/tr")
        print("{} results obtained".format(len(results)))
        for result in results:
            if len(links) >= self.max_link_cnt:
                print("Maximum no. of link results obtained. Ignoring subsequent results.")
                break
            try:
                ahref = result.find_element_by_tag_name("a")
                link = ahref.get_attribute("href")
                print("Gotten {}".format(link))
                links.append(link)
            except Exception as e:
                print("Skipping element..")
        print("Link count total: {}".format(len(links)))
        return links

    
    def _next_page(self):
        ''' 
        Goes to the next page of the search results under REPORTS mode
        '''
        next_page_elem = self._driver.find_element_by_id("dataTable_next")
        next_page_elem.click()
        try:
            element = WebDriverWait(self._driver, 10).until(
                absence_of_element_located((By.CSS_SELECTOR, "td.dataTables_empty"))
            )
        except TimeoutException as te:
            print("Please try again later.")
            self._driver.close()

    
    def _visit_and_download(self, url):
        '''
        Visits an url and download the report from that page
        '''
        print("Visiting {}".format(url))
        self._driver.get(url)
        qlbar = self._driver.find_element_by_css_selector("div.quickLinksBar")
        clickable = qlbar.find_elements_by_tag_name("a")
        for c in clickable:
            if c.get_attribute("text") == "Download PDF":
                print("Found download button. Downloading now...")
                c.click()
                

if __name__ == "__main__":
    s_time = time.time()
    queries = []
    with open(QUERIES_TO_SEARCH_PATH, 'r') as queries_fp:
        queries = queries_fp.readlines()

    lux_crawler = LuxCrawler(max_link_cnt=MAX_LINK_CNT)
    print("LuxCrawler initiated. Starting the sign in...")
    lux_crawler.sign_in(username=USER_ID, password=PASSWORD)
    print("Sign in completed. Starting the searches")
    for query in queries[1:]:
        s_time = time.time()
        query = query.strip()
        print("Searching for keyword \"{}\"".format(query))
        lux_crawler.search_n_dl_reports(query)
        print("Finished downloading for \"{}\" in {}".format(query, time.time() - s_time))

    print("Finished what I wanted to do. Closing now..")
    driver.close()

    print("Total execution time: {}".format(time.time() - s_time))