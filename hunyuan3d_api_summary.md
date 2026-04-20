# 腾讯混元3D (Hunyuan3D) API 使用指南

## 重要说明

腾讯混元3D **不是云API服务**，而是开源的本地部署解决方案。您需要自行部署API服务器，然后通过API调用进行3D生成。

---

## 一、API服务架构

### 1.1 服务类型
- **本地部署API服务** (非云端API)
- 基于 FastAPI 框架
- 使用 Pydantic 进行参数验证
- 支持同步和异步两种调用模式

### 1.2 官方资源
| 资源类型 | URL | 说明 |
|---------|-----|------|
| GitHub仓库 | https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 | 最新版本2.1，完整源码 |
| HuggingFace模型 | https://huggingface.co/tencent/Hunyuan3D-2.1 | 预训练模型下载 |
| 官方体验网站 | https://3d.hunyuan.tencent.com | 在线体验（无需API） |
| HuggingFace演示 | https://huggingface.co/spaces/tencent/Hunyuan3D-2.1 | 在线演示空间 |

---

## 二、API端点详解

### 2.1 基础URL
```
http://localhost:8081  (默认本地部署地址)
```

**注意**: 可通过启动参数修改地址和端口：
```bash
python api_server.py --host 0.0.0.0 --port 8081
```

### 2.2 主要端点

| 端点 | 方法 | 功能 | 标签 |
|-----|------|------|------|
| `/generate` | POST | 同步生成3D模型 | generation |
| `/send` | POST | 异步生成任务（返回任务ID） | generation |
| `/status/{uid}` | GET | 查询任务状态 | status |
| `/health` | GET | 健康检查 | status |
| `/docs` | GET | Swagger交互式文档 | - |
| `/redoc` | GET | ReDoc文档 | - |

---

## 三、认证方式

### 3.1 当前认证方式
**无认证要求** - 本地部署的API服务默认不需要API Key或Token认证。

原因：
- 这是本地部署服务，不是云端API
- 通过CORS允许所有来源访问（可配置限制）
- 主要用于私有环境或内部服务

### 3.2 安全建议
如需添加认证，可考虑：
1. **API Key验证**: 在FastAPI中添加中间件
2. **网络隔离**: 仅允许特定IP访问
3. **反向代理**: 通过Nginx添加认证层

### 3.3 与腾讯云API的区别
| 特性 | 混元生文API (云服务) | 混元3D API (本地部署) |
|-----|------------------|-------------------|
| 服务类型 | 云端API | 本地部署 |
| 认证方式 | API Key (Bearer Token) | 无认证 |
| 端点URL | https://api.hunyuan.cloud.tencent.com/v1 | http://localhost:8081 |
| 计费方式 | 按调用次数计费 | 需自备GPU资源 |
| 并发限制 | 5个并发（默认） | 可配置（默认5） |

---

## 四、请求格式详解

### 4.1 GenerationRequest 参数模型

```python
class GenerationRequest(BaseModel):
    """请求参数模型"""
    
    # 必需参数
    image: str  # Base64编码的输入图片
    
    # 可选参数（带默认值）
    remove_background: bool = True      # 自动去除背景
    texture: bool = False               # 是否生成纹理
    seed: int = 1234                    # 随机种子（0 到 2^32-1）
    
    # 生成控制参数
    octree_resolution: int = 256        # 网格分辨率（64-512）
    num_inference_steps: int = 5        # 推理步数（1-20）
    guidance_scale: float = 5.0         # 引导强度（0.1-20.0）
    
    # 性能参数
    num_chunks: int = 8000              # 处理块数（1000-20000）
    face_count: int = 40000             # 最大面数（1000-100000）
```

### 4.2 参数详解表

