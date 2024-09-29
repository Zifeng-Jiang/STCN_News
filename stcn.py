from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from lxml import html
from datetime import datetime, timedelta
import time

def scrape_content(driver, link):
    driver.get(link)
    time.sleep(1)  # 等待页面加载
    content_source = driver.page_source
    content_tree = html.fromstring(content_source)

    # 使用 XPath 提取非表格和非 script 标签的文本内容
    paragraphs = content_tree.xpath('/html/body/div[2]/div[2]/div[1]/div[3]/div[2]//text()[not(ancestor::div[contains(@class, "table")]) and not(ancestor::script)]')
    content = ' '.join([text.strip() for text in paragraphs if text.strip()])

    # 定义多个可能的日期 XPath 并尝试提取
    date_xpaths = [
        '/html/body/div[2]/div[2]/div[1]/div[2]/span[3]',  # 第一种可能的 XPath
        '/html/body/div[2]/div[2]/div[1]/div[2]/span[2]',  # 第二种可能的 XPath
    ]
    
    # 初始化日期为 None
    news_date = None
    
    # 尝试从多个 XPath 中提取日期
    for xpath in date_xpaths:
        date_str = content_tree.xpath(f'string({xpath})').strip()
        if date_str:
            try:
                # 尝试解析日期字符串
                news_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                break  # 找到有效日期后停止
            except ValueError:
                print(f"无法解析日期: {date_str}")

    return content, news_date

def get_dynamic_content(key_word):
    # 设置 Selenium WebDriver
    options = Options()
    options.add_argument("--headless")  # 设置为无头模式
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--ignore-certificate-errors")  # 禁用 SSL 验证
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("--window-size=1400,1000")  # 设置窗口大小

    driver = webdriver.Chrome(service=ChromeService(), options=options)

    # 打开目标网页
    url = f"https://stcn.com/article/search.html?search_type=news&keyword={key_word}&uncertainty=1&sorter=time"
    driver.get(url)

    # 等待页面动态加载内容
    time.sleep(3)

    # 获取加载后的页面内容
    page_source = driver.page_source

    # 解析页面内容
    tree = html.fromstring(page_source)

    # 获取当前时间和三天前的时间
    time_threshold = datetime.now() - timedelta(days=3)

    # 抓取新闻条目
    news_items = tree.xpath('//ul[@class="list infinite-list"]/li')
    print(f"Found {len(news_items)} news items")

    news_list = []

    # 提取每条新闻的标题、摘要、链接和标签
    for index, item in enumerate(news_items):
        title = item.xpath('string(.//div[@class="tt"]/a)')
        link = item.xpath('.//div[@class="tt"]/a/@href')

        title = title.strip() if title else '无标题'
        link = link[0].strip() if link else '无链接'

        # 确保链接是完整的
        if not link.startswith(('http://', 'https://')):
            link = f"https://stcn.com{link}"  # 构建完整的链接

        # 提取摘要
        summary = item.xpath('string(.//div[@class="desc"] | .//div[2])')
        summary = summary.strip() if summary else '无摘要'

        # 提取所有标签
        tags = item.xpath('.//div[@class="tags"]//span/text()')
        tags = ', '.join([tag.strip() for tag in tags if tag.strip()]) or '无标签'

        # 爬取新闻内容和日期
        content, news_date = scrape_content(driver, link)

        # 检查新闻日期是否在三天内
        if news_date and news_date < time_threshold:
            print(f"Skipping old news: {news_date}")
            continue

        # 打印提取的内容
        print(f"Title: {title}")
        print(f"Link: {link}")
        print(f"Summary: {summary}")
        print(f"Date: {news_date.strftime('%Y-%m-%d %H:%M') if news_date else '无日期'}")
        print(f"Tags: {tags}")
        print(f"Content: {content}")
        print('-' * 50)

        # 将新闻信息存储在字典中
        news_list.append({
            'keyword': key_word,
            'title': title,
            'link': link,
            'summary': summary,
            'date': news_date.strftime('%Y-%m-%d %H:%M') if news_date else '无日期',
            'tags': tags,
            'content': content
        })

    # 关闭浏览器
    driver.quit()
    
    return news_list
