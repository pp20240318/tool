# 图片压缩工具 - TinyPNG API

基于 TinyPNG API 的批量图片压缩工具，支持递归处理多层文件夹、断点续传和多 API Key 自动切换。

## 功能特性

✅ **递归扫描** - 自动处理多层嵌套文件夹  
✅ **保持结构** - 输出文件夹保持原目录结构  
✅ **断点续传** - 基于文件 MD5 哈希判断是否已压缩，中断后继续执行  
✅ **多 Key 管理** - 自动切换 API key，每个 key 500 次后换下一个  
✅ **详细日志** - 记录压缩时间、大小、压缩率等信息  
✅ **错误处理** - 完善的异常处理和错误提示  

## 安装依赖

```bash
pip install -r requirements.txt
```

或直接安装：

```bash
pip install tinify
```

## 配置说明

### 1. 获取 API Key

1. 访问 https://tinypng.com/developers
2. 注册账号并获取免费的 API key
3. 每个 key 每月可免费压缩 500 张图片

### 2. 配置文件 (config.json)

```json
{
    "api_keys": [
        "your-api-key-1",
        "your-api-key-2",
        "your-api-key-3"
    ],
    "source_folder": "./images",
    "output_folder": "./compressed_images",
    "max_compressions_per_key": 500,
    "supported_formats": [".jpg", ".jpeg", ".png", ".webp"]
}
```

**配置项说明：**

- `api_keys`: TinyPNG API keys 列表，程序会自动轮换使用
- `source_folder`: 需要压缩的图片源文件夹
- `output_folder`: 压缩后图片的输出文件夹
- `max_compressions_per_key`: 每个 API key 的最大使用次数（默认 500）
- `supported_formats`: 支持的图片格式列表

## 使用方法

### 1. 配置 API Key

编辑 `config.json` 文件，将 `api_keys` 中的值替换为你的真实 API key：

```json
"api_keys": [
    "abcd1234efgh5678ijkl",
    "wxyz9876stuv5432pqrs"
]
```

### 2. 设置源文件夹

将 `source_folder` 设置为你要压缩的图片文件夹路径：

```json
"source_folder": "D:/my_photos"
```

### 3. 运行程序

```bash
python image_compressor.py
```

### 4. 查看结果

- 压缩后的图片保存在 `output_folder` 指定的文件夹中
- 目录结构与源文件夹保持一致
- 压缩日志保存在 `compression_log.json` 中

## 断点续传

程序会自动记录已压缩的文件：

- 压缩记录保存在 `compression_log.json` 文件中
- 基于文件的 MD5 哈希值判断是否已压缩
- 中断后再次运行会自动跳过已压缩的文件
- 即使文件被移动到其他位置，只要内容相同就会被识别

## 日志文件说明

`compression_log.json` 包含以下信息：

- **compressed_files**: 已压缩文件的详细信息
  - 源文件路径
  - 输出文件路径
  - 原始大小
  - 压缩后大小
  - 压缩率
  - 压缩时间
  - 使用的 API key 索引

- **key_usage**: 每个 API key 的使用次数统计

- **current_key_index**: 当前使用的 key 索引

## 示例输出

```
============================================================
图片压缩工具 - TinyPNG API
============================================================
正在使用 API key [1/3]
当前 key 已使用次数: 0
开始扫描文件夹: ./images
找到 15 个图片文件

[1/15] 处理: ./images/photo1.jpg
✓ 压缩成功: photo1.jpg
  原始大小: 2048.50 KB
  压缩后: 890.32 KB
  压缩率: 56.54%

...

============================================================
压缩完成！
总文件数: 15
成功压缩: 15
跳过（已压缩）: 0
失败: 0
============================================================

API Key 使用统计:
  Key 1: 15 / 500
  Key 2: 0 / 500
  Key 3: 0 / 500
```

## 注意事项

1. 确保有稳定的网络连接
2. API key 需要有效且未超出使用限制
3. 程序会保持原始文件不变，只创建压缩后的副本
4. 建议在压缩前备份重要图片
5. 如需重新压缩所有图片，删除 `compression_log.json` 文件即可

## 故障排除

### API key 错误
- 检查 API key 是否正确
- 确认 API key 未过期或超出限制

### 网络连接错误
- 检查网络连接
- 如有代理，确保代理设置正确

### 文件路径错误
- 确保源文件夹路径存在
- 使用绝对路径或正确的相对路径

## 许可证

MIT License

