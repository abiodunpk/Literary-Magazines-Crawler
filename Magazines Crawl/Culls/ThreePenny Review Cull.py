#!/usr/bin/env python
# coding: utf-8

# In[102]:


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


# In[142]:


base_url = 'https://www.threepennyreview.com/'
ua = UserAgent()
headers = {}
headers['user_agent'] =  ua.msie
response = requests.get(base_url, headers=headers, verify=False)
print(response)


# In[4]:


#WEBDRIVER 
browser = webdriver.Chrome()


# In[7]:


browser.get(base_url)


# In[137]:


def get_all_issues():
    url = 'https://www.threepennyreview.com/past.html'
    
    def get_current_issue():        
        current_url = 'https://www.threepennyreview.com/current.html'
        browser.get(current_url)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        name = soup.find('h2')
        return name.text, current_url
    
    current_name, current_link = get_current_issue()        
        
    browser.get(url)
    soup = BeautifulSoup(browser.page_source, 'lxml')
    all_issues = {}
    all_issues[current_name] = current_link
    
    for tag in soup.findAll('a'):
        try:
            link = tag['href']
        except Exception:
            pass   
        divide=link.find('/')
        if link[:divide] == 'tocs':
            all_issues[tag.text] = base_url + link            
    return all_issues      
    


# In[139]:


all_issues = get_all_issues()


# In[165]:


def get_all_booklinks(issues):
    """Recieves a dictionary of respective issues and directories"""
    all_booklinks = {}
    for issue, directory in tqdm(issues.items()):
        browser.get(directory)
        soup = BeautifulSoup(browser.page_source, 'lxml')
        booklinks={}
        for tag in soup.findAll('a'):
            try:
                link = tag['href']
            except Exception:
                pass            
            divide = link.find('samples')
            if divide >=0:
                booklinks[tag.text] =  base_url + link[divide:]
        all_booklinks[issue] = booklinks
    return all_booklinks


# In[166]:


all_book_titles =  get_all_booklinks(all_issues)


# In[175]:


def unicodenormalize(s):
    ns = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    return ns


# In[242]:


def scrape_books(book_links):
    """Receives a dictionary of categories,books, and their links"""
    
    def create_epub():  
        eb = epub.EpubBook()
        eb.set_identifier(f"{savename}")
        eb.set_title(f"{book}")
        eb.set_language('en')
        eb.add_author(f"{author}")
        style = '''
            body, table {
                margin-left: 100px;
                margin-right: 100px;
                font-size: 28px !important;
                font: 28px Times New Roman !important;
                font-weight: 400 !important;
            }
            '''        
        return eb
        
   
    for category, values in book_links.items():
        try: os.mkdir(category)
        except: pass
        print(f"Scraping {category} category. . .")
        current_books = os.listdir(path=category)
        
        for book, link in tqdm(values.items()):
            browser.get(link)
            soup = BeautifulSoup(browser.page_source, 'lxml')
            author = soup.find('center').text
            savename = re.sub('\W+', ' ', book)
            altsavename = re.sub('\W+', '', book) 
            eb_content = browser.page_source
            cork = eb_content.find('Home Page</a>')
            eb_content = eb_content[:cork]
            #creating EPUB
            eb = create_epub()
                
           #Writing Contents to Epub      
                        
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
            
            try:
                pdf.output(name=f'{savename}.pdf', dest='F')
                new_pdf_path = os.path.join(category, f'{savename}.pdf')
                new_epub_path = os.path.join(category, f"{altsavename}.epub")
                shutil.move(src=f'{savename}.pdf', dst=new_pdf_path)
                shutil.move(src=f'{savename}.epub', dst=new_epub_path)     
            except: pass
#             
#             os.rename(path,new_pdf_path)     
    


# In[243]:


scrape_books(all_book_titles)


# In[ ]:





# In[ ]:





# In[ ]:




