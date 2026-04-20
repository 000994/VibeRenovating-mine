# 腾讯混元3D API 文档索引

本目录包含完整的腾讯混元3D (Hunyuan3D) API使用指南。

## 文档列表

| 文件 | 说明 | 推荐阅读顺序 |
|-----|------|------------|
| `hunyuan_api_comparison.md` | **API对比说明** - 区分混元生文和混元3D | 1️️ 先看这个 |
| `hunyuan3d_quick_reference.md` | **快速参考卡** - 一分钟速查表 | 2️⃣ 快速入门 |
| `hunyuan3d_api_summary.md` | **完整API文档** - 详细说明 | 3️⃣ 深入了解 |
| `hunyuan3d_client.py` | **Python客户端** - 可直接使用 | 4️⃣ 实践代码 |

---

## 快速导航

### 我想快速了解区别
→ 打开 `hunyuan_api_comparison.md`

### 我想快速开始使用
→ 打开 `hunyuan3d_quick_reference.md`

### 我想详细了解API
→ 打开 `hunyuan3d_api_summary.md`

### 我想直接用代码
→ 运行 `hunyuan3d_client.py`

---

## 核心要点

### ⚠️ 重要认知
腾讯混元3D **不是云端API**，而是**本地开源模型**！

- ❌ 没有云端API服务
- ❌ 不需要API Key
- ❌ 不兼容OpenAI SDK
- ✓ 需要自己部署GPU服务器
- ✓ 完全免费开源

### 🎯 正确使用流程

1. **部署服务器**（必需）
   ```bash
   git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
   python api_server.py --port 8081
   ```

2. **使用客户端**
   ```python
   from hunyuan3d_client import Hunyuan3DClient
   client = Hunyuan3DClient("http://localhost:8081")
   client.generate("input.png", "output.glb")
   ```

---

## 文档内容概览

### 1. API对比说明
- 混元生文API vs 混元3D API
- 常见误区纠正
- 正确代码示例
- 官方文档链接

### 2. 快速参考卡
- 一分钟快速开始
- API端点速查表
- 参数速查表
- 预设配置
- 常见问题速查

### 3. 完整API文档
- API服务架构详解
- 端点详解（4个主要端点）
- 认证方式说明
- 请求格式详解（9个参数）
- 响应格式详解
- 部署要求和步骤
- Python完整实现示例
- 常见问题解答
- 最佳实践建议
- 资源链接汇总

### 4. Python客户端
- 完整的客户端类实现
- 同步和异步调用
- 图片编码/解码
- 健康检查
- 状态查询
- 预设配置（快速/高质量）
- 详细的使用示例
- 错误处理

---

## 常见问题速查

**Q: 我想用API Key调用混元3D？**
→ ❌ 不可能。混元3D没有云端API。看对比文档了解详情。

**Q: 能用OpenAI SDK调用吗？**
→ ❌ 不能。混元3D不兼容OpenAI SDK。使用提供的客户端代码。

**Q: 有免费体验吗？**
→ ✓ 有。访问 https://3d.hunyuan.tencent.com 无需部署。

**Q: 部署需要什么？**
→ ✓ NVIDIA GPU（16GB+ VRAM），Python 3.10，PyTorch。

**Q: 生成速度如何？**
→ 形状10-15秒，纹理30-40秒。

---

## 快速开始步骤

### 步骤1: 部署服务器
```bash
# 克隆仓库
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
cd Hunyuan3D-2.1

# 安装依赖
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt

# 启动服务器
python api_server.py --port 8081

# 查看交互式文档
# 浏览器打开: http://localhost:8081/docs
```

### 步骤2: 使用客户端
```python
# 导入客户端
from hunyuan3d_client import Hunyuan3DClient

# 创建连接
client = Hunyuan3DClient("http://localhost:8081")

# 检查服务
if client.is_service_ready():
    print("服务就绪")
    
    # 快速生成
    output = client.generate_fast("input.png", "output.glb")
    
    # 高质量生成
    output = client.generate_high_quality("input.png", "output.glb", texture=True)
```

---

## 官方资源

| 类型 | URL |
|-----|-----|
| GitHub仓库 | https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 |
| HuggingFace模型 | https://huggingface.co/tencent/Hunyuan3D-2.1 |
| 官方体验站 | https://3d.hunyuan.tencent.com |
| HuggingFace演示 | https://huggingface.co/spaces/tencent/Hunyuan3D-2.1 |
| 技术报告 | https://arxiv.org/pdf/2506.15442 |
| ComfyUI插件 | https://github.com/visualbruno/ComfyUI-Hunyuan3d-2-1 |

---

## 技术支持

### 文档问题
如果文档有不清楚的地方，请查阅：
- 官方GitHub README
- 启动服务器后的交互式文档（http://localhost:8081/docs）

### 使用问题
- GitHub Issues: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/issues
- 官方微信群: 见GitHub README中的二维码
- Discord: https://discord.gg/dNBrdrGGMa

---

## 文档更新

- **创建日期**: 2026-03-31
- **基于版本**: Hunyuan3D-2.1
- **数据来源**: 官方GitHub、HuggingFace、腾讯云文档

---

## 总结

**记住3个关键点**:

1. **混元3D = 本地部署**（不是云端API）
2. **无需API Key**（本地服务无认证）
3. **使用提供的客户端**（不兼容OpenAI SDK）

按推荐顺序阅读文档，你将全面掌握混元3D API的正确使用方式！