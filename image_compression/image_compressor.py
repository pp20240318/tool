import os
import json
import hashlib
import tinify
from pathlib import Path
from datetime import datetime
from PIL import Image
import tempfile

class ImageCompressor:
    def __init__(self, config_file='config.json'):
        """初始化图片压缩器"""
        self.config_file = config_file
        self.log_file = 'compression_log.json'
        self.load_config()
        self.load_log()
        self.current_key_index = self.log_data.get('current_key_index', 0)
        self.set_api_key()
        
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            # 创建默认配置
            default_config = {
                "api_keys": [
                    "your-api-key-1",
                    "your-api-key-2",
                    "your-api-key-3"
                ],
                "source_folder": "./images",
                "output_folder": "./compressed_images",
                "max_compressions_per_key": 500,
                "max_width": 1920,
                "enable_resize": True,
                "supported_formats": [".jpg", ".jpeg", ".png", ".webp"]
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"已创建默认配置文件：{self.config_file}")
            print("请在配置文件中填写您的 API keys！")
            self.config = default_config
        else:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
    
    def load_log(self):
        """加载压缩日志"""
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r', encoding='utf-8') as f:
                self.log_data = json.load(f)
        else:
            self.log_data = {
                'compressed_files': {},  # 文件哈希 -> 压缩信息
                'key_usage': {},  # API key 使用计数
                'key_details': {},  # API key 详细信息（首次使用、最后使用时间等）
                'current_key_index': 0,
                'total_compressions': 0,  # 总压缩次数
                'last_run_time': None  # 最后运行时间
            }
        
        # 确保旧版本日志也有新字段
        if 'key_details' not in self.log_data:
            self.log_data['key_details'] = {}
        if 'total_compressions' not in self.log_data:
            self.log_data['total_compressions'] = 0
        if 'last_run_time' not in self.log_data:
            self.log_data['last_run_time'] = None
        
        # 修复 API keys 与配置不一致的问题
        self.fix_api_keys_mismatch()
    
    def fix_api_keys_mismatch(self):
        """修复日志中的 API keys 与配置文件不一致的问题"""
        config_keys = set(self.config['api_keys'])
        log_keys_usage = set(self.log_data.get('key_usage', {}).keys())
        log_keys_details = set(self.log_data.get('key_details', {}).keys())
        
        # 如果配置文件中的 keys 与日志中的 keys 完全不同，说明更换了 keys
        if not config_keys.intersection(log_keys_usage):
            print("检测到 API keys 已更换，清理旧 key 记录...")
            # 保留总压缩次数，但清空 key 相关的记录
            self.log_data['key_usage'] = {}
            self.log_data['key_details'] = {}
            self.log_data['current_key_index'] = 0
            self.save_log()
            print("已清理旧 API key 记录")
        else:
            # 移除不在配置中的旧 key 记录
            keys_to_remove = log_keys_usage - config_keys
            if keys_to_remove:
                print(f"移除已不在配置中的旧 API keys: {len(keys_to_remove)} 个")
                for key in keys_to_remove:
                    self.log_data['key_usage'].pop(key, None)
                    self.log_data['key_details'].pop(key, None)
                self.save_log()
        
        # 修复 current_key_index 超出范围的问题
        current_index = self.log_data.get('current_key_index', 0)
        if current_index >= len(self.config['api_keys']):
            print(f"修复 current_key_index: {current_index} -> 0 (已超出范围)")
            self.log_data['current_key_index'] = 0
            self.save_log()
        
        # 如果当前索引对应的 key 已用完，尝试找到下一个可用的 key
        current_index = self.log_data.get('current_key_index', 0)
        if current_index < len(self.config['api_keys']):
            current_key = self.config['api_keys'][current_index]
            usage = self.log_data.get('key_usage', {}).get(current_key, 0)
            max_usage = self.config.get('max_compressions_per_key', 500)
            if usage >= max_usage:
                # 当前 key 已用完，尝试找下一个可用的 key
                for i in range(len(self.config['api_keys'])):
                    test_key = self.config['api_keys'][i]
                    test_usage = self.log_data.get('key_usage', {}).get(test_key, 0)
                    if test_usage < max_usage:
                        print(f"切换到可用的 API key [{i + 1}/{len(self.config['api_keys'])}]")
                        self.log_data['current_key_index'] = i
                        self.save_log()
                        break
    
    def save_log(self):
        """保存压缩日志"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, indent=4, ensure_ascii=False)
    
    def get_file_hash(self, file_path):
        """计算文件的MD5哈希值"""
        md5_hash = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def set_api_key(self):
        """设置当前使用的 API key"""
        if self.current_key_index >= len(self.config['api_keys']):
            raise Exception("所有 API keys 已用完！")
        
        current_key = self.config['api_keys'][self.current_key_index]
        tinify.key = current_key
        
        # 初始化当前 key 的使用计数
        if current_key not in self.log_data['key_usage']:
            self.log_data['key_usage'][current_key] = 0
        
        # 初始化当前 key 的详细信息
        if current_key not in self.log_data['key_details']:
            self.log_data['key_details'][current_key] = {
                'first_used': datetime.now().isoformat(),
                'last_used': None,
                'total_usage': 0
            }
        
        usage = self.log_data['key_usage'][current_key]
        max_usage = self.config.get('max_compressions_per_key', 500)
        remaining = max_usage - usage
        
        print(f"正在使用 API key [{self.current_key_index + 1}/{len(self.config['api_keys'])}]")
        print(f"当前 key 已使用: {usage} 次，剩余: {remaining} 次")
    
    def switch_api_key(self):
        """切换到下一个 API key"""
        self.current_key_index += 1
        self.log_data['current_key_index'] = self.current_key_index
        
        if self.current_key_index >= len(self.config['api_keys']):
            raise Exception("所有 API keys 已达到使用上限！")
        
        self.set_api_key()
        print(f"已切换到下一个 API key")
    
    def check_and_switch_key(self):
        """检查当前 key 使用次数，必要时切换"""
        current_key = self.config['api_keys'][self.current_key_index]
        usage = self.log_data['key_usage'][current_key]
        max_usage = self.config.get('max_compressions_per_key', 500)
        
        if usage >= max_usage:
            print(f"当前 API key 已达到 {max_usage} 次使用上限")
            self.switch_api_key()
    
    def resize_image_if_needed(self, image_path):
        """如果需要，对图片进行等比缩放
        
        返回:
            str: 缩放后的临时文件路径，如果不需要缩放则返回原路径
            bool: 是否进行了缩放
        """
        # 检查是否启用缩放功能
        if not self.config.get('enable_resize', False):
            return image_path, False
        
        max_width = self.config.get('max_width', 1920)
        
        try:
            # 打开图片
            img = Image.open(image_path)
            original_width, original_height = img.size
            
            # 如果宽度不超过最大宽度，不需要缩放
            if original_width <= max_width:
                return image_path, False
            
            # 计算新的尺寸（等比缩放）
            ratio = max_width / original_width
            new_width = max_width
            new_height = int(original_height * ratio)
            
            print(f"  本地缩放: {original_width}x{original_height} -> {new_width}x{new_height}")
            
            # 缩放图片
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # 创建临时文件保存缩放后的图片
            file_ext = os.path.splitext(image_path)[1].lower()
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
            temp_path = temp_file.name
            temp_file.close()
            
            # 保存缩放后的图片，保持原格式和质量
            if file_ext in ['.jpg', '.jpeg']:
                resized_img.save(temp_path, 'JPEG', quality=95, optimize=True)
            elif file_ext == '.png':
                resized_img.save(temp_path, 'PNG', optimize=True)
            elif file_ext == '.webp':
                resized_img.save(temp_path, 'WEBP', quality=95)
            else:
                resized_img.save(temp_path)
            
            img.close()
            resized_img.close()
            
            return temp_path, True
            
        except Exception as e:
            print(f"  警告: 图片缩放失败，将使用原图: {e}")
            return image_path, False
    
    def is_compressed(self, file_path):
        """检查文件是否已压缩"""
        file_hash = self.get_file_hash(file_path)
        return file_hash in self.log_data['compressed_files']
    
    def compress_image(self, source_path, output_path):
        """压缩单个图片"""
        temp_file_to_delete = None
        try:
            # 检查并切换 key
            self.check_and_switch_key()
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # 先进行本地缩放（如果需要）
            process_path, was_resized = self.resize_image_if_needed(source_path)
            if was_resized:
                temp_file_to_delete = process_path
            
            # 压缩图片（使用缩放后的文件或原文件）
            source = tinify.from_file(process_path)
            source.to_file(output_path)
            
            # 更新使用计数
            current_key = self.config['api_keys'][self.current_key_index]
            self.log_data['key_usage'][current_key] += 1
            self.log_data['total_compressions'] += 1
            
            # 更新 key 详细信息
            current_time = datetime.now().isoformat()
            if current_key not in self.log_data['key_details']:
                self.log_data['key_details'][current_key] = {
                    'first_used': current_time,
                    'last_used': current_time,
                    'total_usage': 1
                }
            else:
                self.log_data['key_details'][current_key]['last_used'] = current_time
                self.log_data['key_details'][current_key]['total_usage'] = self.log_data['key_usage'][current_key]
            
            # 记录压缩信息
            file_hash = self.get_file_hash(source_path)
            original_size = os.path.getsize(source_path)
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            self.log_data['compressed_files'][file_hash] = {
                'source_path': source_path,
                'output_path': output_path,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': f"{compression_ratio:.2f}%",
                'compressed_at': current_time,
                'api_key_index': self.current_key_index,
                'api_key_used': current_key[:20] + "..."  # 只保存 key 的前20个字符用于识别
            }
            
            # 保存日志（每次压缩后立即保存，确保断点续传数据准确）
            self.save_log()
            
            # 计算当前 key 剩余次数
            max_usage = self.config.get('max_compressions_per_key', 500)
            remaining = max_usage - self.log_data['key_usage'][current_key]
            
            print(f"[OK] 压缩成功: {os.path.basename(source_path)}")
            print(f"  原始大小: {original_size / 1024:.2f} KB")
            print(f"  压缩后: {compressed_size / 1024:.2f} KB")
            print(f"  压缩率: {compression_ratio:.2f}%")
            print(f"  当前 Key 剩余次数: {remaining}")
            
            # 清理临时文件
            if temp_file_to_delete and os.path.exists(temp_file_to_delete):
                try:
                    os.unlink(temp_file_to_delete)
                except:
                    pass
            
            return True
            
        except tinify.AccountError as e:
            print(f"[错误] API key 错误: {e}")
            if temp_file_to_delete and os.path.exists(temp_file_to_delete):
                try:
                    os.unlink(temp_file_to_delete)
                except:
                    pass
            return False
        except tinify.ClientError as e:
            print(f"[错误] 请求错误: {e}")
            if temp_file_to_delete and os.path.exists(temp_file_to_delete):
                try:
                    os.unlink(temp_file_to_delete)
                except:
                    pass
            return False
        except tinify.ServerError as e:
            print(f"[错误] 服务器错误: {e}")
            if temp_file_to_delete and os.path.exists(temp_file_to_delete):
                try:
                    os.unlink(temp_file_to_delete)
                except:
                    pass
            return False
        except tinify.ConnectionError as e:
            print(f"[错误] 连接错误: {e}")
            if temp_file_to_delete and os.path.exists(temp_file_to_delete):
                try:
                    os.unlink(temp_file_to_delete)
                except:
                    pass
            return False
        except Exception as e:
            print(f"[失败] 压缩失败: {source_path}")
            print(f"  错误: {e}")
            if temp_file_to_delete and os.path.exists(temp_file_to_delete):
                try:
                    os.unlink(temp_file_to_delete)
                except:
                    pass
            return False
    
    def get_all_images(self, folder):
        """递归获取文件夹中的所有图片"""
        images = []
        supported_formats = self.config.get('supported_formats', ['.jpg', '.jpeg', '.png', '.webp'])
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                ext = os.path.splitext(file)[1].lower()
                
                if ext in supported_formats:
                    images.append(file_path)
        
        return images
    
    def get_output_path(self, source_path):
        """根据源文件路径生成输出路径，保持目录结构"""
        source_folder = os.path.abspath(self.config['source_folder'])
        output_folder = os.path.abspath(self.config['output_folder'])
        source_path = os.path.abspath(source_path)
        
        # 计算相对路径
        rel_path = os.path.relpath(source_path, source_folder)
        
        # 生成输出路径
        output_path = os.path.join(output_folder, rel_path)
        
        return output_path
    
    def display_api_keys_status(self):
        """显示所有 API keys 的使用状态"""
        print("\n" + "="*60)
        print("API Keys 使用状态详情")
        print("="*60)
        
        max_usage = self.config.get('max_compressions_per_key', 500)
        
        for i, key in enumerate(self.config['api_keys'], 1):
            usage = self.log_data['key_usage'].get(key, 0)
            remaining = max_usage - usage
            percentage = (usage / max_usage) * 100 if max_usage > 0 else 0
            
            # 显示状态条（使用ASCII字符避免编码问题）
            bar_length = 30
            filled = int(bar_length * usage / max_usage) if max_usage > 0 else 0
            bar = '#' * filled + '-' * (bar_length - filled)
            
            # 当前使用的 key 标记
            current_marker = " <- 当前使用" if i - 1 == self.current_key_index else ""
            
            print(f"\nKey {i}{current_marker}")
            print(f"  标识: {key[:10]}...{key[-4:]}")
            print(f"  使用: {usage} / {max_usage} ({percentage:.1f}%)")
            print(f"  进度: [{bar}]")
            print(f"  剩余: {remaining} 次")
            
            # 如果有详细信息，显示首次和最后使用时间
            if key in self.log_data.get('key_details', {}):
                details = self.log_data['key_details'][key]
                if details.get('first_used'):
                    first_used = details['first_used'][:19].replace('T', ' ')
                    print(f"  首次使用: {first_used}")
                if details.get('last_used'):
                    last_used = details['last_used'][:19].replace('T', ' ')
                    print(f"  最后使用: {last_used}")
        
        print("\n" + "="*60)
        print(f"历史总压缩次数: {self.log_data.get('total_compressions', 0)}")
        if self.log_data.get('last_run_time'):
            last_run = self.log_data['last_run_time'][:19].replace('T', ' ')
            print(f"上次运行时间: {last_run}")
        print("="*60 + "\n")
    
    def run(self):
        """执行批量压缩"""
        # 显示当前 API keys 状态
        self.display_api_keys_status()
        
        source_folder = self.config['source_folder']
        
        if not os.path.exists(source_folder):
            print(f"错误: 源文件夹不存在: {source_folder}")
            return
        
        print(f"开始扫描文件夹: {source_folder}")
        images = self.get_all_images(source_folder)
        
        if not images:
            print("未找到任何图片文件！")
            return
        
        print(f"找到 {len(images)} 个图片文件\n")
        
        # 统计信息
        total = len(images)
        compressed = 0
        skipped = 0
        failed = 0
        
        for i, image_path in enumerate(images, 1):
            print(f"\n[{i}/{total}] 处理: {image_path}")
            
            # 检查是否已压缩
            if self.is_compressed(image_path):
                print(f"[跳过] 跳过（已压缩）: {os.path.basename(image_path)}")
                skipped += 1
                continue
            
            # 获取输出路径
            output_path = self.get_output_path(image_path)
            
            # 压缩图片
            if self.compress_image(image_path, output_path):
                compressed += 1
            else:
                failed += 1
        
        # 更新最后运行时间
        self.log_data['last_run_time'] = datetime.now().isoformat()
        self.save_log()
        
        # 输出统计信息
        print("\n" + "="*60)
        print("压缩完成！")
        print("="*60)
        print(f"总文件数: {total}")
        print(f"成功压缩: {compressed}")
        print(f"跳过（已压缩）: {skipped}")
        print(f"失败: {failed}")
        print("="*60)
        
        # 显示详细的 API key 使用统计
        self.display_api_keys_status()

def main():
    """主函数"""
    print("="*60)
    print("图片压缩工具 - TinyPNG API")
    print("="*60)
    
    compressor = ImageCompressor()
    compressor.run()

if __name__ == '__main__':
    main()

