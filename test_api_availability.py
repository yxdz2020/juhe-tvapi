import json
import requests
import concurrent.futures
from typing import Dict, Tuple, List
import time
import os
import argparse

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def load_apis_from_config(config_path: str) -> Dict[str, dict]:
    """
    从配置文件中加载API列表
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    return config

def validate_api_response(data: dict) -> bool:
    """
    验证API响应数据是否符合预期格式
    """
    if not isinstance(data, dict):
        return False
    
    if 'code' in data and data['code'] != 1 and data['code'] != 200:
        return False
    
    if 'list' in data:
        if not isinstance(data['list'], list):
            return False
        if len(data['list']) > 0:
            first_item = data['list'][0]
            required_fields = ['vod_id', 'vod_name']
            for field in required_fields:
                if field not in first_item:
                    alt_fields = {
                        'vod_id': ['id', 'video_id'],
                        'vod_name': ['name', 'title']
                    }
                    found = False
                    for alt_field in alt_fields.get(field, []):
                        if alt_field in first_item:
                            found = True
                            break
                    if not found:
                        return False
    elif 'data' in data:
        if not isinstance(data['data'], (list, dict)):
            return False
    else:
        if len(data) == 0:
            return False
    
    return True

def remove_duplicate_apis(config: dict) -> Tuple[dict, List[Tuple[str, str]]]:
    """
    优化版去重核心：标准化对比URL，忽略空格、末尾斜杠及HTTP/HTTPS差异
    """
    api_sites = config.get('api_site', {})
    seen_urls = {}
    removed_apis = []
    
    new_api_sites = {}
    for name, value in api_sites.items():
        if 'api' in value and isinstance(value['api'], str):
            original_url = value['api']
            
            # --- 优化点：清洗 URL 用于严格去重对比 ---
            # 1. 去除首尾多余空格
            # 2. 去除末尾的斜杠 '/'
            clean_url = original_url.strip().rstrip('/')
            
            # 3. 剥离协议头，抹平 http 和 https 的差异
            compare_url = clean_url.replace("https://", "").replace("http://", "")
            
            if compare_url in seen_urls:
                # 发现重复的API
                removed_apis.append((name, original_url))
                print(f"✂️ 已清理重复 API: [{name}] -> {original_url}")
                print(f"   (由于内容等同于首次出现的: [{seen_urls[compare_url]}])")
            else:
                # 首次出现的API，记录其清洗后的用于后续比对的特征码
                seen_urls[compare_url] = name
                new_api_sites[name] = value
        else:
            # 没有 api 字段的配置也默认保留
            new_api_sites[name] = value
    
    # 更新配置
    config['api_site'] = new_api_sites
    return config, removed_apis

def test_api(api_name: str, api_url: str, max_retries: int = 2) -> Tuple[str, str, bool, int, str]:
    """
    测试单个API的有效性
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    test_urls = [
        f"{api_url}?ac=detail&limit=1",
        f"{api_url}?ac=list&limit=1",
        f"{api_url}?limit=1",
        api_url
    ]
    
    for attempt in range(max_retries):
        for test_url in test_urls:
            try:
                response = requests.get(
                    test_url, 
                    headers=headers, 
                    timeout=10,
                    verify=False
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if validate_api_response(data):
                            return api_name, test_url, True, response.status_code, "有效"
                        else:
                            continue
                    except json.JSONDecodeError:
                        continue
                
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                continue
    
    return api_name, api_url, False, response.status_code if 'response' in locals() else -1, str(e) if 'e' in locals() else "请求失败"

def remove_unavailable_apis(config: dict, unavailable_apis: List[str]) -> dict:
    """
    从配置中移除不可用的API
    """
    new_config = json.loads(json.dumps(config))
    for api_name in unavailable_apis:
        if api_name in new_config.get('api_site', {}):
            del new_config['api_site'][api_name]
            print(f"🗑️ 已移除测速失效的API: {api_name}")
    return new_config

def main():
    parser = argparse.ArgumentParser(description="测试并清理配置文件中的API。")
    parser.add_argument(
        '-y', '--yes',
        action='store_true',
        help="自动对所有提问回答'是'，用于非交互式环境（如GitHub Actions）。"
    )
    args = parser.parse_args()

    config_path = 'config.json'
    
    if not os.path.exists(config_path):
        print(f"错误: 找不到配置文件 {config_path}")
        return
    
    config = load_apis_from_config(config_path)
    
    print("--- 开始进行 API 深度去重处理 ---")
    deduplicated_config, removed_apis = remove_duplicate_apis(config)
    if removed_apis:
        print(f"\n✅ 深度去重完成！共精准移除了 {len(removed_apis)} 个冗余 API 节点。")
        
        choice = 'y' if args.yes else input(f"\n是否要将去重后的配置保存到 {config_path} ? (y/N): ")
        if choice.lower() in ['y', 'yes']:
            backup_path = f"{config_path}.backup.{int(time.time())}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"原配置已备份至: {backup_path}")
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(deduplicated_config, f, ensure_ascii=False, indent=4) # 优化排版为缩进4格
            print(f"已将去重后的配置保存到 {config_path}")
            config = deduplicated_config
        else:
            print("未执行去重配置保存操作，将使用原始配置进行测试")
    else:
        print("✅ 未发现重复的 API 链接，源列表已是最佳状态。")
    
    api_sites = config.get('api_site', {})
    apis = {key: value['api'] for key, value in api_sites.items() if 'api' in value}
    
    print(f"\n加载了 {len(apis)} 个独立 API 进行连通性测试")
    print("=" * 80)
    
    results = []
    available_count = 0
    unavailable_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_api = {executor.submit(test_api, name, url): (name, url) for name, url in apis.items()}
        for future in concurrent.futures.as_completed(future_to_api):
            name, url = future_to_api[future]
            try:
                result = future.result()
                results.append(result)
                if result[2]:
                    print(f"✓ {name}: {result[3]} (状态码: {result[3]})")
                    available_count += 1
                else:
                    if result[3] == -1:
                        print(f"✗ {name}: {result[4]} (错误: {result[4]})")
                    else:
                        print(f"✗ {name}: {result[3]} (状态码: {result[3]}, 错误: {result[4]})")
                    unavailable_count += 1
            except Exception as e:
                print(f"测试 {name} 时发生错误: {e}")
                results.append((name, url, False, -1, str(e)))
                unavailable_count += 1
                
    print("\n" + "=" * 80)
    print(f"测试完成: {available_count}/{len(results)} 个API有效")
    
    available_apis = [r for r in results if r[2]]
    unavailable_apis = [r for r in results if not r[2]]
    
    if unavailable_count > 0:
        choice = 'y' if args.yes else input(f"\n是否要从 {config_path} 中移除这 {unavailable_count} 个无效的API? (y/N): ")
        if choice.lower() in ['y', 'yes']:
            unavailable_api_names = [r[0] for r in unavailable_apis]
            updated_config = remove_unavailable_apis(config, unavailable_api_names)
            
            backup_path = f"{config_path}.backup.{int(time.time())}"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(updated_config, f, ensure_ascii=False, indent=4) # 优化排版为缩进4格
            
            print(f"🎉 成功！已从配置文件中永久移除 {unavailable_count} 个无效的 API。")
        else:
            print("未执行移除操作")
    else:
        print("\n🎉 所有测试的 API 均有效，无需进一步清理。")

if __name__ == "__main__":
    main()
