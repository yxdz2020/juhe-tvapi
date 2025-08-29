# -*- coding: utf-8 -*-

import requests  # 用于发起网络请求
import base58    # 用于 Base58 解码
import json      # 用于处理 JSON 数据
import time      # 用于在重试之间添加延迟

# --- 配置区 ---
# 请将下面的链接替换为您需要读取的实际链接
URLS_TO_FETCH = [
    "https://example.com/your-first-encoded-content-url",
    "https://example.com/your-second-encoded-content-url"
    # 如果有更多链接，可以继续在这里添加
]

OUTPUT_FILENAME = "config.json"
MAX_RETRIES = 3 # 定义请求失败时的最大重试次数
RETRY_DELAY = 5 # 定义每次重试之间的延迟（秒）

def fetch_and_decode_url(url):
    """
    从给定的 URL 获取内容，进行 Base58 解码，并解析为 Python 字典。
    增加了重试逻辑以提高脚本的稳定性。
    """
    for attempt in range(MAX_RETRIES):
        try:
            print(f"正在尝试第 {attempt + 1}/{MAX_RETRIES} 次请求链接: {url}")
            # 发起 GET 请求，设置一个超时时间以防请求卡住
            response = requests.get(url, timeout=15)
            # 如果请求失败 (例如 404, 500 错误)，则抛出异常
            response.raise_for_status()

            # 1. 读取链接内容 (Base58 编码的字符串)
            encoded_content = response.text.strip()
            if not encoded_content:
                print(f"警告: 从 {url} 获取的内容为空。")
                return None

            # 2. 用 Base58 解码
            # Base58 解码后得到的是 bytes 类型
            decoded_bytes = base58.b58decode(encoded_content)
            # 将 bytes 转为 utf-8 编码的字符串
            decoded_string = decoded_bytes.decode('utf-8')

            # 假设解码后的内容是 JSON 格式的字符串，我们将其解析为 Python 字典
            data = json.loads(decoded_string)
            print(f"成功解码链接内容: {url}")
            return data

        except requests.exceptions.RequestException as e:
            print(f"错误: 请求链接 {url} 失败: {e}")
        except Exception as e:
            # 捕获其他可能的错误，例如 Base58 解码失败或 JSON 解析失败
            print(f"错误: 处理来自 {url} 的内容时出错: {e}")
        
        # 如果不是最后一次尝试，则等待一段时间后重试
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
    
    # 3. 先保存到缓存区 (这里用一个列表作为缓存区)
    decoded_data_buffer = []

    for url in URLS_TO_FETCH:
        decoded_content = fetch_and_decode_url(url)
        if decoded_content:
            # 只有成功解码并解析的内容才会被添加到缓存区
            decoded_data_buffer.append(decoded_content)

    # 4. 等所有的链接内容解码完成
    if not decoded_data_buffer:
        print("错误: 所有链接均未能成功获取和解码内容，无法生成配置文件。")
        return

    print("\n所有链接内容已成功解码，准备合并...")

    # 5. 把所有的链接内容合并
    # 假设每个解码后的内容都是一个字典，我们将它们合并到一个新的字典中
    # 如果不同来源有相同的键 (key)，后来的会覆盖先来的
    merged_config = {}
    for data_part in decoded_data_buffer:
        if isinstance(data_part, dict):
            merged_config.update(data_part)
        else:
            print(f"警告: 解码后的部分内容不是一个字典，将跳过合并: {data_part}")


    # 6. 保存到 config.json
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            # 使用 json.dump 写入文件
            # indent=4 让 JSON 文件格式化，更易读
            # ensure_ascii=False 确保中文等非 ASCII 字符能正确显示而不是被转义
            json.dump(merged_config, f, indent=4, ensure_ascii=False)
        print(f"成功！所有内容已合并并保存到文件: {OUTPUT_FILENAME}")
    except IOError as e:
        print(f"错误: 写入文件 {OUTPUT_FILENAME} 失败: {e}")

    print("--- 更新任务结束 ---")


if __name__ == "__main__":
    main()
