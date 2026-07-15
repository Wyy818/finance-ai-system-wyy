import json
import os

import requests
import streamlit as st


class AIService:
    PROVIDERS = ["OpenAI", "Anthropic", "Gemini", "Ollama"]

    def __init__(self):
        self.provider = st.session_state.get("ai_provider", "OpenAI")
        self.api_key = st.session_state.get("ai_api_key", "")
        self.base_url = st.session_state.get("ai_base_url", "")

    def render_config(self):
        st.subheader("AI 服务配置")
        col1, col2 = st.columns(2)
        with col1:
            provider = st.selectbox("选择AI服务商", self.PROVIDERS, key="ai_provider")
        with col2:
            api_key = st.text_input("API Key", value=st.session_state.get("ai_api_key", ""), type="password", key="ai_api_key")

        if provider in ["OpenAI", "Gemini"]:
            base_url = st.text_input("API Base URL（留空使用默认）", value=st.session_state.get("ai_base_url", ""), key="ai_base_url")

    def chat(self, messages, model=None, temperature=0.7):
        if not self.api_key and self.provider != "Ollama":
            return None

        if self.provider == "OpenAI":
            return self._chat_openai(messages, model, temperature)
        elif self.provider == "Anthropic":
            return self._chat_anthropic(messages, model, temperature)
        elif self.provider == "Gemini":
            return self._chat_gemini(messages, model, temperature)
        else:
            return self._chat_ollama(messages, model, temperature)

    def _chat_openai(self, messages, model, temperature):
        url = self.base_url or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model or "gpt-4o-mini",
            "messages": messages,
            "temperature": temperature
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            st.error(f"OpenAI API调用失败：{str(e)}")
            return None

    def _chat_anthropic(self, messages, model, temperature):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        payload = {
            "model": model or "claude-3-haiku-20240307",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 4096
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["content"][0]["text"]
        except Exception as e:
            st.error(f"Anthropic API调用失败：{str(e)}")
            return None

    def _chat_gemini(self, messages, model, temperature):
        url = self.base_url or "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        url += f"?key={self.api_key}"

        content = ""
        for msg in messages:
            content += f"{msg['role']}: {msg['content']}\n"

        payload = {
            "contents": [{
                "parts": [{
                    "text": content
                }]
            }],
            "generationConfig": {
                "temperature": temperature
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            st.error(f"Gemini API调用失败：{str(e)}")
            return None

    def _chat_ollama(self, messages, model, temperature):
        try:
            import ollama
            response = ollama.chat(
                model=model or "qwen2.5",
                messages=messages,
                options={"temperature": temperature}
            )
            return response["message"]["content"]
        except ImportError:
            st.error("Ollama未安装，请配置其他AI服务商")
            return None
        except Exception as e:
            st.error(f"Ollama调用失败：{str(e)}")
            return None


def get_ai_service():
    return AIService()