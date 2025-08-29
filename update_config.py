# -*- coding: utf-8 -*-
import requests
import base58
import json
import time

# --- 配置区 ---
URLS_TO_FETCH = [
    "https://example.com/your-first-encoded-content-url",  # 这是一个Base58加密的链接
    "https://raw.githubusercontent.com/666zmy/MoonTV/refs/heads/main/config.json", # 这是一个明文JSON链接
    "https://example.com/your-second-encoded-content-url" # 可以混合放置
]

# --- 白名单配置 ---
# 脚本将只从解码后的内容中寻找并保留这些顶级键
ALLOWED_TOP_LEVEL_KEYS = {"cache_time", "api_site"}

OUTPUT_FILENAME = "config.json"
MAX_RETRIES = 3
RETRY_DELAY = 5

def fetch_and_decode_url(url):
    """
    从URL获取内容，智能判断是Base58还是明文JSON，然后解码/解析，并根据白名单进行过滤。
    """
    for attempt in range(MAX_RETRIES):
        try:
            print(f"正在尝试第 {attempt + 1}/{MAX_RETRIES} 次请求链接: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            # 指定编码为 utf-8，避免因服务器未指定编码而导致的乱码问题
            response.encoding = 'utf-8'
            content = response.text.strip()
            
            if not content:
                print(f"警告: 从 {url} 获取的内容为空。")
                return None

            data = None
            # --- 核心改动：智能判断逻辑 ---
            try:
                # 路径1：首先，尝试进行Base58解码
                print("...尝试将内容作为 Base58 解码...")
                decoded_bytes = base58.b58decode(content)
                decoded_string = decoded_bytes.decode('utf-8')
                data = json.loads(decoded_string)
                print("...成功将内容作为 Base58 解码。")
            except Exception:
                # 路径2：如果Base58解码失败，则认为内容是明文JSON
                print("...Base58 解码失败，尝试直接作为明文 JSON 解析...")
                try:
                    data = json.loads(content)
                    print("...成功将内容作为明文 JSON 解析。")
                except json.JSONDecodeError as json_e:
                    # 如果作为JSON解析也失败，说明内容格式有问题
                    print(f"错误: 内容既不是有效的Base58，也不是有效的JSON。错误信息: {json_e}")
                    return None
            
            # --- 后续流程不变 ---
            print(f"成功解析链接内容: {url}")
            if isinstance(data, dict):
                filtered_data = {key: data[key] for key in ALLOWED_TOP_LEVEL_KEYS if key in data}
                if not filtered_data:
                    print("警告: 解析后的内容中未找到任何白名单指定的键。")
                    return None
                print(f"内容已按白名单过滤，保留键: {list(filtered_data.keys())}")
                return filtered_data
            else:
                print("警告: 解析后的内容不是一个可按键过滤的字典。")
                return None

        except requests.exceptions.RequestException as req_e:
            print(f"错误：请求链接失败: {req_e}")
        except Exception as e:
            print(f"错误: 处理来自 {url} 的内容时发生未知错误: {e}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep(RETRY_DELAY)
            
    print(f"错误: 在 {MAX_RETRIES} 次尝试后，仍然无法处理链接: {url}")
    return None

def main():
    """
    主执行函数
    """
    print("--- 开始更新配置文件 ---")
    clean_data_buffer = [content for url in URLS_TO_FETCH if (content := fetch_and_decode_url(url))]
    if not clean_data_buffer:
        print("错误: 所有链接内容均为空或无法按规则过滤，无法生成配置文件。")
        return
    print(f"\n过滤完成，共获得 {len(clean_data_buffer)} 组有效内容。准备通过重命名方式合并...")
    
    # 智能合并，重命名重复项
    merged_api_sites = {}
    for item in clean_data_buffer:
        if "api_site" in item and isinstance(item.get("api_site"), dict):
            for key, value in item["api_site"].items():
                new_key = key
                counter = 2
                while new_key in merged_api_sites:
                    new_key = f"{key}_{counter}"
                    counter += 1
                if new_key != key:
                    print(f"发现重复键 '{key}'，已重命名为 '{new_key}'")
                merged_api_sites[new_key] = value

    first_valid_cache_time = next((item.get("cache_time") for item in clean_data_buffer if "cache_time" in item), 7200)
    final_config = {
        "cache_time": first_valid_cache_time,
        "api_site": merged_api_sites
    }
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(final_config, f, indent=4, ensure_ascii=False)
        print(f"成功！所有内容已通过重命名方式完整写入文件: {OUTPUT_FILENAME}")
    except IOError as e:
        print(f"错误: 写入文件 {OUTPUT_FILENAME} 失败: {e}")
    print("--- 更新任务结束 ---")

if __name__ == "__main__":
    main()
