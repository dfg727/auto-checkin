# -*- coding:utf-8 -*-
# -------------------------------
# @Author : github@wh1te3zzz
# @Time   : 2025-09-01
# NodeLoc 签到脚本 (Playwright 版本)
# -------------------------------
"""
NodeLoc签到
自行网页捉包提取请求头中的cookie和x-csrf-token填到变量 NLCookie 中,用#号拼接，多账号换行隔开
export NL_COOKIE="_t=******; _forum_session=xxxxxx#XXXXXX"

cron: 59 8 * * *
const $ = new Env("NodeLoc签到");
"""
import os
import sys
import time
import logging
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, expect

# 设置环境变量
os.environ['NL_COOKIE'] = '__stripe_mid=3bb726df-555e-4845-87a6-6d02cddd7f301d9852; _forum_session=KBvbBl6YeUw0qpRF8roORWSNXOjjaOn7JBe4qghYFy55kl4qcRynNavNaeiI6hgsPSrKx7ag36f2%2FKLJ9XI%2FPhTFbTpc%2F5OOhI1tauA3zqtASv78OfoYNAlVOqKfAXJiDaBPXMCW1tJX4qiqUrth%2BuBbLFsvecoiEbC4YqryEC79V2bqIBagIs9xWdNfYO%2FOdBFplNU7kntEOD5TIWzi6nKjw6h310vjWraXT4qXNurBTRuEPTtyJOKPNVMBm6dAfDCaN58ji9hCXd%2Fd0uIoD7J2PK3U5Bq2%2Fv8riAAPMLuWrQuYLvkcEX7EElpbTSb%2Bb8PQeItPyrzmaoyXX0IKXJo2cwROzJK6byxTRjuBi4HlJPAMHCs%3D--jESbgitD0JfwA8fI--SZc%2FuVqanDy21vj%2FX85qvQ%3D%3D; __stripe_sid=29b078e5-69af-4c76-b7e2-6e4a16964cf2afaee7; _t=V8d%2Fife3B2eVevgLstAwjFtEwzPAbPXOZaCR9UKcNwPctSuquPww33pzylDo5VicDWcyFnv4tYyZyWvHf%2FIpt5rz%2BGRLcZ7YzOe4xzCL8Tk5LijAU115CDmHcRlJ86ZX7OTA5yvBeAABE57zOXO2q199Oy%2FPrSqgoM64YZLUwi2y9VV3dobgw078ybT0t6VI8S8QhdRgFayKNk%2FnUBqhqa9VwNO1m0xqvZzF7OKy9a18UcGgSi4wDkSxJyRfJun3bJtrj5qXhEAR789t%2BasTScQXHnZLpLJnhuQxEU%2FhQxk%3D--ExZahluZzAExrxc7--HQxLTlKugLIlg%2FbhRwpP1Q%3D%3D'

# ==================== 固定配置 ====================
DOMAIN = "www.nodeloc.com"
HOME_URL = f"https://{DOMAIN}/u/"  # 用户列表页
CHECKIN_BUTTON_SELECTOR = 'li.header-dropdown-toggle.checkin-icon button.checkin-button'
USERNAME_SELECTOR = 'div.directory-table__row.me a[data-user-card]'  # 当前登录用户
SCREENSHOT_DIR = "./photo"
LOG_LEVEL = logging.INFO
# =================================================
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)

results = []

