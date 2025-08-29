# -*- coding: utf-8 -*-

import requests
import base58
import json
import time

# --- 配置区 ---
URLS_TO_FETCH = [
    "https://raw.githubusercontent.com/cmliu/cmliu/refs/heads/main/tvapi_config_json",
    "https://gist.githubusercontent.com/senshinya/5a5cb900dfa888fd61d767530f00fc48/raw/gistfile1.txt"
    # 如果有更多链接，可以继续在这里添加
]

# --- 白名单配置 ---
# 脚本将只从解码后的内容中寻找并保留这些顶级键
ALLOWED_TOP_LEVEL_KEYS = {
    "cache_time", 
    "api_site"
}


OUTPUT_FILENAME = "config.json"
MAX_RETRIES = 3
RETRY_DELAY = 5

def fetch_and_decode_url(url):
    """
    从URL获取内容，解码，并根据白名单进行过滤。
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

            # 根据白名单过滤解码后的数据
            if isinstance(data, dict):
                filtered_data = {
                    key: data[key] for key in ALLOWED_TOP_LEVEL_KEYS if key in data
                }
                
                if not filtered_data:
                    print("警告: 解码后的内容中未找到任何白名单指定的键。")
                    return None
                
                print(f"内容已按白名单过滤，保留键: {list(filtered_data.keys())}")
                return filtered_data
            else:
                print("警告: 解码后的内容不是一个可按键过滤的字典。")
                return None

        except Exception as e:
            print(f"错误: 处理来自 {url} 的内容时出错: {e}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
            
    print(f"错误: 在 {MAX_RETRIES} 次尝试后，仍然无法处理链接: {url}")
    return None

def main():
    """
    主执行函数
    """
    print("--- 开始更新配置文件 ---")
    
    clean_data_buffer = []
    for url in URLS_TO_FETCH:
        filtered_content = fetch_and_decode_url(url)
        if filtered_content:
            clean_data_buffer.append(filtered_content)

    if not clean_data_buffer:
        print("错误: 所有链接内容均为空或无法按规则过滤，无法生成配置文件。")
        return

    print(f"\n过滤完成，共获得 {len(clean_data_buffer)} 组有效内容。准备合并...")

    # --- 核心改动：合并所有 api_site 内容 ---

    # 1. 创建一个空的字典，用于存放所有合并后的 api_site 内容
    merged_api_sites = {}

    # 2. 遍历从所有链接中获取的干净数据
    for item in clean_data_buffer:
        # 确认 item 中有 "api_site" 并且其内容是一个字典
        if "api_site" in item and isinstance(item.get("api_site"), dict):
            # 使用 update 方法将当前链接的 api_site 内容合并进去
            merged_api_sites.update(item["api_site"])

    # 3. 决定最终的 cache_time
    # 从所有链接中寻找第一个有效的 cache_time 值，如果都找不到，则使用默认的 7200
    first_valid_cache_time = next((item.get("cache_time") for item in clean_data_buffer if "cache_time" in item), 7200)
    
    # 4. 构建最终的配置文件结构
    final_config = {
        "cache_time": first_valid_cache_time,
        "api_site": merged_api_sites  # 使用我们刚刚合并好的字典
    }

    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            # json.dump 会自动处理好所有的括号和逗号
            json.dump(final_config, f, indent=4, ensure_ascii=False)
        print(f"成功！所有内容已合并并按指定格式写入文件: {OUTPUT_FILENAME}")
    except IOError as e:
        print(f"错误: 写入文件 {OUTPUT_FILENAME} 失败: {e}")

    print("--- 更新任务结束 ---")

if __name__ == "__main__":
    main()
