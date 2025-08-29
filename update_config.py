# -*- coding: utf-8 -*-

import requests  # 用于发起网络请求
import base58    # 用于 Base58 解码
import json      # 用于处理 JSON 数据
import time      # 用于在重试之间添加延迟

# --- 配置区 ---
# 请将下面的链接替换为您需要读取的实际链接
URLS_TO_FETCH = [
    "https://raw.githubusercontent.com/cmliu/cmliu/refs/heads/main/tvapi_config_json",
    "https://gist.githubusercontent.com/senshinya/5a5cb900dfa888fd61d767530f00fc48/raw/gistfile1.txt"
    # 如果有更多链接，可以继续在这里添加
]

OUTPUT_FILENAME = "config.json"
MAX_RETRIES = 3 # 定义请求失败时的最大重试次数
RETRY_DELAY = 5 # 定义每次重试之间的延迟（秒）

def fetch_and_decode_url(url):
    """
    从给定的 URL 获取内容，进行 Base58 解码，并解析为 Python 对象（通常是字典）。
    """
    for attempt in range(MAX_RETRIES):
        try:
            print(f"正在尝试第 {attempt + 1}/{MAX_RETRIES} 次请求链接: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()

            encoded_content = response.text.strip()
            if not encoded_content:
                print(f"警告: 从 {url} 获取的内容为空。")
                return None

            decoded_bytes = base58.b58decode(encoded_content)
            decoded_string = decoded_bytes.decode('utf-8')
            data = json.loads(decoded_string)
            print(f"成功解码链接内容: {url}")
            return data

        except requests.exceptions.RequestException as e:
            print(f"错误: 请求链接 {url} 失败: {e}")
        except Exception as e:
            print(f"错误: 处理来自 {url} 的内容时出错: {e}")
        
        if attempt < MAX_RETRIES - 1:
            print(f"将在 {RETRY_DELAY} 秒后重试...")
            time.sleep(RETRY_DELAY)
            
    print(f"错误: 在 {MAX_RETRIES} 次尝试后，仍然无法处理链接: {url}")
    return None

def main():
    """
    主执行函数
    """
    print("--- 开始更新配置文件 ---")
    
    # 缓存区，用于存储从每个链接解码后的数据
    decoded_data_buffer = []

    for url in URLS_TO_FETCH:
        decoded_content = fetch_and_decode_url(url)
        if decoded_content: # 确保解码内容不为空
            decoded_data_buffer.append(decoded_content)

    if not decoded_data_buffer:
        print("错误: 所有链接均未能成功获取和解码内容，无法生成配置文件。")
        return

    print(f"\n解码完成，共获得 {len(decoded_data_buffer)} 项内容。准备合并...")

    # --- 这里是核心改动 ---

    # 1. 将所有解码后的字典内容合并成一个单一的字典
    #    这会把所有影视源都放在同一个层级下
    merged_api_sites = {}
    for data_part in decoded_data_buffer:
        if isinstance(data_part, dict):
            merged_api_sites.update(data_part)
        else:
            print(f"警告: 解码后的部分内容不是一个字典，将跳过合并: {data_part}")

    # 2. 定义您的固定模板
    final_config = {
        "cache_time": 7200,
        "api_site": {} # 先创建一个空的 api_site
    }

    # 3. 将合并后的影视源内容放入模板的 "api_site" 键中
    final_config["api_site"] = merged_api_sites

    # 4. 将最终构成的完整对象写入文件
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(final_config, f, indent=4, ensure_ascii=False)
        print(f"成功！内容已按模板格式保存到文件: {OUTPUT_FILENAME}")
    except IOError as e:
        print(f"错误: 写入文件 {OUTPUT_FILENAME} 失败: {e}")

    print("--- 更新任务结束 ---")

if __name__ == "__main__":
    main()
