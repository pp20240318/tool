import json
import os

def view_stats():
    """快速查看 API key 使用统计"""
    log_file = 'compression_log.json'
    config_file = 'config.json'
    
    if not os.path.exists(log_file):
        print("还没有压缩记录！")
        return
    
    # 读取配置
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # 读取日志
    with open(log_file, 'r', encoding='utf-8') as f:
        log_data = json.load(f)
    
    max_usage = config.get('max_compressions_per_key', 500)
    
    print("\n" + "="*60)
    print("API Keys 使用统计")
    print("="*60 + "\n")
    
    for i, key in enumerate(config['api_keys'], 1):
        usage = log_data.get('key_usage', {}).get(key, 0)
        remaining = max_usage - usage
        percentage = (usage / max_usage) * 100 if max_usage > 0 else 0
        
        # 进度条
        bar_length = 30
        filled = int(bar_length * usage / max_usage) if max_usage > 0 else 0
        bar = '#' * filled + '-' * (bar_length - filled)
        
        # 当前使用标记
        current_index = log_data.get('current_key_index', 0)
        current_marker = " <- 当前使用" if i - 1 == current_index else ""
        
        print(f"Key {i}{current_marker}")
        print(f"  标识: {key[:10]}...{key[-4:]}")
        print(f"  已使用: {usage} 次")
        print(f"  剩余: {remaining} 次")
        print(f"  进度: [{bar}] {percentage:.1f}%")
        
        # 详细信息
        if key in log_data.get('key_details', {}):
            details = log_data['key_details'][key]
            if details.get('first_used'):
                first_used = details['first_used'][:19].replace('T', ' ')
                print(f"  首次使用: {first_used}")
            if details.get('last_used'):
                last_used = details['last_used'][:19].replace('T', ' ')
                print(f"  最后使用: {last_used}")
        
        print()
    
    print("="*60)
    print(f"历史总压缩次数: {log_data.get('total_compressions', 0)}")
    
    if log_data.get('last_run_time'):
        last_run = log_data['last_run_time'][:19].replace('T', ' ')
        print(f"上次运行时间: {last_run}")
    
    # 显示已压缩文件数
    compressed_count = len(log_data.get('compressed_files', {}))
    print(f"已压缩文件数: {compressed_count}")
    print("="*60)

if __name__ == '__main__':
    view_stats()