| 参数 | 类型 | 默认值 | 范围 | 说明 |
|-----|------|--------|------|------|
| `image` | string | **必需** | - | Base64编码的PNG/JPG图片 |
| `remove_background` | bool | True | - | 是否自动移除背景 |
| `texture` | bool | False | - | 是否生成PBR纹理材质 |
| `seed` | int | 1234 | 0 - 4,294,967,295 | 随机种子，用于复现 |
| `octree_resolution` | int | 256 | 64 - 512 | 网格细节程度 |
| `num_inference_steps` | int | 5 | 1 - 20 | 生成质量（越大越好但越慢） |
| `guidance_scale` | float | 5.0 | 0.1 - 20.0 | 生成引导强度 |
| `num_chunks` | int | 8000 | 1000 - 20000 | 内存优化参数 |
| `face_count` | int | 40000 | 1000 - 100000 | 纹理网格面数限制 |

---

## 五、响应格式

### 5.1 同步生成响应
```
Content-Type: application/octet-stream
返回: .glb 或 .obj 文件（二进制数据）
```

### 5.2 异步生成响应

**POST /send 返回：**
```json
{
  "uid": "550e8400-e29b-41d4-a716-446655440000"
}
```

**GET /status/{uid} 返回：**

**处理中：**
```json
{
  "status": "processing"
}
```

**正在添加纹理：**
```json
{
  "status": "texturing"
}
```

**完成：**
```json
{
  "status": "completed",
  "model_base64": "Base64编码的GLB文件..."
}
```

**错误：**
```json
{
  "status": "error",
  "message": "错误描述"
}
```

### 5.3 健康检查响应
```json
{
  "status": "healthy",
  "worker_id": "a1b2c3"
}
```

---

## 六、部署要求

### 6.1 系统要求
- **GPU**: NVIDIA GPU（推荐至少16GB VRAM）
- **内存**: 
  - 仅形状生成：10GB
  - 仅纹理生成：21GB
  - 形状+纹理：29GB
- **Python**: 3.10
- **PyTorch**: 2.5.1+cu124
- **操作系统**: Linux/Windows/MacOS

### 6.2 模型文件
需要下载的模型：
- **Hunyuan3D-Shape-v2-1**: 3.3B参数（形状生成）
- **Hunyuan3D-Paint-v2-1**: 2B参数（纹理生成）

---

## 七、Python实现示例

### 7.1 完整客户端实现

