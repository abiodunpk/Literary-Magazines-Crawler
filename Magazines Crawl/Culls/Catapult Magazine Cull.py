#!/usr/bin/env python
# coding: utf-8

# In[1]:


from selenium import webdriver
from fpdf import FPDF
from tqdm import tqdm
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from ebooklib import epub
from time import sleep
import requests
import os
import unicodedata
import re
import shutil
import warnings
warnings.filterwarnings('ignore')


# In[3]:





# In[10]:


browser = webdriver.Chrome()


# In[ ]:


def drive_page(page_url, patience=6):
    """Drives pages and Loads DOM Element"""
    browser.get(page_url)
    sleep(patience)
    
    def skip_ads():
        try:
            skip = browser.find_element_by_xpath('//a[@id="om-full-page-takeover-entrance-optin-no-button"]')
            skip.click()
        except Exception:
            pass        
        
    try:
        for i in range(patience):
            browser.execute_script('window.scrollTo(0,document.body.scrollHeight);')
            #CLOSE POPUP
            skip_ads()            
            sleep(3)
    except Exception:
        print("Error, Cannot Scroll")

    # CLOSE ANY POPUP    
    skip_ads()
    sleep(patience)
    
    return browser.page_source


# In[12]:


url = "https://catapult.co/"
ua = UserAgent()
headers = {}
headers['user-agent'] = ua.chrome


# In[13]:


categories = ['fiction', 'on-writing', 'column']
def generate_category_soups(categories):
    category_soups = {}
    for c in tqdm(categories):
        base_url = f"https://catapult.co/editorial/categories/{c}/stories"
        catapult_source = drive_page(base_url)
        soup = BeautifulSoup(catapult_source, 'lxml')
        category_soups[f"{c}"] = soup
    return category_soups


# In[14]:


category_soups = generate_category_soups(categories)


# In[ ]:


category_soups['fiction']


# In[15]:


print(category_soups.keys())


# In[16]:


def generate_booklinks(soup, story_attrs=None, b_url="https://catapult.co"):
    """Returns a dictionary of Story Names and Their Links"""
    links = {}
    if not story_attrs:
        story_attrs = {'class':"content"} 
    story_tags = soup.findAll('div', attrs=story_attrs)
    for tag in tqdm(story_tags):
        link = tag.find('a')
        link_text = link.text.strip()
        link = link["href"]
        link = b_url + str(link)
        links[link_text] = link
    return links        


# In[17]:


def generate_all_booklinks(category_soups):
    booklinks = {}
    for c in tqdm(category_soups.keys()):
        c_soup = category_soups[c]
        booklinks[c] = generate_booklinks(c_soup)
    return booklinks


# In[18]:


all_booklinks=generate_all_booklinks(category_soups)


# In[ ]:


all_booklinks


# In[23]:


def unicodenormalize(s):
    ns = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    return ns


# In[30]:


def scrape_books(book_links):
    """Receives a dictionary of categories,books, and their links"""
    
    def create_epub():
        
        style = '''
            body, table {
                margin-left: 100px;
                margin-right: 100px;
                font-size: 28px !important;
                font: 28px Times New Roman !important;
                font-weight: 400 !important;
            }
            '''       
        eb = epub.EpubBook()
        eb.set_identifier(f"{savename}")
        eb.set_title(f"{book}")
        eb.set_language('en')
        eb.add_author(f"{author}")
        return eb
        
    def create_pdf():
        pdf = FPDF()
        pdf.add_page()
        line_height = 5
        with open(path, 'w', encoding='utf-8') as f:
            f.write(savename)
        #Defining PDF Parameters for Header
        pdf.set_font("Times", 'B', size=16)
        pdf.write(line_height, txt = f"{book}\n")
        pdf.set_font("Times", 'I', size=13)
        pdf.write(line_height, txt=f"{author}\n")
        return pdf
                      
    for category, values in book_links.items():
        try: os.mkdir(category)
        except: pass
        print(f"Scraping {category} category. . .")
        current_books = os.listdir(path=category)
    
        
        #GET LINKS AND NAMES FROM DICTIONARY OF SOUPS
        for book, link in tqdm(values.items()):
            page = requests.get(link, headers=headers, verify=False)
            page = page.content
            soup = BeautifulSoup(page, 'lxml')
              
            #REMOVE SPECIAL CHARACTERS FROM TITLES and defiing author#             
            savename = re.sub('\W+', ' ', book)
            altsavename = re.sub('\W+', '', book)
            author = soup.find('div', attrs={'class': 'name'}).text
            bio = soup.find('div',attrs={'class': 'about'}).text
            
            path = os.path.join(category,f'{savename}.txt' )
#             
            #CREATING PDF Instance
            pdf = create_pdf() 
            #CREATING EPUB INSTANCE
            eb = create_epub()
            #Writing Contents to PDF, TEXT FILE, and EPUB
            
            eb_header = f'<h2 style="text-align:center">{book}</h2>'
            eb_content = eb_header + f'<p><i style="text-align:center">{author}, Catapult</i></p>'
            
            pdf.set_font("Times", size=9)
            for div in soup.find_all('div', attrs={'class':'story_content'}):
                for tag in div.descendants:
                    if str(tag)[:2] == '<p':
                        
                        text = unicodenormalize(tag.text)
                        text = text.decode('latin-1')
                        pdf.write(8, txt=f"{text}\n\n")
                        #Write to Text File
                        with open (path, 'a', encoding='utf-8') as f:
                            f.write(f"{tag.text}\n\n")
                        #Write to Epub_contents
                        eb_content += f'<p>{tag.text}</p>'                        
                    else: continue
            # WRITE TO EPUB
            about = f"<h3>About Author</h3><p><i>{bio}</i></p>"
            eb_content+= about
            chapter = epub.EpubHtml(title=f"{book}", file_name='chap_01.xhtml', lang='hr')
            chapter.content = eb_content            
            eb.add_item(chapter)
            spine = ['nav']
            spine.append(chapter)
            nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
            eb.add_item(nav_css)
            eb.spine = spine
            epub_path = os.path.join(category, f"{savename}.epub")
            epub.write_epub(epub_path, eb, {})
            
            #MOVE ACCIDENTAL FILES TO THEIR CATEGORY
            try:
                pdf.output(name=f'{savename}.pdf', dest='F')
                new_pdf_path = os.path.join(category, f'{savename}.pdf')
                new_epub_path = os.path.join(category, f"{altsavename}.epub")
                shutil.move(src=f'{savename}.pdf', dst=new_pdf_path)
                shutil.move(src=f'{savename}.epub', dst=new_epub_path)        
            except: pass
            
#             
#             os.rename(path,new_pdf_path)           
                


# In[31]:


scrape_books(all_booklinks)


# In[ ]:




