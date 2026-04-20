# 腾讯混元API对比说明

## 关键区别

很多人混淆了腾讯混元的两种API，这是完全不同的产品：

### 混元生文API（云端API）
- **用途**: 文本生成、对话、图像生成
- **类型**: 云端付费API服务
- **认证**: 需要API Key
- **端点**: `https://api.hunyuan.cloud.tencent.com/v1`
- **兼容**: OpenAI SDK兼容
- **计费**: 按调用次数计费

### 混元3D API（本地部署）
- **用途**: 图片生成3D模型
- **类型**: 开源本地部署模型
- **认证**: 无需认证
- **端点**: `http://localhost:8081`（自己部署）
- **兼容**: 不兼容OpenAI SDK
- **成本**: 需自备GPU资源

---

## 混元生文API示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_HUNYUAN_API_KEY",  # 在腾讯云控制台获取
    base_url="https://api.hunyuan.cloud.tencent.com/v1"
)

# 文本生成
response = client.chat.completions.create(
    model="hunyuan-turbos-latest",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)

# 图像生成
response = client.images.generate(
    model="hunyuan-lite",
    prompt="一只可爱的兔子",
    size="1024x1024"
)
print(response.data[0].url)
```

**获取API Key**: https://console.cloud.tencent.com/hunyuan/start

---

## 混元3D API示例

```python
from hunyuan3d_client import Hunyuan3DClient
import base64

# 需要先部署服务器
client = Hunyuan3DClient("http://localhost:8081")  # 无需API Key

# 生成3D模型
output = client.generate(
    image_path="input.png",
    output_path="output.glb",
    texture=True
)
# 输出: GLB文件路径
```

**部署服务器**: 
```bash
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
pip install -r requirements.txt
python api_server.py --port 8081
```

---

## 功能对比表

| 功能 | 混元生文API | 混元3D API |
|-----|-----------|----------|
| 文本对话 | ✓ | ✗ |
| 图像生成 | ✓ | ✗ |
| 3D生成 | ✗ | ✓ |
| 需要GPU | ✗（云端） | ✓（本地） |
| API Key | ✓ | ✗ |
| OpenAI兼容 | ✓ | ✗ |
| 免费使用 | ✗（付费） | ✓（开源） |
| 交互式文档 | 在线控制台 | http://localhost:8081/docs |

---

## 常见误区

### ❌ 错误理解
"我想用腾讯混元的API Key调用3D生成服务"

**真相**: 混元3D没有云端API，必须自己部署。

### ❌ 错误代码
```python
# 这是错误的！混元3D不支持OpenAI SDK
from openai import OpenAI
client = OpenAI(
    api_key="YOUR_KEY",
    base_url="https://api.hunyuan.cloud.tencent.com/v1"
)
# 这个端点只能用于文本/图像生成，不支持3D生成
```

### ✅ 正确做法
```python
# 正确的混元3D使用方式
from hunyuan3d_client import Hunyuan3DClient

# 先部署服务器，然后本地连接
client = Hunyuan3DClient("http://localhost:8081")
output = client.generate("input.png", "output.glb")
```

---

## 官方文档链接

### 混元生文API文档
- 产品介绍: https://cloud.tencent.com/document/product/1729
- API文档: https://cloud.tencent.com/document/api/1729
- OpenAI兼容: https://cloud.tencent.com/document/product/1729/111007
- 控制台: https://console.cloud.tencent.com/hunyuan

### 混元3D文档
- GitHub: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- HuggingFace: https://huggingface.co/tencent/Hunyuan3D-2.1
- 体验网站: https://3d.hunyuan.tencent.com
- 技术报告: https://arxiv.org/pdf/2506.15442

---

## 总结

**记住这个关键区别**:

- **混元生文** = 云端API服务（类似OpenAI，需要API Key）
- **混元3D** = 本地开源模型（需要自己部署GPU服务器）

如果你想快速体验3D生成而不部署服务器：
- 使用官方网站: https://3d.hunyuan.tencent.com
- 使用HuggingFace演示: https://huggingface.co/spaces/tencent/Hunyuan3D-2.1

如果你需要API集成到应用：
- 必须自己部署服务器
- 使用提供的客户端代码连接本地服务器