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

import warnings
warnings.filterwarnings("ignore")

base_url = 'https://www.addastories.com'
ua = UserAgent()
headers = {}
headers['user_agent'] =  ua.chrome


adda = requests.get(base_url, headers=headers, verify=False)

soup = BeautifulSoup(adda.text, 'lxml')



level_one_attrs = {'class': 'service-desc'}

def get_categories():
    """Returns a dictionary of categories and their corresponding links """
    categories = {}
    for tag in soup.find_all('div', attrs=level_one_attrs):
        try: 
            path = f'{tag.text.strip()}'
            if not tag.text.isspace(): 
                categories[f"{path}"] = tag.a['href']
        except: pass#
    return categories
        


# In[9]:


categories = get_categories()
print(categories)


# In[10]:


def get_booktitlesoup(categories, p=False):
    """Receives a dictionary of Categories and their links"""
    category_soups = {}
    if not p:
        for category, path in categories.items():
            url = base_url + path
            page = requests.get(url, headers=headers, verify=False)
            category_soups[f'{category}'] = page.text
    if p:
        for category, path in categories.items():
            url = base_url + path + f"page/{p}/"
            page = requests.get(url, headers=headers, verify=False)
            category_soups[f'{category}'] = page.text

        
    return category_soups


# In[11]:


def get_all_page_soups(pages=5):
    all_page_booktitles = {}
    for p in tqdm(range(pages)):
        p +=1
        csoup = get_booktitlesoup(categories, p)
        all_page_booktitles[p] = csoup
    return all_page_booktitles        


# In[12]:


all_page_soups = get_all_page_soups()
print(all_page_soups.keys())


# In[13]:


def get_booktitles(category_soups):
    """Receives a dictionary of HTML documents"""
    div_attrs = {'class': 'service-desc'}
    all_books = {}
    for c, s in category_soups.items():
        books = {}
        soup2 = BeautifulSoup(s, 'lxml')
        for tag in soup2.find_all('div',attrs=div_attrs):
            title = re.sub('\n+', ' ', tag.text)
            title = title.strip()
            books[f'{title}'] = tag.a['href']
            all_books[f'{c} BOOKS'] = books
    return all_books


# In[14]:


def all_book_titles(all_page_soups):
    all_book_titles={}
    for s in tqdm(all_page_soups.keys()):
        book_titles = get_booktitles(all_page_soups[s])
        all_book_titles[s] = book_titles
    return all_book_titles


# In[15]:


all_book_titles = all_book_titles(all_page_soups)


# In[16]:


print(all_book_titles)


# In[17]:


def unicodenormalize(s):
    ns = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore')
    return ns


# In[23]:


def scrape_books(book_links):
    """Receives a dictionary of categories,books, and their links"""
    for category, values in book_links.items():
        try: os.mkdir(category)
        except: pass
        print(f"Scraping {category} category. . .")
        current_books = os.listdir(path=category)
        
        for book, link in tqdm(values.items()):
            page = requests.get(link, headers=headers, verify=False)
            page = page.content
            soup = BeautifulSoup(page, 'lxml')
            name_split = book.find('by')
            
            title_header = f"""
            ## {book[0:name_split]}
            {book[name_split:]}            
            """        
            path = os.path.join(category,f'{book}.txt' )
#             os.chdir(category)
            #creating PDF Instance
            pdf = FPDF()
            pdf.add_page()
            line_height = 5
            with open(path, 'w', encoding='utf-8') as f:
                f.write(title_header)
            #Defining PDF Parameters for Header
            pdf.set_font("Times", 'B', size=16)
            pdf.write(line_height, txt = f"{book[0:name_split]}\n")
            pdf.set_font("Times", 'I', size=13)
            pdf.write(line_height, txt=f"{book[name_split:]}\n")
            
            #Writing Contents to PDF
            pdf.set_font("Times", size=9)
            for div in soup.find_all('div', attrs={'class':'article--content'}):
                for tag in div.descendants:
                    if str(tag)[:2] == '<p':
                        
                        text = unicodenormalize(tag.text)
                        text = text.decode('latin-1')
                        pdf.write(8, txt=f"{text}\n\n")
                        with open (path, 'a', encoding='utf-8') as f:
                            f.write(f"{tag.text}\n\n")
                        
                    else: continue            
            try:
                pdf.output(name=f'{book}.pdf', dest='F')
                new_pdf_path = os.path.join(category, f'{book}.pdf')
                shutil.move(src=f'{book}.pdf', dst=new_pdf_path)
            except: pass
#             
#             os.rename(path,new_pdf_path)           
                
    


# In[24]:


def begin_scrape():
    for p in range(len(all_book_titles)):
        try:
            book_titles = all_book_titles[p+1]
            scrape_books(book_titles)
        except:
            pass


# In[ ]:


begin_scrape()


# In[ ]:




