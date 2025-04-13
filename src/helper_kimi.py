import selenium
from helper_chrome_driver import 基本爬虫
from helper_xlsx import 保存聊天会话df
from my_project.settings import CONFIGS, BASE_DIR
import pandas
import time
from selenium.webdriver.common.keys import Keys
from tool_kimi_results import 读取系统剪贴板,解析kimi表格,增加n行
from tool_static import 得到一个不重复的文件路径, 路径到链接
def 打开提示词表():
    # fpath = BASE_DIR / "健康会话模版.xlsx"
    fpath = BASE_DIR / "tpl3.xlsx"
    return pandas.read_excel(fpath, sheet_name="提示词", header=0)


class Kimi爬虫(基本爬虫):
    home_page = "https://kimi.moonshot.cn/chat/cvridgn6o68u1lgcdld0"
    default_driver_path = CONFIGS.get("driver_path")
    default_user_data_dir = CONFIGS.get("user_data_dir")

    提示词表 = 打开提示词表()

    @property
    def 初次加好友会话制作提示词(self):
        return self.提示词表[self.提示词表.名称 == "初次加好友"].内容.iloc[0]

    def 输入提示词(self, 提示词, 提交=True):
        e = self.find_element_xpath(
            '//div[@class="chat-input-editor-container"]/div[@role="textbox"]',
            wait_seconds=10,
        )
        self.清空输入框(e)

        lines = 提示词.splitlines()

        lines = filter(lambda x: x.strip(), lines)

        for line in lines:
            e.send_keys(line)
            time.sleep(0.1)
            e.send_keys(Keys.SHIFT + Keys.ENTER)

        if 提交:
            e.send_keys(Keys.ENTER)

    def 制作初次加好友会话(self):
        self.输入提示词(self.初次加好友会话制作提示词, 提交=True)

    def 获取制作的表格内容(self):
        """//*[@id="app"]/div/div/div[2]/div/div/div[1]/div[3]/div[2]/div[2]/div[2]/div[3]/div"""
        """<div data-v-fca19cf8="" class="send-button">
        <svg data-v-fca19cf8="" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" name="stop" class="send-icon iconify" width="1em" height="1em" viewBox="0 0 1024 1024">
        <path d="M331.946667 379.904c-11.946667 23.466667-11.946667 54.186667-11.946667 115.626667v32.938666c0 61.44 0 92.16 11.946667 115.626667 10.538667 20.650667 27.306667 37.418667 47.957333 47.957333 23.466667 11.946667 54.186667 11.946667 115.626667 11.946667h32.938666c61.44 0 92.16 0 115.626667-11.946667 20.650667-10.538667 37.418667-27.306667 47.957333-47.957333 11.946667-23.466667 11.946667-54.186667 11.946667-115.626667v-32.938666c0-61.44 0-92.16-11.946667-115.626667a109.696 109.696 0 0 0-47.957333-47.957333c-23.466667-11.946667-54.186667-11.946667-115.626667-11.946667h-32.938666c-61.44 0-92.16 0-115.626667 11.946667-20.650667 10.538667-37.418667 27.306667-47.957333 47.957333z" fill="currentColor"></path></svg></div>
        
        <path d="M705.536 433.664a38.4 38.4 0 1 1-54.272 54.272L550.4 387.114667V729.6a38.4 38.4 0 0 1-76.8 0V387.114667l-100.864 100.821333a38.4 38.4 0 1 1-54.272-54.272l166.4-166.4a38.4 38.4 0 0 1 54.272 0l166.4 166.4z" fill="currentColor"></path>
        
        """
        # e = self.find_element_xpath('''//div[@class="send-button"]/svg/path[start-swith(@d,"M705")]''')
        # return self.find_element_css('''div.send-button > svg > path[d^="M331.946667"]''', wait_seconds=1)
        # return self.find_element_css('''div.send-button > svg > path[d^="M705.536 433"]''', wait_seconds=1)
        # return self.driver.find_element(By.CSS_SELECTOR,'''div.send-button > svg > path[d^="M331.946667"]''')
        # return self.driver.find_element(By.CSS_SELECTOR,'''div.send-button > svg > path[d^="M705.536 433."]''')

        self.制作初次加好友会话()
        while self.是否制作中():
            print("正在制作...")
            time.sleep(1)
        e = self.寻找最后一个复制()
        assert e is not None,' 没有找到最后一个复制'
        self.光标移到元素(e)

        old = 读取系统剪贴板()
        e.click()
        time.sleep(0.1)
        new = 读取系统剪贴板()
        assert old != new,' 没有复制成功'
        print(new)
        return 解析kimi表格(new)

    # def 生成excel会话文件(self, fpath):
    #     df = self.获取制作的表格内容()
    #     保存聊天会话df(fpath, df)
    def 获取制作的表格内容并存储到excel文件中(self):
        df = self.获取制作的表格内容()
        fpath = 得到一个不重复的文件路径(".xlsx")
        保存聊天会话df(fpath, 增加n行(df, 10))
        return 路径到链接(fpath)

    def 是否制作中(self):
        try:
            return self.find_element_css('''div.send-button > svg > path[d^="M331.946667"]''', wait_seconds=1) is not None
        except selenium.common.exceptions.TimeoutException as e:
            return False

    def 寻找最后一个复制(self):
        l = self.find_elements_xpath(
            '//div[@class="table"]//div[contains(@class,"simple-button")]/span[text()="复制"]'
        )
        return l[-1] if l else None
