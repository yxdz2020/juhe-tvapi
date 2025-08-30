import json
import os

# --- 配置区 ---
INPUT_CONFIG_FILE = 'config.json'
NORMAL_OUTPUT_FILE = 'config.json'  # 正常源会覆盖原文件
ADULT_OUTPUT_FILE = 'config18.json' # 成人源保存到新文件

# 定义用于识别成人内容的关键词列表 (不区分大小写)
# 您可以根据需要随时增删这个列表中的关键词
ADULT_KEYWORDS = [
    'AV', '麻豆', '91', '杏吧', '森林', '淫水', '玉兔', '番号',
    '精品', '美少女', '老色逼', '色南国', '辣椒', '香奶儿', '鲨鱼',
    '黄色', '成人', '色情', '情色', '小猫咪', '快播', '细胞采集',
    'JKUN', 'souav', '小鸡'
]

def classify_and_separate_sources():
    """
    读取配置文件，根据关键词分类API源，并分别写入两个文件。
    """
    print("--- 步骤 3: 开始分类视频源 ---")
    
    # 检查输入文件是否存在
    if not os.path.exists(INPUT_CONFIG_FILE):
        print(f"错误: 输入文件 '{INPUT_CONFIG_FILE}' 未找到。请确保前序步骤已成功生成该文件。")
        return

    # 读取原始配置文件
    try:
        with open(INPUT_CONFIG_FILE, 'r', encoding='utf-8') as f:
            original_config = json.load(f)
    except json.JSONDecodeError:
        print(f"错误: 无法解析 '{INPUT_CONFIG_FILE}'。文件可能已损坏或格式不正确。")
        return
        
    # 创建两个新的配置模板，继承原始文件的元数据（如 cache_time）
    normal_config = original_config.copy()
    adult_config = original_config.copy()
    
    # 初始化空的 api_site 字典
    normal_sources = {}
    adult_sources = {}
    
    all_sources = original_config.get('api_site', {})
    
    print(f"开始从 {len(all_sources)} 个源中进行分类...")

    # 遍历所有源进行分类
    for key, details in all_sources.items():
        is_adult = False
        source_name = details.get('name', '').lower() # 获取源名称并转为小写

        # 检查名称是否包含任何成人关键词
        for keyword in ADULT_KEYWORDS:
            if keyword.lower() in source_name:
                is_adult = True
                break # 找到一个关键词就足够了，跳出内层循环
        
        if is_adult:
            adult_sources[key] = details
        else:
            normal_sources[key] = details

    # 将分类好的源放回配置模板
    normal_config['api_site'] = normal_sources
    adult_config['api_site'] = adult_sources

    # 写入正常源配置文件
    try:
        with open(NORMAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(normal_config, f, indent=4, ensure_ascii=False)
        print(f"处理完成: {len(normal_sources)} 个正常源已写入 '{NORMAL_OUTPUT_FILE}'")
    except IOError as e:
        print(f"错误: 写入 '{NORMAL_OUTPUT_FILE}' 失败: {e}")

    # 写入成人源配置文件
    try:
        with open(ADULT_OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(adult_config, f, indent=4, ensure_ascii=False)
        print(f"处理完成: {len(adult_sources)} 个成人源已写入 '{ADULT_OUTPUT_FILE}'")
    except IOError as e:
        print(f"错误: 写入 '{ADULT_OUTPUT_FILE}' 失败: {e}")

if __name__ == "__main__":
    classify_and_separate_sources()
