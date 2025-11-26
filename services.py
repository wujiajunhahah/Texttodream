import os
import sys
import json
import time
import requests
import tenacity
from tqdm import tqdm
import logging

class DreamToModelConverter:
    def __init__(self, app=None):
        self.app = app
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.tripo_api_key = os.getenv('TRIPO_API_KEY')

        if not self.deepseek_api_key:
            if app:
                app.logger.error("未设置DEEPSEEK_API_KEY环境变量")
            print("错误: 未设置DEEPSEEK_API_KEY环境变量")
            # 不强制退出，允许应用启动，但在调用时可能会失败
            
        if not self.tripo_api_key:
             if app:
                app.logger.warning("未设置TRIPO_API_KEY环境变量，将无法生成3D模型")
             print("警告: 未设置TRIPO_API_KEY环境变量，将无法生成3D模型")

    def test_deepseek_api(self):
        """测试 DeepSeek API 是否可用"""
        if not self.deepseek_api_key:
            return False
            
        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.deepseek_api_key}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "user", "content": "你好，这是一个测试请求，请回复 '测试成功'"}
                    ],
                    "temperature": 0.3
                },
                timeout=30
            )
            return response.status_code == 200
        except Exception:
            return False

    @tenacity.retry(
        wait=tenacity.wait_fixed(10),  # 每次重试等待10秒
        stop=tenacity.stop_after_attempt(5),  # 最多重试5次
        retry=tenacity.retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
        reraise=True
    )
    def extract_keywords(self, dream_text):
        """使用DeepSeek API从梦境文本中提取关键词、象征意义和解梦"""
        if not self.deepseek_api_key:
            raise Exception("未配置 DeepSeek API Key")

        prompt = f"""
        请分析以下梦境描述，并提取以下内容:
        1. 5-8个最能代表这个梦境的关键词或短语
        2. 3-5个梦境中的核心象征物或场景
        3. 这个梦境可能传达的主要情感或感受
        4. 一个能够视觉化表达这个梦境的简短描述(50字以内)
        5. 对这个梦境的心理学解析(200字以内)

        请以JSON格式返回结果，包含字段: keywords, symbols, emotions, visual_description, interpretation

        梦境描述:
        {dream_text}
        """

        try:
            response = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.deepseek_api_key}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "你是一个专业的梦境分析师，擅长提取梦境中的关键元素和象征意义。请直接返回JSON格式的结果，不要添加任何Markdown格式。"},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=90  # 增加超时时间至90秒
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API 调用失败，状态码: {response.status_code}")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # 从Markdown中提取JSON
            json_content = self.extract_json_from_markdown(content)

            # 手动解析 JSON，确保兼容性
            analysis = json.loads(json_content)

            # 验证返回字段
            required_fields = ["keywords", "symbols", "emotions", "visual_description", "interpretation"]
            for field in required_fields:
                if field not in analysis:
                    raise Exception(f"DeepSeek API 返回缺少字段: {field}")

            return analysis

        except requests.exceptions.Timeout:
            raise
        except Exception as e:
            raise

    def extract_json_from_markdown(self, text):
        """从Markdown文本中提取JSON"""
        import re
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)

        if json_match:
            return json_match.group(1)
        else:
            cleaned_text = text.strip()
            if cleaned_text.startswith("```") and cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[3:-3].strip()
            return cleaned_text

    def generate_model_prompt(self, analysis):
        """根据分析结果生成3D模型提示词"""
        symbols = ", ".join(analysis["symbols"])
        emotions = ", ".join(analysis["emotions"])
        model_prompt = f"{analysis['visual_description']} 包含 {symbols}. 整体氛围: {emotions}"
        return model_prompt

    def generate_3d_model(self, model_prompt):
        """使用Tripo API生成3D模型"""
        if not self.tripo_api_key:
             raise Exception("未配置 Tripo API Key")

        try:
            # 创建任务
            response = requests.post(
                "https://api.tripo3d.ai/v2/openapi/task",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.tripo_api_key}"
                },
                json={
                    "type": "text_to_model",
                    "prompt": model_prompt
                },
                timeout=30
            )

            if response.status_code != 200:
                return None

            result = response.json()
            task_id = result.get("data", {}).get("task_id")
            if not task_id:
                return None

            # 轮询任务状态
            model_url = None
            max_attempts = 60
            for attempt in range(max_attempts):
                time.sleep(10)
                status_response = requests.get(
                    f"https://api.tripo3d.ai/v2/openapi/task/{task_id}",
                    headers={"Authorization": f"Bearer {self.tripo_api_key}"},
                    timeout=30
                )

                if status_response.status_code != 200:
                    continue

                status_data = status_response.json()
                task_status = status_data.get("data", {}).get("status")

                if task_status == "success":
                    data = status_data.get("data", {})
                    output = data.get("output", {})
                    result = data.get("result", {})

                    model_url = (
                        output.get("pbr_model") or
                        output.get("model") or
                        result.get("pbr_model", {}).get("url") or
                        result.get("model", {}).get("url")
                    )

                    if not model_url:
                        return None

                    break
                elif task_status in ["failed", "cancelled", "unknown"]:
                    return None

            return model_url

        except Exception:
            return None

    def process_dream(self, dream_text, user_id, dream_id=None, update_progress_callback=None):
        """
        处理梦境并生成3D模型
        update_progress_callback: function(dream_id, stage, progress, remaining_minutes, status)
        """
        try:
            if self.app:
                self.app.logger.info(f'开始处理用户 {user_id} 的梦境')
            
            # 如果提供了dream_id，则初始化进度跟踪
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "开始", 5, 20, "正在启动梦境处理...")
            
            # 测试 DeepSeek API 可用性
            if not self.test_deepseek_api():
                if self.app:
                    self.app.logger.error('DeepSeek API 不可用')
                if dream_id and update_progress_callback:
                    update_progress_callback(dream_id, "失败", 0, 0, "API服务暂时不可用，请稍后再试")
                raise Exception("DeepSeek API 服务暂时不可用，请稍后再试")

            # 提取关键词和分析
            if self.app:
                self.app.logger.info('开始提取关键词和分析')
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "分析梦境", 20, 15, "正在提取关键词和进行梦境分析...")
            
            analysis = self.extract_keywords(dream_text)
            
            # 生成3D模型
            if self.app:
                self.app.logger.info('开始生成3D模型')
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "生成模型", 40, 10, "正在生成3D模型...")
            
            model_prompt = self.generate_model_prompt(analysis)
            model_url = self.generate_3d_model(model_prompt)
            
            if not model_url:
                if self.app:
                    self.app.logger.error('3D模型生成失败')
                if dream_id and update_progress_callback:
                    update_progress_callback(dream_id, "失败", 0, 0, "3D模型生成失败，请稍后重试")
                raise Exception("3D模型生成失败，请稍后重试")

            # 创建用户目录
            user_dir = os.path.join('static', 'models', f'user_{user_id}')
            os.makedirs(user_dir, exist_ok=True)
            
            # 下载模型文件
            if self.app:
                self.app.logger.info('下载模型文件')
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "下载模型", 60, 5, "正在下载生成的模型文件...")
            
            model_filename = f"dream_{int(time.time())}.glb"
            model_path = os.path.join(user_dir, model_filename)
            
            # 下载文件
            response = requests.get(model_url, stream=True)
            if response.status_code != 200:
                if dream_id and update_progress_callback:
                    update_progress_callback(dream_id, "失败", 0, 0, "下载模型文件失败")
                raise Exception("下载模型文件失败")
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            
            with open(model_path, 'wb') as f, tqdm(
                desc="下载模型",
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(block_size):
                    size = f.write(data)
                    pbar.update(size)
            
            # 优化模型处理
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "优化处理", 80, 3, "正在优化模型和处理资源...")
            
            # 构建相对路径
            relative_model_path = os.path.join('models', f'user_{user_id}', model_filename)
            
            # 返回结果字典
            result = {
                'model_path': relative_model_path,
                'keywords': json.dumps(analysis['keywords']),
                'symbols': json.dumps(analysis['symbols']),
                'emotions': json.dumps(analysis['emotions']),
                'visual_description': analysis['visual_description'],
                'interpretation': analysis['interpretation']
            }
            
            if self.app:
                self.app.logger.info(f'梦境处理完成，模型路径: {relative_model_path}')
            return result
            
        except Exception as e:
            if self.app:
                self.app.logger.error(f'处理梦境时发生错误: {str(e)}')
            # 更新失败状态
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "失败", 0, 0, f"处理失败: {str(e)}")
            raise