```python
"""
Hunyuan3D API 客户端示例
"""
import base64
import requests
import time
import json
from pathlib import Path


class Hunyuan3DClient:
    """Hunyuan3D API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8081"):
        """
        初始化客户端
        
        Args:
            base_url: API服务器地址
        """
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> dict:
        """健康检查"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def encode_image(self, image_path: str) -> str:
        """
        将图片转换为Base64编码
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            Base64编码字符串
        """
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def generate_sync(
        self,
        image_path: str,
        texture: bool = False,
        seed: int = 1234,
        remove_background: bool = True,
        octree_resolution: int = 256,
        num_inference_steps: int = 5,
        guidance_scale: float = 5.0,
        output_path: str = "output.glb"
    ) -> str:
        """
        同步生成3D模型
        
        Args:
            image_path: 输入图片路径
            texture: 是否生成纹理
            seed: 随机种子
            remove_background: 是否移除背景
            octree_resolution: 网格分辨率
            num_inference_steps: 推理步数
            guidance_scale: 引导强度
            output_path: 输出文件路径
            
        Returns:
            保存的文件路径
        """
        # 编码图片
        image_base64 = self.encode_image(image_path)
        
        # 构建请求
        request_data = {
            "image": image_base64,
            "remove_background": remove_background,
            "texture": texture,
            "seed": seed,
            "octree_resolution": octree_resolution,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale
        }
        
        # 发送请求
        response = self.session.post(
            f"{self.base_url}/generate",
            json=request_data,
            timeout=300  # 5分钟超时
        )
        
        if response.status_code == 200:
            # 保存文件
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return output_path
        else:
            raise Exception(f"Generation failed: {response.json()}")
    
    def generate_async(
        self,
        image_path: str,
        texture: bool = False,
        seed: int = 1234,
        remove_background: bool = True
    ) -> str:
        """
        异步生成3D模型（返回任务ID）
        
        Args:
            image_path: 输入图片路径
            texture: 是否生成纹理
            seed: 随机种子
            remove_background: 是否移除背景
            
        Returns:
            任务ID
        """
        # 编码图片
        image_base64 = self.encode_image(image_path)
        
        # 构建请求
        request_data = {
            "image": image_base64,
            "remove_background": remove_background,
            "texture": texture,
            "seed": seed
        }
        
        # 发送异步请求
        response = self.session.post(
            f"{self.base_url}/send",
            json=request_data
        )
        
        if response.status_code == 200:
            return response.json()["uid"]
        else:
            raise Exception(f"Failed to start generation: {response.json()}")
    
    def check_status(self, task_id: str) -> dict:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            状态信息
        """
        response = self.session.get(
            f"{self.base_url}/status/{task_id}"
        )
        return response.json()
    
    def wait_for_completion(
        self,
        task_id: str,
        timeout: int = 600,
        poll_interval: int = 5,
        output_path: str = "output_async.glb"
    ) -> str:
        """
        等待任务完成并保存结果
        
        Args:
            task_id: 任务ID
            timeout: 最大等待时间（秒）
            poll_interval: 查询间隔（秒）
            output_path: 输出文件路径
            
        Returns:
            保存的文件路径
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_status(task_id)
            
            if status["status"] == "completed":
                # 解码并保存文件
                model_base64 = status["model_base64"]
                model_data = base64.b64decode(model_base64)
                
                with open(output_path, 'wb') as f:
                    f.write(model_data)
                
                return output_path
            
            elif status["status"] == "error":
                raise Exception(f"Generation error: {status.get('message', 'Unknown error')}")
            
            # 等待下一次查询
            time.sleep(poll_interval)
        
        raise Exception(f"Timeout: Task did not complete within {timeout} seconds")


# 使用示例
def main():
    # 创建客户端
    client = Hunyuan3DClient("http://localhost:8081")
    
    # 健康检查
    health = client.health_check()
    print(f"Service status: {health}")
    
    # 示例1: 同步生成（无纹理）
    print("\n=== Sync generation (no texture) ===")
    output = client.generate_sync(
        image_path="input.png",
        texture=False,
        seed=42,
        output_path="output_shape.glb"
    )
    print(f"Saved to: {output}")
    
    # 示例2: 异步生成（带纹理）
    print("\n=== Async generation (with texture) ===")
    task_id = client.generate_async(
        image_path="input.png",
        texture=True,
        seed=42
    )
    print(f"Task ID: {task_id}")
    
    # 等待完成
    output = client.wait_for_completion(
        task_id,
        timeout=600,
        output_path="output_textured.glb"
    )
    print(f"Saved to: {output}")


if __name__ == "__main__":
    main()
```

### 7.2 简化调用示例

```python
import base64
import requests

# 1. 编码图片
def encode_image(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

# 2. 同步生成
image_b64 = encode_image("input.png")
response = requests.post(
    "http://localhost:8081/generate",
    json={
        "image": image_b64,
        "texture": True,
        "seed": 1234
    },
    timeout=300
)

# 3. 保存结果
with open("output.glb", 'wb') as f:
    f.write(response.content)
print("Generated successfully!")
```

### 7.3 使用OpenAI SDK风格（不适用）

**注意**: 混元3D API **不支持** OpenAI SDK，因为：
- 它不是OpenAI兼容接口
- 它是专门的3D生成API
- 需要Base64图片输入，返回二进制文件

混元生文API（文本生成）才支持OpenAI SDK：
```python
from openai import OpenAI
client = OpenAI(
    api_key="YOUR_HUNYUAN_API_KEY",
    base_url="https://api.hunyuan.cloud.tencent.com/v1"
)
# 仅用于文本生成，不适用于3D生成
```

---

## 八、部署服务器

### 8.1 快速部署

