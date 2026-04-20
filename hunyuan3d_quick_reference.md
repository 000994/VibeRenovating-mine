# 腾讯混元3D API 快速参考卡

## 一分钟快速开始

### 1. 部署服务器（必需）
```bash
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
cd Hunyuan3D-2.1
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python api_server.py --port 8081
```

### 2. 使用客户端
```python
from hunyuan3d_client import Hunyuan3DClient

client = Hunyuan3DClient("http://localhost:8081")
output = client.generate("input.png", "output.glb", texture=True)
```

---

## API端点速查

| 端点 | 用途 | 方法 |
|-----|------|------|
| `/generate` | 同步生成3D模型 | POST |
| `/send` | 异步生成（返回任务ID） | POST |
| `/status/{uid}` | 查询任务状态 | GET |
| `/health` | 健康检查 | GET |
| `/docs` | Swagger交互式文档 | GET |

---

## 请求参数速查

### 必需参数
- `image`: Base64编码的图片（必需）

### 常用参数
- `texture`: 是否生成纹理（默认False）
- `seed`: 随机种子（默认1234）
- `remove_background`: 移除背景（默认True）

### 质量参数
- `octree_resolution`: 64-512（越大越精细）
- `num_inference_steps`: 1-20（越大越好）
- `guidance_scale`: 0.1-20.0（引导强度）

### 性能参数
- `num_chunks`: 1000-20000（内存优化）
- `face_count`: 1000-100000（纹理面数）

---

## 预设配置

### 快速生成
```python
client.generate_fast("input.png", "output.glb")
# 参数: resolution=128, steps=3
```

### 高质量生成
```python
client.generate_high_quality("input.png", "output.glb", texture=True)
# 参数: resolution=512, steps=20
```

---

## 响应格式

### 同步响应
- Content-Type: `application/octet-stream`
- 内容: GLB/OBJ二进制文件

### 异步状态
```json
{"status": "processing"}        // 处理中
{"status": "texturing"}         // 正在添加纹理
{"status": "completed", "model_base64": "..."} // 完成
{"status": "error", "message": "..."}           // 错误
```

---

## 常见问题速查

**Q: 需要API Key吗？**
A: ❌ 不需要。本地部署无需认证。

**Q: 有云端API吗？**
A: ❌ 没有。必须自己部署GPU服务器。

**Q: 兼容OpenAI SDK吗？**
A: ❌ 不兼容。混元生文才兼容，3D不兼容。

**Q: 需要什么GPU？**
A: ✓ NVIDIA GPU，推荐16GB+ VRAM。

**Q: 生成速度？**
A: 形状: 10-15秒，纹理: 30-40秒。

---

## 关键区别

| | 混元生文API | 混元3D API |
|-|-----------|----------|
| 用途 | 文本/图像生成 | 3D模型生成 |
| 类型 | 云端API | 本地部署 |
| 认证 | API Key ✓ | 无认证 ✗ |
| SDK | OpenAI兼容 | 专用客户端 |

**记住**: 混元生文 = 云端付费，混元3D = 本地开源！

---

## 资源链接

- GitHub: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- 体验: https://3d.hunyuan.tencent.com
- 模型: https://huggingface.co/tencent/Hunyuan3D-2.1
- 文档: 启动后访问 http://localhost:8081/docs

---

## 快速诊断

### 服务未响应
```python
client.is_service_ready()  # False表示服务未启动
```

### 检查GPU
```bash
nvidia-smi  # 确认GPU可用
```

### 检查端口
```bash
curl http://localhost:8081/health
```

---

文档位置:
- 完整文档: hunyuan3d_api_summary.md
- 客户端代码: hunyuan3d_client.py
- 对比说明: hunyuan_api_comparison.md
- 快速参考: hunyuan3d_quick_reference.md（本文件）