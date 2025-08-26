# AWS Bedrock ChatApp - Enhanced Version

一个现代化的 AWS Bedrock AI 聊天应用程序，具有增强的功能和用户界面。

## 🚀 主要特性

### 核心功能
- **多模型支持**: Claude 3.5/4, Amazon Nova 系列, DeepSeek R1
- **多模态交互**: 支持文本、图片、PDF 文档
- **流式响应**: 实时显示 AI 回复
- **上下文管理**: 可选择性记忆对话历史

### 用户界面
- **现代化 UI**: 清晰直观的界面设计
- **可调整布局**: 可调整窗口分割比例
- **搜索功能**: 在聊天历史中搜索内容
- **导出功能**: 支持导出聊天记录为文本或 JSON

### 高级功能
- **参数配置**: 可视化配置模型参数
- **系统提示词管理**: 创建、保存、管理系统提示词
- **文件处理**: 智能处理图片、PDF、文本文件
- **错误处理**: 完善的错误处理和重试机制

## 📦 安装

### 环境要求
- Python 3.8+
- AWS 账户和凭证
- 支持的操作系统: Windows, macOS, Linux

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/yourusername/aws-bedrock-chatapp.git
cd aws-bedrock-chatapp
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置 AWS 凭证**
```bash
# 方法1: 使用 AWS CLI
aws configure

# 方法2: 手动创建 ~/.aws/credentials 文件
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

5. **运行应用**
```bash
python main.py
```

## 🛠️ 配置

### 配置文件
应用使用 `config/settings.yaml` 进行配置，包括：
- 应用设置（窗口大小、字体等）
- AWS 区域和模型列表
- 模型参数预设
- 代理设置

### 系统提示词
- 支持多个系统提示词预设
- 可通过界面创建、编辑、删除
- 自动保存到 `bedrock_chatapp_prompt.json`

## 🎯 使用指南

### 基本操作
1. **选择配置**: 在顶部工具栏选择 AWS Profile、区域、模型等
2. **输入消息**: 在底部输入框输入文本
3. **发送消息**: 点击发送按钮或按 Ctrl+Enter
4. **上传文件**: 点击"Upload File"按钮上传图片或文档

### 快捷键
- `Ctrl+Enter`: 发送消息
- `Ctrl+L`: 清除上下文
- `Ctrl+K`: 清除屏幕
- `Ctrl+O`: 上传文件

### 高级功能
- **参数调整**: 在右侧面板调整模型参数
- **搜索历史**: 使用聊天历史面板的搜索功能
- **导出对话**: 导出聊天记录为文件
- **多模态**: 上传图片进行视觉问答

## 🏗️ 项目结构

```
aws-bedrock-chatapp/
├── config/                 # 配置管理
│   ├── config_manager.py   # 配置管理器
│   └── settings.yaml       # 应用配置
├── models/                 # AI 模型相关
│   └── bedrock_client.py   # Bedrock 客户端
├── utils/                  # 工具函数
│   └── file_handler.py     # 文件处理
├── ui/                     # 用户界面
│   ├── main_window.py      # 主窗口
│   └── components/         # UI 组件
│       └── chat_history.py # 聊天历史组件
├── tests/                  # 单元测试
├── main.py                 # 应用入口
├── requirements.txt        # 依赖列表
└── README.md              # 说明文档
```

## 🧪 测试

运行单元测试：
```bash
# 运行所有测试
python -m pytest

# 运行特定测试
python -m pytest tests/test_config_manager.py

# 运行测试并生成覆盖率报告
python -m pytest --cov=config --cov=models --cov=utils --cov=ui
```

## 🔧 开发

### 代码质量
```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

### 打包分发
```bash
# 构建包
python setup.py sdist bdist_wheel

# 使用 PyInstaller 打包可执行文件
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

## 📋 支持的模型

### Anthropic Claude
- Claude 3.5 Sonnet/Haiku
- Claude 4 Sonnet/Opus
- Claude 3.7 Sonnet
- 支持思维链推理模式

### Amazon Nova
- Nova Premier/Pro/Lite/Micro
- 多模态支持

### DeepSeek
- DeepSeek R1
- 推理优化模型

## 🔒 安全注意事项

- **凭证安全**: 不要在代码中硬编码 AWS 凭证
- **日志安全**: 敏感信息不会记录到日志文件
- **输入验证**: 对用户输入进行验证和清理
- **文件安全**: 上传文件大小和类型限制

## 🐛 故障排除

### 常见问题

1. **AWS 凭证错误**
   - 检查 `~/.aws/credentials` 文件
   - 确认 IAM 用户有 Bedrock 访问权限

2. **模型访问被拒绝**
   - 在 AWS 控制台启用相应的 Bedrock 模型
   - 检查区域设置是否正确

3. **网络连接问题**
   - 检查代理设置
   - 确认网络连接正常

4. **依赖安装失败**
   - 更新 pip: `pip install --upgrade pip`
   - 使用国内镜像: `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt`

## 📝 更新日志

### v2.0.0 (当前版本)
- 完全重构代码架构
- 添加现代化 UI 组件
- 增强错误处理和重试机制
- 添加单元测试
- 支持更多文件格式
- 改进配置管理

### v1.0.0
- 基础聊天功能
- 多模型支持
- 简单文件上传

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👨‍💻 作者

**James Huang** - 初始开发

## 🙏 致谢

- AWS Bedrock 团队
- Anthropic Claude 团队
- 开源社区的贡献者们