```bash
# 1. 克隆仓库
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1.git
cd Hunyuan3D-2.1

# 2. 安装依赖
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt

# 3. 编译自定义模块
cd hy3dpaint/custom_rasterizer && pip install -e . && cd ../..
cd hy3dpaint/DifferentiableRenderer && bash compile_mesh_painter.sh && cd ../..

# 4. 启动API服务器
python api_server.py \
    --model_path tencent/Hunyuan3D-2.1 \
    --subfolder hunyuan3d-dit-v2-1 \
    --port 8081 \
    --low_vram_mode  # 低显存模式（可选）

# 5. 查看交互式文档
# 浏览器打开: http://localhost:8081/docs
```

### 8.2 Docker部署

```bash
# 使用官方Docker镜像（推荐）
cd docker
docker-compose up -d

# 或手动构建
docker build -t hunyuan3d-api .
docker run -d -p 8081:8081 --gpus all hunyuan3d-api
```

---

## 九、常见问题

### Q1: 混元3D有云端API吗？
**答**: 目前没有。混元3D是开源模型，需要自行部署。云端只有混元生文和混元生图API。

### Q2: 生成速度如何？
**答**: 
- 仅形状生成：约10-15秒
- 形状+纹理生成：约30-40秒
- 低显存模式会更慢

### Q3: 支持哪些输出格式？
**答**: 
- GLB（推荐，支持纹理）
- OBJ（可选）

### Q4: 是否需要API Key？
**答**: 不需要。本地部署服务无认证机制。

### Q5: 如何提高生成质量？
**答**: 
1. 增加推理步数（`num_inference_steps`）
2. 提高网格分辨率（`octree_resolution`）
3. 使用高质量输入图片
4. 启用纹理生成（`texture=True`）

---

## 十、最佳实践建议

### 10.1 生产环境部署
1. 使用Docker容器化部署
2. 配置负载均衡（多worker）
3. 添加Redis缓存（异步任务管理）
4. 设置API认证中间件
5. 监控GPU资源使用

### 10.2 性能优化
1. 使用 `--low_vram_mode` 减少显存占用
2. 调整 `num_chunks` 优化内存使用
3. 使用 SSD 存储模型文件
4. 批量生成时使用异步模式

### 10.3 质量优化
```python
# 高质量生成参数
request_data = {
    "image": image_b64,
    "texture": True,
    "octree_resolution": 512,        # 最高分辨率
    "num_inference_steps": 20,       # 最大步数
    "guidance_scale": 7.5,           # 更强引导
    "face_count": 80000              # 更多面数
}
```

---

## 十一、资源链接汇总

| 类型 | 链接 |
|-----|------|
| GitHub源码 | https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1 |
| HuggingFace模型 | https://huggingface.co/tencent/Hunyuan3D-2.1 |
| API文档（本地） | http://localhost:8081/docs |
| 官方体验站 | https://3d.hunyuan.tencent.com |
| HuggingFace演示 | https://huggingface.co/spaces/tencent/Hunyuan3D-2.1 |
| 技术报告 | https://arxiv.org/pdf/2506.15442 |
| ComfyUI插件 | https://github.com/visualbruno/ComfyUI-Hunyuan3d-2-1 |
| Unity支持 | https://github.com/VR-Jobs/Hunyuan3D-2.1-Unity-XR-PC-Phone |

---

## 总结

腾讯混元3D API是一个功能强大的**本地部署3D生成服务**，具有以下特点：

1. **无云端API**: 需自行部署服务器
2. **无需认证**: 本地服务无API Key机制
3. **完整文档**: 自动生成Swagger/ReDoc文档
4. **灵活调用**: 支持同步和异步两种模式
5. **参数丰富**: 可精细控制生成过程
6. **高质量输出**: 支持PBR材质纹理

**推荐使用场景**：
- 游戏开发资产制作
- VR/AR内容创作
- 电商产品3D展示
- 工业设计可视化
- 教育/科研应用

---

文档生成时间: 2026-03-31
基于 Hunyuan3D-2.1 版本