"""
Created on 2024 Nov 10

@author: Winston
"""

import base64
from io import BytesIO
import json
import re
import time

from PIL import Image
from django.utils.functional import cached_property
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

from helper_chrome_driver import get_driver_new, get_driver_service

from selenium.webdriver.support import expected_conditions as EC
from my_project.settings import CONFIGS


def base64_to_image(base64_str):
    base64_data = re.sub("^data:image/.+;base64,", "", base64_str)
    byte_data = base64.b64decode(base64_data)
    image_data = BytesIO(byte_data)
    img = Image.open(image_data)
    return img


class 头条爬虫(object):
    home_page = "https://www.toutiao.com"
    分类榜单页面 = "https://api.toutiaoapi.com/feoffline/hotspot_and_local/html/hot_list_new/index.html?category_name="
    单例 = None
    def __init__(
        self,
        headless=False,
        driver=None,
        logs=None,
        implicitly_wait_seconds=0,
        driver_path=None,
        user_data_dir=None,
    ):
        self.driver_path = driver_path or CONFIGS.get("driver_path")
        self.user_data_dir = user_data_dir or CONFIGS.get("user_data_dir")

        self.headless = headless
        self.implicitly_wait_seconds = implicitly_wait_seconds

        self._driver = driver if driver is not None else self.get_driver()

        # if logs:
        #     self.logs = logs
        self._logs = logs

        self.网址变更时间 = 0
        self.go_homepage()

    @classmethod
    def 得到爬虫单例(cls):
        if cls.单例 is None:
            cls.单例 = cls()
        return cls.单例
    
    @classmethod
    def 清除单例(cls):
        if cls.单例 is not None:
            单例 = cls.得到爬虫单例()
            单例.quit()
            cls.单例 = None

    
    @classmethod
    def copy_driver(cls, pa):
        return cls(driver=pa.driver)
    
    def 是否停留在主页(self):
        url = self.driver.current_url
        return url and url.startswith(self.home_page)

    def 是否停留在分类榜单页面(self):
        url = self.driver.current_url
        return url and url.startswith(self.分类榜单页面)

    def 加载变化时间(self):
        return time.time() - self.网址变更时间

    def go_homepage(self):
        if not self.是否停留在主页():
            self.go(self.home_page)
        elif self.加载变化时间() > 5:
            self.driver.refresh()
        else:
            print("5秒内已完成打开主页")
            return
        print("========完成打开主页！========")

    def 打开分类榜单页面(self):
        if not self.是否停留在分类榜单页面():
            self.go(self.分类榜单页面)
        elif self.加载变化时间() > 5:
            self.driver.refresh()
        else:
            print("5秒内已完成打开分类榜单页面")
            return
        print("========完成打开主页！========")


    def quit(self):
        self.driver.quit()

    # @cached_property
    # def driver(self):
    #     print("self.driver_path", self.driver_path)
    #     print("self.user_data_dir", self.user_data_dir)
    #     return get_driver_new(
    #         self.headless,
    #         self.implicitly_wait_seconds,
    #         driver_path=self.driver_path,
    #         user_data_dir=self.user_data_dir,
    #     )

    @property
    def driver(self):
        return self._driver
    
    @driver.setter
    def driver(self, value):
        self._driver = value
    
    def get_driver(self):
        print("self.driver_path", self.driver_path)
        print("self.user_data_dir", self.user_data_dir)
        return get_driver_new(
            self.headless,
            self.implicitly_wait_seconds,
            driver_path=self.driver_path,
            user_data_dir=self.user_data_dir,
        )


    def go(self, url):
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                      get: () => undefined
                    })
                  """
            },
        )
        self.driver.get(url)
        WebDriverWait(self.driver, 30).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        self.网址变更时间 = time.time()

    # @cached_property
    # def logs(self):
    #     return self.driver.get_log("performance")

    @property
    def logs(self):
        if self._logs is None:
            self._logs = self.driver.get_log("performance")
        return self._logs
        # return self.driver.get_log("performance")

    @logs.setter
    def logs(self, value):
        self._logs = value

    def 刷新日志(self):
        self.logs = self.driver.get_log("performance")

    def 得到所有网络请求的url以及请求id(self, logs):
        for i in range(len(logs) - 1, -1, -1):
            log = logs[i]
            logjson = json.loads(log["message"])["message"]
            if logjson["method"] == "Network.responseReceived":
                params = logjson["params"]
                try:
                    requestUrl = params["response"]["url"]
                    requestId = params["requestId"]
                    yield requestUrl, requestId
                except:
                    pass

    def 搜索请求(self, url):
        l = self.得到所有网络请求的url以及请求id(self.logs)
        l = filter(lambda x: x[0].startswith(url), l)


        return list(l)

    def 搜索热榜请求(self):
        return self.搜索请求(
            url="https://www.toutiao.com/hot-event/hot-board",
            # logs=logs
        )

    def 搜索分类热榜请求(self):
        return self.搜索请求(
            url="https://api.toutiaoapi.com/api/feed/hotboard_light/v1",
            # logs=logs
        )

    def get_content(self, request_id):
        try:
            response_body = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            return response_body["body"]
        except:
            pass

    def get_json(self, request_id):
        try:
            content = self.get_content(request_id)
            if content is not None:
                return json.loads(content)
        except Exception as e:
            print(e)
        # return []

    def get_image(self, request_id):
        try:
            return base64_to_image(self.get_content(request_id))
        except Exception as e:
            print(e)

    def 得到第一个热榜请求内容(self):
        l = self.搜索热榜请求()
        return self.get_json(l[0][1]) if l else None

    def 得到第一个分类热榜请求内容(self):
        l = self.搜索分类热榜请求()
        return self.get_json(l[0][1]) if l else None


    def 得到所有json(self, url_starts_with):
        for t in self.搜索请求(url_starts_with):
            j = self.get_json(t[1])
            if j is not None:
                yield j

    @property
    def 所有评论(self):
        url = "https://www.toutiao.com/article/v4/tab_comments/?"
        rtn = []
        for d in self.得到所有json(url):
            if d:
                for x in d.get("data"):
                    rtn.append(x.get("comment"))
        return rtn

    @property
    def 所有回复(self):
        url = "https://www.toutiao.com/2/comment/v4/reply_list/?"
        rtn = []
        for d in self.得到所有json(url):
            if d:
                t = d.get("data").get("id_str")
                l = d.get("data", {}).get("data", []) or []
                for x in l:
                    x.update(评_id=t)
                    rtn.append(x)
        return rtn

    @property
    def 第一个查看全部回复(self):
        try:
            return self.driver.find_element(
                By.CSS_SELECTOR, "button.check-more-reply:first-of-type"
            )
        except NoSuchElementException:
            pass

    def 移动到元素(self, e):
        ActionChains(self.driver).move_to_element(e).perform()

    def page_down(self):
        e = self.find_element_css('body')
        ActionChains(self.driver).move_to_element(e).perform()
        e.send_keys(Keys.PAGE_DOWN)
        # for _ in range(5):
        #     e.send_keys(Keys.ARROW_DOWN)
        #     time.sleep(0.5)
        # e.send_keys(Keys.ARROW_DOWN)
        # time.sleep(1)
        # e.send_keys(Keys.ARROW_DOWN)
        # e.send_keys(Keys.END)

    def 得到最大页面高度(self):
        return self.driver.execute_script("return document.body.scrollHeight")

    def 滚动至浏览器底部(self):
        max_height = self.得到最大页面高度()
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(0.5)
        return self.得到最大页面高度() - max_height

    def goto_last_comments(self):
        try:
            e = self.find_element_css("ul.comment-list > li:last-of-type")
            ActionChains(self.driver).move_to_element(e).perform()
            # e = self.find_element_css('body')
            # e.send_keys(Keys.PAGE_DOWN)
        except TimeoutException:
            return False
        return True

    def find(self, by, selector, method, wait_seconds=10):
        return WebDriverWait(self.driver, wait_seconds).until(
            lambda x: getattr(x, method)(by, selector)
        )

    def find_element_css(self, selector, wait_seconds=10):
        # return WebDriverWait(self.driver, wait_seconds).until(lambda x: x.find_element(By.CSS_SELECTOR, selector))
        return self.find(
            By.CSS_SELECTOR, selector, method="find_element", wait_seconds=wait_seconds
        )

    def find_element_xpath(self, selector, wait_seconds=10):
        return self.find(
            By.XPATH, selector, method="find_element", wait_seconds=wait_seconds
        )

    def find_elements_css(self, selector, wait_seconds=10):
        return self.find(
            By.CSS_SELECTOR, selector, method="find_elements", wait_seconds=wait_seconds
        )

    def find_elements_xpath(self, selector, wait_seconds=10):
        return self.find(
            By.XPATH, selector, method="find_elements", wait_seconds=wait_seconds
        )

    def scroll_down(self, scroll_px=500):
        print("scroll down")
        self.driver.execute_script(f"window.scrollBy(0,{scroll_px})")

    def hover(self, s):
        e = self.find_element_css(s)
        ActionChains(self.driver).move_to_element(e).perform()
        return e

    def 切换回爬虫(self):
        window_handles = self.driver.window_handles
        if self.driver.current_window_handle != window_handles[0]:
            self.driver.switch_to.window(window_handles[0])