def generate_screenshot_path(prefix: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return os.path.join(SCREENSHOT_DIR, f"{prefix}_{ts}.png")

def get_username_from_user_page(page: Page) -> str:
    log.info("🔍 正在提取用户名...")
    try:
        element = page.wait_for_selector(USERNAME_SELECTOR, timeout=10000)
        username = element.get_attribute("data-user-card")
        return username.strip() if username else ""
    except Exception as e:
        log.error(f"❌ 提取用户名失败: {e}")
        return ""

def check_login_status(page: Page):
    log.debug("🔐 正在检测登录状态...")
    try:
        page.wait_for_selector("div.directory-table__row.me, button.checkin-button", timeout=10000)
        log.info("✅ 登录成功")
        return True
    except Exception as e:
        log.error(f"❌ 登录失败或 Cookie 无效: {e}")
        screenshot_path = generate_screenshot_path('login_failed')
        page.screenshot(path=screenshot_path)
        log.info(f"📸 已保存登录失败截图：{screenshot_path}")
        return False

def setup_browser():
    log.debug("🌐 启动浏览器...")
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--window-size=1920,1080',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-infobars',
                '--disable-popup-blocking'
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        return playwright, browser, context
    except Exception as e:
        log.error(f"❌ 浏览器启动失败: {e}")
        return None, None, None

def hover_checkin_button(page: Page):
    try:
        # 先尝试关闭可能存在的对话框
        try:
            overlay = page.wait_for_selector('div.dialog-overlay', timeout=3000)
            if overlay:
                overlay.click()
                time.sleep(1)
        except:
            pass
        
        button = page.wait_for_selector(CHECKIN_BUTTON_SELECTOR, timeout=10000)
        # 直接点击签到按钮，不进行悬停
        # button.hover()
        time.sleep(1)
    except Exception as e:
        log.warning(f"⚠️ 刷新签到状态失败: {e}")

def browse_topics(page: Page):
    log.info("🔍 开始浏览主题...")
    try:
        # 打开首页
        page.goto(f"https://{DOMAIN}")
        time.sleep(4)
        
        # 获取所有主题链接
        topic_links = page.query_selector_all('a.topic-card__title-link')
        log.info(f"📋 找到 {len(topic_links)} 个主题链接")
        
        # 循环打开每个链接
        for i, link in enumerate(topic_links):
            try:
                href = link.get_attribute('href')
                if not href:
                    continue
                
                # 构建完整链接
                full_link = href if href.startswith('http') else f"https://{DOMAIN}{href}"
                log.info(f"🌐 打开主题 {i+1}/{len(topic_links)}: {full_link}")
                
                # 在新标签页打开
                with page.context.new_page() as new_page:
                    new_page.goto(full_link)
                    time.sleep(4)
                    
                    # 滚动浏览页面
                    scroll_count = 0
                    max_scrolls = 20  # 固定滚动次数
                    
                    while scroll_count < max_scrolls:
                        # 计算滚动位置
                        scroll_position = (scroll_count + 1) * 200
                        log.info(f"📜 滚动页面到位置: {scroll_position}, 滚动次数: {scroll_count}")
                        
                        # 滚动到指定位置
                        new_page.evaluate(f'window.scrollTo(0, {scroll_position})')
                        time.sleep(2)
                        
                        scroll_count += 1
                    
                    # 最后滚动到页面底部
                    log.info("📜 滚动到页面底部")
                    new_page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    time.sleep(2)
                    
                    if scroll_count >= max_scrolls:
                        log.info(f"⚠️ 达到最大滚动次数 {max_scrolls}，停止滚动")
                    
                    # 关闭新标签页
                    new_page.close()
                    time.sleep(1)
                    
            except Exception as e:
                log.warning(f"⚠️ 处理主题链接失败: {e}")
                continue
        
        log.info("✅ 浏览主题完成")
        
    except Exception as e:
        log.error(f"❌ 浏览主题异常: {e}")

def perform_checkin(page: Page, username: str):
    try:
        page.goto("https://www.nodeloc.com/")
        time.sleep(3)
        hover_checkin_button(page)
        button = page.wait_for_selector(CHECKIN_BUTTON_SELECTOR, timeout=10000)

        if "checked-in" in button.get_attribute("class"):
            msg = f"[✅] {username} 今日已签到"
            log.info(msg)
            return False

        log.info(f"📌 {username} - 准备签到")
        button.scroll_into_view_if_needed()
        time.sleep(1)
        button.click()
        time.sleep(3)

        hover_checkin_button(page)

        if "checked-in" in button.get_attribute("class"):
            msg = f"[🎉] {username} 签到成功！"
            log.info(msg)
            return True
        else:
            msg = f"[⚠️] {username} 点击后状态未更新，可能失败"
            log.warning(msg)
            path = generate_screenshot_path("checkin_uncertain")
            page.screenshot(path=path)
            log.info(f"📸 已保存状态存疑截图：{path}")
            return False

    except Exception as e:
        msg = f"[❌] {username} 签到异常: {e}"
        log.error(msg)
        path = generate_screenshot_path("checkin_error")
        try:
            page.screenshot(path=path)
            log.info(f"📸 已保存错误截图：{path}")
        except:
            pass
        return False

def process_account(cookie_str: str):
    cookie = cookie_str.split("#", 1)[0].strip()
    if not cookie:
        log.error("❌ Cookie 为空")
        return False

    playwright = None
    browser = None
    context = None
    try:
        playwright, browser, context = setup_browser()
        if not all([playwright, browser, context]):
            log.error("❌ 浏览器启动失败")
            return False

        log.info("🚀 正在打开用户列表页...")
        page = context.new_page()
        page.goto(HOME_URL)
        time.sleep(3)

        log.info("🍪 正在设置 Cookie...")
        for item in cookie.split("; "):
            item = item.strip()
            if not item or "=" not in item:
                continue
            try:
                name, value = item.split("=", 1)
                context.add_cookies([{
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.nodeloc.com',
                    'path': '/',
                    'secure': True,
                    'httpOnly': False
                }])
            except Exception as e:
                log.warning(f"[⚠️] 添加 Cookie 失败: {item} -> {e}")
                continue

        page.reload()
        time.sleep(5)

        if not check_login_status(page):
            log.error("❌ 登录失败，Cookie 可能失效")
            return False

        username = get_username_from_user_page(page)
        log.info(f"👤 当前用户: {username}")

        if username == "":
            return False

        # result = perform_checkin(page, username)
        # 执行新的浏览主题功能
        browse_topics(page)
        return result

    except Exception as e:
        msg = f"[🔥] 处理异常: {e}"
        log.error(msg)
        return msg
    finally:
        if context:
            try:
                context.close()
            except:
                pass
        if browser:
            try:
                browser.close()
            except:
                pass
        if playwright:
            try:
                playwright.stop()
            except:
                pass

def main():
    global results
    if 'NL_COOKIE' not in os.environ:
        msg = "❌ 未设置 NL_COOKIE 环境变量"
        print(msg)
        results.append(msg)
        sys.exit(1)

    raw_lines = os.environ.get("NL_COOKIE").strip().split("\n")
    cookies = [line.strip() for line in raw_lines if line.strip()]

    if not cookies:
        msg = "❌ 未解析到有效 Cookie"
        print(msg)
        results.append(msg)
        sys.exit(1)

    log.info(f"✅ 查找到 {len(cookies)} 个账号，开始顺序签到...")

    for cookie_str in cookies:
        result = process_account(cookie_str)
        results.append(result)
        time.sleep(5)

    success_count = sum(1 for r in results if r is True)
    fail_count = sum(1 for r in results if r is False)
    log.info(f"✅ 全部执行完成 - 成功: {success_count}, 失败: {fail_count}")

    if success_count == 0:
        log.error("❌ 所有账号签到均失败")
        sys.exit(1)
    elif fail_count > 0:
        log.warning(f"⚠️ 有 {fail_count} 个账号签到失败")
        sys.exit(1)
    else:
        log.info("✅ 所有账号签到成功")
        sys.exit(0)

if __name__ == '__main__':
    main()
