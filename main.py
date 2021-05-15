#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/8/15 下午 10:30
# @Author : Aries
# @Site : 
# @File : main.py
# @Software: PyCharm

from selenium import webdriver
from bs4 import BeautifulSoup
import time
import requests
import pymssql
from tqdm import tqdm

year = input("請輸入年分:")

print("開始連接資料庫......")
# 連接資料庫
conn = pymssql.connect(
    host='',
    user='',
    password='',
    database=''
)

print("開始建立資料表......")
# 建立資料表
cursor = conn.cursor()
cursor.execute(f"""
IF OBJECT_ID('test_{year}', 'U') IS NOT NULL
  DROP TABLE test_{year}
CREATE TABLE test_{year} (
  編號 INT NOT NULL,
  報名序號 VARCHAR(100),
  名字 VARCHAR(100),
  學校 VARCHAR(100),
  入取學校 VARCHAR(100),
  正取或備取 VARCHAR(100),
  PRIMARY KEY(編號)
)
""")
conn.commit()

htmltext = requests.get(f"https://www.com.tw/cross/test_county{year}.html")
soup = BeautifulSoup(htmltext.text, 'html.parser')

city_data = soup.find_all('div', align="left")

print("開始抓取都市......")
city = []
for i in tqdm(city_data):
    city_every = i.find_all('a')
    for j in city_every:
        city.append(j.get('href'))

print("開始抓取各區......")
area = []
for i in tqdm(city):
    htmltext = requests.get(f"https://www.com.tw/cross/{i}")
    soup = BeautifulSoup(htmltext.text, 'html.parser')
    area_data = soup.find_all('div', align="left")
    for i in area_data:
        area_every = i.find_all('a')
        for j in area_every:
            area.append(j.get('href'))

print("開始抓取各考場......")
place = []
for i in tqdm(area):
    htmltext = requests.get(f"https://www.com.tw/cross/{i}")
    soup = BeautifulSoup(htmltext.text, 'html.parser')
    place_data = soup.find_all('div', align="left")
    for i in place_data:
        place_every = i.find_all('a')
        for j in place_every:
            place.append(j.get('href'))

driver = webdriver.Chrome()

ID = 1
print("開始抓取學生資料......")
for test in tqdm(range(0, len(place))):
    driver.get(f"https://www.com.tw/cross/{place[test]}")
    time.sleep(.5)
    htmltext = driver.page_source
    soup = BeautifulSoup(htmltext, 'html.parser')

    # 背景顏色標籤
    detail = []
    bgcolor = ['#DEDEDC', '#FFFFFF']
    a = soup.find_all('tr', bgcolor=bgcolor[0])
    b = soup.find_all('tr', bgcolor=bgcolor[1])
    for i in a:
        detail.append(i)
    for i in b:
        detail.append(i)

    # 每1000頁重開一次瀏覽器
    if test % 1000 == 0:
        driver.close()
        driver = webdriver.Chrome()

    for every in detail:
        take = []  # 正取或備取
        number = []  # 報名序號
        school = []  # 學校
        name = []  # 名字
        admission = []  # 入取學校

        # 抓取標籤
        All = every.find_all('div', align="left")
        school_and_department = every.find_all('a')
        take_data = All[0].find_all('div', align="center")  # 找出備取或正取 (第1個到最後)
        number_data = every.find_all('td', width="30%")  # 找出報名序號 (第0個)
        name_and_admission = every.find_all('td', width="5%")  # 找出名字 (第0個) 找出入取學校(第1個到最後)

        # 入取學校
        for i in range(1, len(name_and_admission)):
            img = name_and_admission[i].find_all('img', align="absbottom")
            if len(img) != 0:
                admission.append('True')
            else:
                admission.append(' ')
        # 正取或備取
        for i in range(1, len(take_data)):
            take.append(take_data[i].text)

        # 報名學校和報名科系
        for i in school_and_department:
            i = i.text.replace('\n', '')
            school.append(i)

        # 報名序號和名字
        for i in range(0, len(school)):
            name.append(name_and_admission[0].text)
            number.append(number_data[0].text)

        for i in range(0, len(name)):
            # 將資料存入資料庫
            cursor.executemany(f"INSERT INTO test_{year} VALUES (%d, %s, %s, %s, %s, %s)",
                               [(ID, number[i], name[i], school[i], admission[i], take[i])])
            conn.commit()
            ID += 1

driver.close()
conn.close()

print("已完成")