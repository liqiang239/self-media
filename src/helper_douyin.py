from helper_toutiao import 头条爬虫

from tool_douyin import 得到视频后缀
from tool_static import 得到一个不重复的文件路径, 路径到链接

import requests

from selenium.webdriver.common.keys import Keys


from requests.cookies import RequestsCookieJar
import time

class 抖音爬虫(头条爬虫):
    home_page = "https://www.douyin.com/?recommend=1"

    @classmethod
    def 从头条爬虫单例拷贝实例(cls):
        return cls.copy_driver(头条爬虫.得到爬虫单例())

    @property
    def headers(self):
        return {
            "User-Agent": self.driver.execute_script("return navigator.userAgent"),
            "Referer": self.driver.current_url,
        }

    @property
    def cookie_jar(self):
        # 初始化 Selenium 并获取 Cookie
        selenium_cookies = self.driver.get_cookies()

        # 将 Selenium Cookie 转换为 requests 的 CookieJar
        cookie_jar = RequestsCookieJar()
        for cookie in selenium_cookies:
            cookie_jar.set(
                name=cookie["name"],
                value=cookie["value"],
                domain=cookie.get("domain"),  # 确保 domain 匹配目标 URL
                path=cookie.get("path", "/"),
            )
        return cookie_jar

    def download_video(self, video_url):
        fpath = 得到一个不重复的文件路径(得到视频后缀(video_url))
        response = requests.get(
            video_url, headers=self.headers, cookies=self.cookie_jar, stream=True
        )
        with open(fpath, "wb") as fp:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    fp.write(chunk)
        return 路径到链接(fpath)

    def 移动鼠标到筛选(self):
        c = "#search-content-area > div > div.eVQDrSwo > div.qWNh2IMg.CRPlkYAk.j7kc7ENz > div > div > div > div.jjU9T0dQ > span"
        # self.move_to_element(self.find_element_xpath('//div[@data-e2e="searchbar-filter-icon"]'))
        # self.find_element_xpath('//span[text()="全部"]').click(
        self.hover(c)

    def 点击视频tab(self):
        # search-content-area > div > div.eVQDrSwo > div.qWNh2IMg.CRPlkYAk.j7kc7ENz > div > div > div > span:nth-child(2)
        self.find_element_xpath('//span[text()="视频"][@data-key="video"]').click()

    def 点击最多点赞选项(self):
        self.find_element_xpath(
            '//*[@id="search-content-area"]//span[text()="最多点赞"]'
        ).click()

    def 点击一周内选项(self):
        self.find_element_xpath(
            '//*[@id="search-content-area"]//span[text()="一周内"]'
        ).click()

    def 获取所有结果卡片(self):
        x = '//*[@id="search-result-container"]/div/ul/li/div[@class="search-result-card"]/a'
        return list(map(lambda e: e.get_attribute("href"), self.find_elements_xpath(x)))

    def 搜索相关视频链接(self, title="男子抛弃妻儿16年后起诉儿子要赡养费"):
        input_element = self.find_element_xpath('//input[@data-e2e="searchbar-input"]')
        input_element.send_keys(Keys.CONTROL + "a")  # 全选
        input_element.send_keys(Keys.BACKSPACE)  # 删除
        input_element.send_keys(title)
        self.find_element_xpath('//button[@data-e2e="searchbar-button"]').click()
        self.点击视频tab()
        self.移动鼠标到筛选()
        self.点击最多点赞选项()
        self.点击一周内选项()
        return self.获取所有结果卡片()

    def 从日志中搜索视频地址(self):
        # 'https://v3-web.douyinvod.com/dc7277b976396a8a34fd5f2fe60fcab6/67dbeeec/video/tos/cn/tos-cn-ve-0015c800/4a64aae2eeaf4cd8a0b24df32a61039e/?a=6383&ch=26&cr=3&dr=0&lr=all&cd=0%7C0%7C0%7C3&cv=1&br=648&bt=648&cs=0&ds=3&ft=AJkeU_TERR0s~dC52Dv2Nc0iPMgzbLKJxO1U_4~fCjV9Nv7TGW&mime_type=video_mp4&qs=0&rc=ZTVmM2hmZ2ZnaTRpOzk8ZUBpam51cmQ6ZjM1ODMzNGkzM0BjYjUuLmFiNl4xMl5jNV81YSMxXmxkcjRva21gLS1kLS9zcw%3D%3D&btag=c0000e00030000&cquery=100o_100w_100B_100D_102u&dy_q=1742455694&l=202503201528148FD1EBC239B6CF01CA6C&__vid=7021722422260911390'
        time.sleep(5)
        self.刷新日志()
        q = list(self.得到所有网络请求的url以及请求id(self.logs))
        for x in q:
            if x[0].startswith("https://v3-web.douyinvod.com/") and "__vid=" in x[0]:
                return x[0]
            

    def 下载抖音视频(self, url):
        self.go(url)
        video_url = self.从日志中搜索视频地址()
        print('aaa:', video_url)
        return self.download_video(video_url)
