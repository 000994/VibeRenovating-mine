"""
腾讯混元3D API 客户端
=====================
这是一个完整的Hunyuan3D-2.1 API客户端实现

使用前需要:
1. 部署Hunyuan3D API服务器（见下方部署说明）
2. 安装依赖: pip install requests

部署API服务器:
git clone https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
cd Hunyuan3D-2.1
pip install -r requirements.txt
python api_server.py --port 8081

官方文档:
- GitHub: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1
- API文档: 启动后访问 http://localhost:8081/docs
"""

import base64
import requests
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Hunyuan3DClient:
    """
    Hunyuan3D API客户端
    
    特点:
    - 无需API Key认证（本地部署服务）
    - 支持同步和异步生成
    - 自动图片Base64编码
    - 完整的错误处理
    """
    
    def __init__(self, base_url: str = "http://localhost:8081", timeout: int = 300):
        """
        初始化客户端
        
        Args:
            base_url: API服务器地址（默认本地部署地址）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def is_service_ready(self) -> bool:
        """
        检查服务是否就绪
        
        Returns:
            bool: 服务是否健康
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5
            )
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except Exception:
            return False
    
    def encode_image(self, image_path: str) -> str:
        """
        将图片文件转换为Base64编码
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: Base64编码字符串
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def decode_model(self, model_base64: str, output_path: str) -> str:
        """
        将Base64编码的模型保存为文件
        
        Args:
            model_base64: Base64编码的模型数据
            output_path: 输出文件路径
            
        Returns:
            str: 保存的文件路径
        """
        model_data = base64.b64decode(model_base64)
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            f.write(model_data)
        
        return str(path)
    
    def generate(
        self,
        image_path: str,
        output_path: str = "output.glb",
        texture: bool = False,
        seed: int = 1234,
        remove_background: bool = True,
        octree_resolution: int = 256,
        num_inference_steps: int = 5,
        guidance_scale: float = 5.0,
        num_chunks: int = 8000,
        face_count: int = 40000,
        sync: bool = True
    ) -> str:
        """
        生成3D模型
        
        Args:
            image_path: 输入图片路径
            output_path: 输出模型路径（默认GLB格式）
            texture: 是否生成纹理（PBR材质）
            seed: 随机种子（用于复现）
            remove_background: 是否自动移除背景
            octree_resolution: 网格分辨率（64-512，越大越精细）
            num_inference_steps: 推理步数（1-20，越大质量越好）
            guidance_scale: 引导强度（0.1-20.0）
            num_chunks: 处理块数（内存优化参数）
            face_count: 最大面数（纹理生成时）
            sync: 是否同步等待（True=同步，False=异步）
            
        Returns:
            str: 保存的模型文件路径
            
        Raises:
            Exception: 生成失败时抛出异常
        """
        # 编码图片
        image_base64 = self.encode_image(image_path)
        
        # 构建请求参数
        request_data = {
            "image": image_base64,
            "remove_background": remove_background,
            "texture": texture,
            "seed": seed,
            "octree_resolution": octree_resolution,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "num_chunks": num_chunks,
            "face_count": face_count
        }
        
        if sync:
            # 同步生成
            response = self.session.post(
                f"{self.base_url}/generate",
                json=request_data,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # 直接保存二进制文件
                path = Path(output_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(path, 'wb') as f:
                    f.write(response.content)
                
                return str(path)
            else:
                error_msg = response.json().get("text", "Unknown error")
                raise Exception(f"Generation failed: {error_msg}")
        else:
            # 异步生成
            response = self.session.post(
                f"{self.base_url}/send",
                json=request_data,
                timeout=30
            )
            
            if response.status_code == 200:
                task_id = response.json()["uid"]
                return self.wait_for_completion(task_id, output_path)
            else:
                raise Exception(f"Failed to start generation: {response.json()}")
    
    def start_async_generation(
        self,
        image_path: str,
        texture: bool = False,
        seed: int = 1234,
        **kwargs
    ) -> str:
        """
        启动异步生成任务（不等待完成）
        
        Args:
            image_path: 输入图片路径
            texture: 是否生成纹理
            seed: 随机种子
            **kwargs: 其他生成参数
            
        Returns:
            str: 任务ID
        """
        image_base64 = self.encode_image(image_path)
        
        request_data = {
            "image": image_base64,
            "texture": texture,
            "seed": seed,
            **kwargs
        }
        
        response = self.session.post(
            f"{self.base_url}/send",
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["uid"]
        else:
            raise Exception(f"Failed to start generation: {response.json()}")
    
    def check_status(self, task_id: str) -> Dict[str, Any]:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict: 状态信息，包含:
                - status: processing/texturing/completed/error
                - model_base64: 完成时的模型数据
                - message: 错误时的错误信息
        """
        response = self.session.get(
            f"{self.base_url}/status/{task_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Status check failed: {response.json()}")
    
    def wait_for_completion(
        self,
        task_id: str,
        output_path: str = "output.glb",
        max_wait_time: int = 600,
        poll_interval: int = 5,
        verbose: bool = True
    ) -> str:
        """
        等待异步任务完成并保存结果
        
        Args:
            task_id: 任务ID
            output_path: 输出文件路径
            max_wait_time: 最大等待时间（秒）
            poll_interval: 查询间隔（秒）
            verbose: 是否打印进度
            
        Returns:
            str: 保存的模型文件路径
            
        Raises:
            Exception: 超时或生成失败
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            status = self.check_status(task_id)
            
            if verbose:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Status: {status['status']}")
            
            if status["status"] == "completed":
                # 保存模型
                return self.decode_model(status["model_base64"], output_path)
            
            elif status["status"] == "error":
                error_msg = status.get("message", "Unknown error")
                raise Exception(f"Generation failed: {error_msg}")
            
            # 等待下一次查询
            time.sleep(poll_interval)
        
        raise Exception(f"Timeout: Task did not complete in {max_wait_time}s")
    
    def generate_high_quality(
        self,
        image_path: str,
        output_path: str = "output_hq.glb",
        texture: bool = True
    ) -> str:
        """
        高质量生成（预设最佳参数）
        
        Args:
            image_path: 输入图片路径
            output_path: 输出文件路径
            texture: 是否生成纹理
            
        Returns:
            str: 保存的模型路径
        """
        return self.generate(
            image_path=image_path,
            output_path=output_path,
            texture=texture,
            octree_resolution=512,      # 最高分辨率
            num_inference_steps=20,     # 最大步数
            guidance_scale=7.5,         # 更强引导
            face_count=80000            # 更多面数
        )
    
    def generate_fast(
        self,
        image_path: str,
        output_path: str = "output_fast.glb",
        texture: bool = False
    ) -> str:
        """
        快速生成（预设速度优化参数）
        
        Args:
            image_path: 输入图片路径
            output_path: 输出文件路径
            texture: 是否生成纹理
            
        Returns:
            str: 保存的模型路径
        """
        return self.generate(
            image_path=image_path,
            output_path=output_path,
            texture=texture,
            octree_resolution=128,      # 低分辨率
            num_inference_steps=3,      # 最少步数
            guidance_scale=3.0,         # 低引导
            face_count=20000            # 较少面数
        )


def main():
    """使用示例"""
    
    print("=" * 60)
    print("腾讯混元3D API 客户端示例")
    print("=" * 60)
    
    # 创建客户端
    client = Hunyuan3DClient(
        base_url="http://localhost:8081",
        timeout=300
    )
    
    # 1. 检查服务状态
    print("\n[1] 检查服务状态...")
    if client.is_service_ready():
        print("✓ 服务就绪")
    else:
        print("✗ 服务未就绪，请确保API服务器已启动")
        print("  启动命令: python api_server.py --port 8081")
        return
    
    # 示例图片路径（需要用户提供）
    image_path = "input.png"
    
    # 检查图片是否存在
    if not Path(image_path).exists():
        print(f"\n提示: 请准备一张测试图片 '{image_path}'")
        print("或修改 image_path 变量为你的图片路径")
        return
    
    # 2. 快速生成（仅形状，无纹理）
    print(f"\n[2] 快速生成（仅形状）...")
    try:
        output = client.generate_fast(
            image_path=image_path,
            output_path="output_shape.glb",
            texture=False
        )
        print(f"✓ 生成成功: {output}")
    except Exception as e:
        print(f"✗ 生成失败: {e}")
    
    # 3. 标准生成（带纹理）
    print(f"\n[3] 标准生成（带纹理）...")
    try:
        output = client.generate(
            image_path=image_path,
            output_path="output_textured.glb",
            texture=True,
            sync=True
        )
        print(f"✓ 生成成功: {output}")
    except Exception as e:
        print(f"✗ 生成失败: {e}")
    
    # 4. 异步生成示例
    print(f"\n[4] 异步生成示例...")
    try:
        task_id = client.start_async_generation(
            image_path=image_path,
            texture=True,
            seed=9999
        )
        print(f"任务ID: {task_id}")
        
        # 等待完成
        output = client.wait_for_completion(
            task_id=task_id,
            output_path="output_async.glb",
            verbose=True
        )
        print(f"✓ 异步生成成功: {output}")
    except Exception as e:
        print(f"✗ 异步生成失败: {e}")
    
    # 5. 高质量生成
    print(f"\n[5] 高质量生成...")
    try:
        output = client.generate_high_quality(
            image_path=image_path,
            output_path="output_hq.glb",
            texture=True
        )
        print(f"✓ 高质量生成成功: {output}")
    except Exception as e:
        print(f"✗ 高质量生成失败: {e}")
    
    print("\n" + "=" * 60)
    print("完成！生成的GLB文件可用以下工具查看：")
    print("  - Blender (导入GLB)")
    print("  - Windows 10+ 内置3D查看器")
    print("  - https://3dviewer.net (在线查看)")
    print("=" * 60)


if __name__ == "__main__":
    main()


"""
快速使用示例：

from hunyuan3d_client import Hunyuan3DClient

# 初始化
client = Hunyuan3DClient("http://localhost:8081")

# 检查服务
if client.is_service_ready():
    # 快速生成
    client.generate_fast("input.png", "output.glb")
    
    # 高质量生成
    client.generate_high_quality("input.png", "output.glb", texture=True)
    
    # 自定义参数
    client.generate(
        "input.png",
        "custom.glb",
        texture=True,
        octree_resolution=512,
        num_inference_steps=20
    )
"""