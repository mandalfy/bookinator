import requests
import os
import subprocess
import re

def get_wsl_host_ip():
    try:
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if "nameserver" in line:
                    return line.split()[1]
    except:
        return None

def check_url(url):
    print(f"Testing {url}...")
    try:
        # Disable proxies
        session = requests.Session()
        session.trust_env = False
        resp = session.get(f"{url}/api/tags", timeout=2)
        print(f"  ✅ SUCCESS! Status: {resp.status_code}")
        return True
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return False

print("--- Ollama Connectivity Diagnostic ---")

candidates = [
    "http://127.0.0.1:11434",
    "http://localhost:11434",
    "http://host.docker.internal:11434"
]

wsl_ip = get_wsl_host_ip()
if wsl_ip:
    print(f"Detected WSL Host IP: {wsl_ip}")
    candidates.append(f"http://{wsl_ip}:11434")

success_url = None
for url in candidates:
    if check_url(url):
        success_url = url
        break

if success_url:
    print("\n🎉 FOUND OLLAMA!")
    print(f"Please update OLLAMA_BASE_URL = \"{success_url}\" in 'llm_engine.py'")
else:
    print("\n❌ Could not connect to Ollama on any common address.")
    print("Please ensure Ollama is running on Windows and accepting connections.")
    print("If using WSL, you might need to set OLLAMA_HOST=0.0.0.0 on Windows.")
