"""
@filename:RRR.py
@author:dying
@time:2024-05-24
"""
import re
from collections import Counter
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
import csv
import requests
from lxml import etree
import time

# 基础URL
base_url = "https://nanjing.zu.fang.com/house/pn{}"

# 记录所有的链接
links = []
# 记录所有的结果
result_list = []

header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/64.0.3282.186 Safari/537.36'}


# 获取当前页面下有关租房信息的链接
def get_link(url):
    resp = requests.get(url)
    resp_context = resp.text
    soup = BeautifulSoup(resp_context, 'html.parser')

    # 找到所有包含链接的dl元素
    dl_elements = soup.find_all('dl', class_='list hiddenMap rel')

    # 提取链接并存入列表
    for dl in dl_elements:
        a_tag = dl.find('a')
        if a_tag:
            link = urljoin(url, a_tag['href'])
            links.append(link)

    """
    根据传入的URL，使用requests库发送GET请求，并解析返回的HTML页面。
    若返回的页面标题为"跳转..."，则使用正则表达式解析页面中的JavaScript代码，获取新的URL，并重新发送GET请求。
    若返回的页面标题为"访问验证-房天下"，则不进行任何处理。

    Args:
    - url (str): 目标页面的URL地址。

    Returns:
    - BeautifulSoup: 解析后的HTML页面对象。

    """
def get_real(url):
    resp = requests.get(url, headers=header)
    soup = BeautifulSoup(resp.content, 'html.parser', from_encoding='gb18030')
    if soup.find('title').text.strip() == '跳转...':

        pattern1 = re.compile(r"var t4='(.*?)';")
        script = soup.find("script", text=pattern1)
        t4 = pattern1.search(str(script)).group(1)

        pattern1 = re.compile(r"var t3='(.*?)';")
        script = soup.find("script", text=pattern1)
        t3 = re.findall(pattern1, str(script))[-2]
        url = t4 + '?' + t3
        HTML = requests.get(url, headers=header)
        soup = BeautifulSoup(HTML.content, 'html.parser', from_encoding='gb18030')
    elif soup.find('title').text.strip() == '访问验证-房天下':
        pass

    return soup


def clean(data):
    return ''.join(data.split())


# 访问不同的页码
urls = [base_url.format(i) for i in range(1, 11)]
for url in urls:
    get_link(url)

for i, url in enumerate(links, start=1):
    print(f'>>> 正在获取 {url}')
    trline = []
    trlitem = []
    soup = get_real(url)
    trline = soup.find_all('div', class_='tr-line clearfix')
    trlitem = soup.find_all('div', class_='trl-item2 clearfix')
    if len(trlitem) == 2:
        trlitem.append(trlitem[1])
        trlitem[1] = None
        distance = None
    else:
        distance = trlitem[1].find('div', class_='rcont').find('a').getText().strip()

    facilities = soup.find('div', class_='content-item zf_new_ptss')
    if facilities is not None:
        facilities_cleaned = clean(facilities.find('div', class_='cont clearfix').getText().strip())

    highlights = soup.find('div', class_='fyms_con floatl gray3').getText().strip()
    highlights_cleaned = clean(highlights)

    result = {
        "序号": i,

        "城市": "南京",

        "房屋租金": soup.find('div', class_='trl-item sty1').find('i').getText().strip(),

        "支付方式": soup.find('div', class_='trl-item sty1').find('a').getText().strip(),

        "出租方式": trline[0].find('div', class_='trl-item1 w146').find('div', class_='tt').
        find('a').getText().strip(),

        "房屋户型": trline[0].find('div', class_='trl-item1 w182').find('div', class_='tt').
        getText().strip(),

        "房屋面积": trline[0].find('div', class_='trl-item1 w132').find('div', class_='tt').
        getText().strip(),

        "房屋朝向": trline[1].find('div', class_='trl-item1 w146').
        find('div', class_='tt').getText().strip(),
        "楼层": trline[1].find('div', class_='trl-item1 w182').
        find('div', class_='tt').getText().strip(),

        "房屋专修": trline[1].find('div', class_='trl-item1 w132').
        find('div', class_='tt').getText().strip(),

        "小区": trlitem[0].find('div', class_='rcont').find('a').getText().strip(),

        "距地铁的距离": distance,

        "地址": trlitem[2].find('div', class_='rcont').find('a').getText().strip(),

        "配套设施": facilities_cleaned,

        "房源亮点": highlights_cleaned
    }
    if trlitem[1] is not None:
        result["距地铁的距离"] = trlitem[1].find('div', class_='rcont').find('a').getText().strip()
    else:
        result["距地铁的距离"] = "None"

    print(result)
    result_list.append(result)
    time.sleep(5)  # 为了避免给网站造成过多负担，可以添加适当的延迟



print(result_list)
# 将字典列表写入CSV文件
fieldnames = ['序号', '城市', '房屋租金', '支付方式', '出租方式', '房屋户型', '房屋面积', '房屋朝向', '楼层',
              '房屋专修', '小区', '距地铁的距离', '地址', '配套设施', '房源亮点']

with open('rent_data.csv', mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)

    # 写入表头
    writer.writeheader()

    # 写入数据
    for data in result_list:
        writer.writerow(data)
