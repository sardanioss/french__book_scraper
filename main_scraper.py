from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

# how the search will work is like this:
# get title -> get the year by splitting the line at / and then at " " -> get the last element and add it at the end, now search for it
# -> if not found then remove the last element and search again -> if not found then try to remove the author and add back the last element
# -> if again not found then remove the last element as well as the author and search again
# if found good if not repeat the process with the next title

def process_title(stage, title):
    if stage == 1:
        title_elements = title.split("-")
        to_add = title_elements[-1].strip()
        return title.replace(" - " + to_add, f" {to_add.split('/')[-1]}")
    elif stage == 2:
        element = title.split(" ")[-1]
        return title.replace(element, "")
    elif stage == 3:
        date_element = title.split(" ")[-1]
        # remove the author
        title = title.split("by")[0].strip()
        return title + " " + date_element
    elif stage == 4:
        title_elements = title.split(" ")
        to_add = title_elements[-1]
        return title.replace(to_add, "")


base_url = "https://www.chasse-aux-livres.fr/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(base_url)
    page.wait_for_timeout(5000)
    #<input id="query" name="query" type="search" style="font-size: 14px; padding-right: 4px !important;" class="query form-control px-2 ui-autocomplete-input" placeholder="Entrez un titre, un auteur, un éditeur, un ISBN ou des mots-clés..." value="HISTOIRE UNIVERSELLE 6 by C. Grimberg, R. Svanström" autocomplete="off">
    with open("titles.txt", "r", encoding="utf-8") as f:
        titles = f.read().split("\n")
    for title in titles:
        for i in range(1, 5):
            processed_title = process_title(i, title)
            page.fill("input[name='query']", processed_title)
            page.keyboard.press("Enter")
            page.wait_for_timeout(5000)
            # now there are three things that can, first there are multiple entries and we need to get the first one, second is there is one entry and it got loaded automatically, third is there are no entries and we need to go back and try again with a different process
            # let's first check if there are multiple entries
            to_check_further = True
            try:
                # there are multiple entries
                tbody = page.locator("tbody#tbody-results-list-mobile")
                rows = tbody.locator("tr").count()
                if rows > 1:
                    # there are multiple entries
                    first_row = tbody.locator("tr").first
                    first_row.click()
                    page.wait_for_timeout(5000)
                    book_title = page.locator("h1#book-title-and-details").first.inner_text()
                    to_check_further = False
                    print(book_title)
                    time.sleep(5)
            except:
                # there is only one entry
                pass
            try:
                # there's a single entry
                book_title = page.locator("h1#book-title-and-details").first.inner_text()
                print(book_title)
                to_check_further = False
            except:
                # there's no entry
                #<p id="no-result-msg">Désolé, aucun résultat n'a été trouvé pour <strong>“&nbsp;HISTOIRE UNIVERSELLE 6 by C. Grimberg, R. Svanström 1964&nbsp;”</strong> dans le catalogue <strong>Livres</strong>.</p>
                no_result_msg = page.locator("p#no-result-msg").first.inner_text()
                print(no_result_msg)
                to_check_further = False

