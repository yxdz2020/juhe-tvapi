# -*- coding: utf-8 -*-

import requests
import base58
import json
import time

# --- 配置区 ---
URLS_TO_FETCH = [
    "https://example.com/your-first-encoded-content-url",
    "https://example.com/your-second-encoded-content-url"
]

# --- 新增：白名单配置 ---
# 定义一个“白名单”，只保留我们想要的顶级键（key）
# 脚本将只从解码后的内容中寻找并保留这些键对应的数据
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
            
            # 将解码后的字符串解析为Python字典
            data = json.loads(decoded_string)
            print(f"成功解码链接内容: {url}")

            # --- 核心改动：根据白名单过滤解码后的数据 ---
            if isinstance(data, dict):
                # 创建一个新字典，只包含白名单中存在的键
                filtered_data = {
                    key: data[key] for key in ALLOWED_TOP_LEVEL_KEYS if key in data
                }
                
                if not filtered_data:
                    print("警告: 解码后的内容中未找到任何白名单指定的键。")
                    return None
                
                print(f"内容已按白名单过滤，保留键: {list(filtered_data.keys())}")
                return filtered_data
            else:
                # 如果解码后的内容不是字典，我们无法按键过滤，所以返回空
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
    
    # 这个列表将收集所有经过过滤和清理后的“干净”数据
    clean_data_buffer = []

    for url in URLS_TO_FETCH:
        # fetch_and_decode_url 函数现在返回的是已经过滤好的数据
        filtered_content = fetch_and_decode_url(url)
        if filtered_content:
            clean_data_buffer.append(filtered_content)

    if not clean_data_buffer:
        print("错误: 所有链接内容均为空或无法按规则过滤，无法生成配置文件。")
        return

    print(f"\n过滤完成，共获得 {len(clean_data_buffer)} 组有效内容。准备写入文件...")

    # 我们仍然保持最终模板的结构，但api_site的值是经过清理的数据列表
    # 注意：这里的结构取决于您最终想要一个对象还是多个。
    # 根据我们之前的讨论，使用列表可以完整保留多个链接的内容。
    final_config = {
        # 如果您希望所有内容的cache_time都一样，可以写死
        "cache_time": 7200, 
        # 将所有清理过的数据放入一个列表中
        "api_site": [item.get("api_site", {}) for item in clean_data_buffer if "api_site" in item]
    }
    
    # 如果您的多个链接里的 cache_time 可能不同，且您想保留第一个有效的 cache_time
    # 可以用下面的逻辑动态设置
    first_valid_cache_time = next((item.get("cache_time") for item in clean_data_buffer if "cache_time" in item), 7200)
    final_config["cache_time"] = first_valid_cache_time


    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(final_config, f, indent=4, ensure_ascii=False)
        print(f"成功！所有内容已按白名单过滤并写入到文件: {OUTPUT_FILENAME}")
    except IOError as e:
        print(f"错误: 写入文件 {OUTPUT_FILENAME} 失败: {e}")

    print("--- 更新任务结束 ---")

if __name__ == "__main__":
    main()
