import requests
import base58
import json

def fetch_decode_and_merge(urls):
    """
    从给定的 URL 列表中获取内容，进行 Base58 解码，然后合并 JSON 数据。

    :param urls: 包含要处理的 URL 的列表。
    :return: 合并后的 Python 字典。
    """
    merged_config = {}
    
    print("开始处理链接...")
    
    for url in urls:
        try:
            print(f"正在读取链接: {url}")
            # 发起网络请求获取原始数据
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 如果请求失败 (状态码不是 2xx)，则抛出异常

            # 获取 Base58 编码的文本内容，并去除首尾空白
            encoded_content = response.text.strip()
            if not encoded_content:
                print(f"警告: 链接 {url} 内容为空，已跳过。")
                continue

            print("内容读取成功，开始 Base58 解码...")
            # 解码 Base58 内容，得到字节串
            decoded_bytes = base58.b58decode(encoded_content)
            
            # 将解码后的字节串转换为 UTF-8 格式的字符串
            decoded_json_string = decoded_bytes.decode('utf-8')
            
            print("解码成功，正在解析 JSON...")
            # 将 JSON 字符串解析为 Python 字典
            config_part = json.loads(decoded_json_string)
            
            # 合并字典。如果存在相同的键，后一个链接中的值会覆盖前一个
            merged_config.update(config_part)
            print("合并部分配置成功。")

        except requests.exceptions.RequestException as e:
            print(f"错误: 读取链接 {url} 失败: {e}")
        except ValueError as e:
            # base58.b58decode 或 json.loads 可能会抛出 ValueError
            print(f"错误: 解码或解析链接 {url} 的内容时失败: {e}")
        except Exception as e:
            print(f"处理链接 {url} 时发生未知错误: {e}")
            
    return merged_config

def save_config_to_file(config_data, filename="config.json"):
    """
    将配置数据以 JSON 格式保存到文件。

    :param config_data: 要保存的 Python 字典。
    :param filename: 输出文件名。
    """
    if not config_data:
        print("没有可供保存的配置数据，程序退出。")
        return
        
    try:
        print(f"正在将合并后的配置写入文件: {filename}")
        with open(filename, 'w', encoding='utf-8') as f:
            # 将字典写入文件，格式化以方便阅读
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        print(f"成功！配置文件已保存为 {filename}")
    except IOError as e:
        print(f"错误: 写入文件 {filename} 失败: {e}")


if __name__ == "__main__":
    # 目标链接地址列表
    target_urls = [
        "https://raw.githubusercontent.com/cmliu/cmliu/refs/heads/main/tvapi_config_json",
        "https://gist.githubusercontent.com/senshinya/5a5cb900dfa888fd61d767530f00fc48/raw/gistfile1.txt"
    ]
    
    # 执行主流程
    final_config = fetch_decode_and_merge(target_urls)
    save_config_to_file(final_config)
