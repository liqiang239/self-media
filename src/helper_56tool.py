import selenium
from helper_chrome_driver import 基本爬虫
from helper_xlsx import 保存聊天会话df
from my_project.settings import CONFIGS, BASE_DIR
import pandas
import time
from selenium.webdriver.common.keys import Keys
from tool_kimi_results import 读取系统剪贴板,解析kimi表格,增加n行
from tool_static import 得到一个不重复的文件路径, 路径到链接
import pyperclip

def 读取系统剪贴板():
    text = pyperclip.paste()
    return text

class InvalidVideoUrlError(Exception):
    pass


class ParseUrlError(Exception):
    pass


class 灵动爬虫(基本爬虫):
    home_page = "https://www.56tool.com/multimediaCopywritingExtraction"
    default_driver_path = CONFIGS.get("driver_path")
    default_user_data_dir = CONFIGS.get("user_data_dir")


    def 检查提交结果(self):

        try:
            invalid_url_error = self.find_element_xpath('//span[text()="请输入正确的视频链接"]|//span[text()="请先填写视频链接"]', 2)
            if invalid_url_error:
                raise InvalidVideoUrlError
        except selenium.common.exceptions.TimeoutException:
            pass



    def 是否解析中(self):
        try:
            解析中 = self.find_element_xpath('//div[starts-with(text(), "解析中")]', 1)
            return 解析中 is not None
        except selenium.common.exceptions.TimeoutException as e:
            return False

    def 检查提取异常(self):
        """解析步骤执行以后返回的错误"""
        try:
            e = self.find_element_xpath('//span[text()="提取字幕异常"]', 2)
            if e:
                raise ParseUrlError

        except selenium.common.exceptions.TimeoutException as e:
            return False


    def 提取视频文案(self, video_url):
        e_input = self.find_element_xpath('//div[@class="leftCard mw-card h-full"]//textarea')
        self.清空输入框(e_input)
        e_input.send_keys(video_url)
        e_submit = self.find_element_xpath('//div[@class="leftCard mw-card h-full"]//button[starts-with(@class, "arco-btn arco-btn-primary")]')
        e_submit.click()
        print('提交, 检查提示文字')
        self.检查提交结果()
        print('检查是否解析中')
        while self.是否解析中():
            print("解析中...")
            time.sleep(1)

        self.检查提取异常()


        print('解析完成')
        copy_txt_btn = self.find_element_xpath('//button[text()="复制文案"]')
        copy_txt_btn.click()

        subtitle = 读取系统剪贴板()
        return subtitle