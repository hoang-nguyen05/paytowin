from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.request
import urllib.error


def _post_json(url: str, payload: dict, timeout_seconds: float) -> dict | None:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def _get_json(url: str, timeout_seconds: float) -> dict | None:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def _discover_ollama_models(base: str, timeout_seconds: float) -> list[str]:
    tags_url = f"{base.rstrip('/')}/api/tags"
    obj = _get_json(tags_url, timeout_seconds=timeout_seconds)
    models = obj.get("models") or []
    names: list[str] = []
    for m in models:
        n = (m.get("name") or "").strip()
        if n:
            names.append(n)
    return names


def _http_ollama_chat(base: str, model: str, prompt: str, timeout_seconds: float) -> str | None:
    chat_url = f"{base.rstrip('/')}/api/chat"
    generate_url = f"{base.rstrip('/')}/api/generate"
    for _ in range(2):
        try:
            chat_payload = {
                "model": model,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
            }
            chat_obj = _post_json(chat_url, chat_payload, timeout_seconds=timeout_seconds)
            content = (chat_obj or {}).get("message", {}).get("content", "").strip()
            if content:
                return content
        except (TimeoutError, urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
            pass

        try:
            gen_payload = {"model": model, "prompt": prompt, "stream": False}
            gen_obj = _post_json(generate_url, gen_payload, timeout_seconds=timeout_seconds)
            content = (gen_obj or {}).get("response", "").strip()
            if content:
                return content
        except (TimeoutError, urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
            pass

        time.sleep(0.4)
    return None


def _cli_ollama_chat(model: str, prompt: str, timeout_seconds: float) -> str | None:
    try:
        # CLI fallback: useful when local HTTP endpoint is unavailable.
        res = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True,
            text=True,
            timeout=max(timeout_seconds, 30),
            check=False,
        )
        content = (res.stdout or "").strip()
        return content or None
    except (FileNotFoundError, subprocess.SubprocessError, OSError):
        return None


def ollama_chat(model: str, prompt: str, timeout_seconds: float = 20.0) -> str | None:
    """
    Trả về text nếu gọi được Ollama, None nếu lỗi/kết nối không có.
    ENV: OLLAMA_URL (default http://localhost:11434)
    """
    base = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
    base_candidates = [base]
    if "localhost" in base:
        base_candidates.append(base.replace("localhost", "127.0.0.1"))

    model_candidates = [model]
    env_model = (os.environ.get("OLLAMA_MODEL") or "").strip()
    if env_model and env_model not in model_candidates:
        model_candidates.append(env_model)

    for base_item in base_candidates:
        try:
            discovered = _discover_ollama_models(base_item, timeout_seconds=min(timeout_seconds, 8))
            for m in discovered:
                if m not in model_candidates:
                    model_candidates.append(m)
        except (TimeoutError, urllib.error.URLError, OSError, ValueError, json.JSONDecodeError):
            pass

        for model_item in model_candidates:
            content = _http_ollama_chat(base_item, model_item, prompt, timeout_seconds)
            if content:
                return content

    for model_item in model_candidates:
        content = _cli_ollama_chat(model_item, prompt, timeout_seconds=max(timeout_seconds, 45))
        if content:
            return content
    return None


def fallback_advice(summary: str) -> str:
    return (
        "Mình chưa nhận được phản hồi từ máy chủ AI. Bạn kiểm tra Ollama đã chạy chưa, sau đó hỏi lại để nhận tư vấn chi tiết.\n\n"
        f"Dữ liệu hiện tại:\n{summary}"
    )

