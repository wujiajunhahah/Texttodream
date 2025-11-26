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
                app.logger.error("DEEPSEEK_API_KEY environment variable not set")
            print("Error: DEEPSEEK_API_KEY environment variable not set")
            
        if not self.tripo_api_key:
             if app:
                app.logger.warning("TRIPO_API_KEY environment variable not set, 3D model generation will fail")
             print("Warning: TRIPO_API_KEY environment variable not set")

    def test_deepseek_api(self):
        """Test DeepSeek API availability"""
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
                        {"role": "user", "content": "Hello, this is a test request, please reply 'Test Successful'"}
                    ],
                    "temperature": 0.3
                },
                timeout=30
            )
            return response.status_code == 200
        except Exception:
            return False

    @tenacity.retry(
        wait=tenacity.wait_fixed(10),
        stop=tenacity.stop_after_attempt(5),
        retry=tenacity.retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError)),
        reraise=True
    )
    def extract_keywords(self, dream_text):
        """Extract keywords, symbolism, and interpretation from dream text using DeepSeek API (in English)"""
        if not self.deepseek_api_key:
            raise Exception("DeepSeek API Key not configured")

        prompt = f"""
        Please analyze the following dream description and extract the following content in ENGLISH:
        1. 5-8 keywords or phrases that best represent this dream
        2. 3-5 core symbols or scenes in the dream
        3. The main emotions or feelings this dream might convey
        4. A short description (within 50 words) that can visually express this dream (for 3D model generation)
        5. A psychological interpretation of this dream (within 200 words)

        Please return the result in JSON format, including fields: keywords, symbols, emotions, visual_description, interpretation.
        Ensure the JSON is valid.

        Dream Description:
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
                        {"role": "system", "content": "You are a professional dream analyst specializing in extracting key elements and symbolism from dreams. Please return the result directly in JSON format without any Markdown formatting. IMPORTANT: All output must be in English."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                },
                timeout=90
            )

            if response.status_code != 200:
                raise Exception(f"DeepSeek API call failed, status code: {response.status_code}")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Extract JSON from Markdown
            json_content = self.extract_json_from_markdown(content)

            # Manually parse JSON
            analysis = json.loads(json_content)

            # Validate returned fields
            required_fields = ["keywords", "symbols", "emotions", "visual_description", "interpretation"]
            for field in required_fields:
                if field not in analysis:
                    raise Exception(f"DeepSeek API returned missing field: {field}")

            return analysis

        except requests.exceptions.Timeout:
            raise
        except Exception as e:
            raise

    def extract_json_from_markdown(self, text):
        """Extract JSON from Markdown text"""
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
        """Generate 3D model prompt based on analysis results"""
        symbols = ", ".join(analysis["symbols"])
        emotions = ", ".join(analysis["emotions"])
        model_prompt = f"{analysis['visual_description']} featuring {symbols}. Overall atmosphere: {emotions}"
        return model_prompt

    def generate_3d_model(self, model_prompt):
        """Generate 3D model using Tripo API"""
        if not self.tripo_api_key:
             raise Exception("Tripo API Key not configured")

        try:
            # Create task
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

            # Poll task status
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
        Process dream and generate 3D model
        update_progress_callback: function(dream_id, stage, progress, remaining_minutes, status)
        """
        try:
            if self.app:
                self.app.logger.info(f'Starting dream processing for user {user_id}')
            
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "Start", 5, 20, "Starting dream processing...")
            
            if not self.test_deepseek_api():
                if self.app:
                    self.app.logger.error('DeepSeek API unavailable')
                if dream_id and update_progress_callback:
                    update_progress_callback(dream_id, "Failed", 0, 0, "API service temporarily unavailable, please try again later")
                raise Exception("DeepSeek API service temporarily unavailable")

            if self.app:
                self.app.logger.info('Extracting keywords and analysis')
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "Analyze Dream", 20, 15, "Extracting keywords and analyzing dream...")
            
            analysis = self.extract_keywords(dream_text)
            
            if self.app:
                self.app.logger.info('Generating 3D model')
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "Generate Model", 40, 10, "Generating 3D model...")
            
            model_prompt = self.generate_model_prompt(analysis)
            model_url = self.generate_3d_model(model_prompt)
            
            if not model_url:
                if self.app:
                    self.app.logger.error('3D model generation failed')
                if dream_id and update_progress_callback:
                    update_progress_callback(dream_id, "Failed", 0, 0, "3D model generation failed, please retry later")
                raise Exception("3D model generation failed")

            # Create user directory
            user_dir = os.path.join('static', 'models', f'user_{user_id}')
            os.makedirs(user_dir, exist_ok=True)
            
            if self.app:
                self.app.logger.info('Downloading model file')
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "Download Model", 60, 5, "Downloading generated model file...")
            
            model_filename = f"dream_{int(time.time())}.glb"
            model_path = os.path.join(user_dir, model_filename)
            
            response = requests.get(model_url, stream=True)
            if response.status_code != 200:
                if dream_id and update_progress_callback:
                    update_progress_callback(dream_id, "Failed", 0, 0, "Failed to download model file")
                raise Exception("Failed to download model file")
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            
            with open(model_path, 'wb') as f, tqdm(
                desc="Downloading Model",
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for data in response.iter_content(block_size):
                    size = f.write(data)
                    pbar.update(size)
            
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "Optimizing", 80, 3, "Optimizing model and processing resources...")
            
            relative_model_path = os.path.join('models', f'user_{user_id}', model_filename)
            
            result = {
                'model_path': relative_model_path,
                'keywords': json.dumps(analysis['keywords']),
                'symbols': json.dumps(analysis['symbols']),
                'emotions': json.dumps(analysis['emotions']),
                'visual_description': analysis['visual_description'],
                'interpretation': analysis['interpretation']
            }
            
            if self.app:
                self.app.logger.info(f'Dream processing complete, model path: {relative_model_path}')
            return result
            
        except Exception as e:
            if self.app:
                self.app.logger.error(f'Error processing dream: {str(e)}')
            if dream_id and update_progress_callback:
                update_progress_callback(dream_id, "Failed", 0, 0, f"Processing failed: {str(e)}")
            raise
