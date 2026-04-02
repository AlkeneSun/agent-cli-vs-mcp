import time
import json
import subprocess
import re
from typing import List, Dict, Any
from openai import OpenAI
import os
from amap_api import search_poi 

API_KEY = os.environ.get("LLM_API_KEY", "YOUR_LLM_API_KEY_HERE")
BASE_URL = "https://api-inference.modelscope.cn/v1"
MODEL = "MiniMax/MiniMax-M2.5"
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

def run_chat_mcp_mode(prompt: str, seed_messages: List[Dict]=None, force_error: str=""):
    messages = seed_messages.copy() if seed_messages else []
    messages.append({"role": "user", "content": prompt})
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_poi",
                "description": "搜索地点POI",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "string", "description": "要搜索的关键字"},
                        "city": {"type": "string", "description": "城市，如：北京"}
                    },
                    "required": ["keywords"]
                }
            }
        }
    ]

    start_time = time.time()
    total_tokens = 0
    turns = 0
    tool_invocations = []
    final_answer = ""

    while turns < 5:
        turns += 1
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                temperature=0.0
            )
            msg = response.choices[0].message
            total_tokens += response.usage.total_tokens
            
            # The ModelScope API / MiniMax response format sometimes requires msg copy to append
            msg_dict = {"role": msg.role, "content": msg.content or ""}
            
            if msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    } for tc in msg.tool_calls
                ]
                messages.append(msg_dict)
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    args = json.loads(tc.function.arguments)
                    tool_invocations.append(args)
                    
                    if force_error and turns == 1:
                        args['force_error'] = force_error
                    
                    if fn_name == "search_poi":
                        res = search_poi(args.get("keywords", ""), args.get("city", ""), force_error=args.get("force_error", ""))
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": fn_name,
                            "content": json.dumps(res, ensure_ascii=False)
                        })
            else:
                final_answer = msg.content
                break
        except Exception as e:
            final_answer = f"API Request Failed: {str(e)}"
            break

    end_time = time.time()
    return {
        "final_answer": final_answer,
        "latency": end_time - start_time,
        "total_tokens": total_tokens,
        "turns": turns,
        "tool_invocations": tool_invocations
    }

def run_chat_cli_mode(prompt: str, seed_messages: List[Dict]=None, force_error: str=""):
    cli_system = '''你是一个智能助理，可以通过命令行来调用外部工具来完成任务。
如果你需要搜索POI，你需要生成一个Bash命令行：
```bash
python cli_tool.py --keywords "搜索关键字" --city "城市名称"
```
你需要等待系统给你返回命令的执行结果后，再基于结果回答。请只在一轮中输出一次bash代码块。'''

    messages = [{"role": "system", "content": cli_system}]
    if seed_messages:
        messages.extend(seed_messages)
    messages.append({"role": "user", "content": prompt})

    start_time = time.time()
    total_tokens = 0
    turns = 0
    tool_invocations = []
    final_answer = ""

    while turns < 5:
        turns += 1
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.0
            )
            content = response.choices[0].message.content
            total_tokens += response.usage.total_tokens
            
            messages.append({"role": "assistant", "content": content})

            bash_match = re.search(r'```(?:bash|sh)\n(.*?)```', content, re.DOTALL)
            if bash_match:
                cmd = bash_match.group(1).strip()
                kw_match = re.search(r'--keywords\s+[\'"]?([^\'"]+)[\'"]?', cmd)
                city_match = re.search(r'--city\s+[\'"]?([^\'"]+)[\'"]?', cmd)
                invoc_args = {}
                if kw_match: invoc_args['keywords'] = kw_match.group(1).rstrip('\'"')  # strip trailing quotes inside match if any
                if city_match: invoc_args['city'] = city_match.group(1).rstrip('\'"')
                tool_invocations.append(invoc_args)

                if force_error and turns == 1:
                    cmd += f' --force_error "{force_error}"'
                
                try:
                    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15, cwd="/Users/aks/.gemini/antigravity/scratch/cli_mcp_research")
                    output = proc.stdout if proc.returncode == 0 else proc.stderr + proc.stdout
                except Exception as e:
                    output = str(e)
                
                messages.append({
                    "role": "user", 
                    "content": f"系统执行结果:\n{output}\n请根据结果结合问题继续回答。"
                })
            else:
                final_answer = content
                break
        except Exception as e:
            final_answer = f"API Request Failed: {str(e)}"
            break
            
    end_time = time.time()
    return {
        "final_answer": final_answer,
        "latency": end_time - start_time,
        "total_tokens": total_tokens,
        "turns": turns,
        "tool_invocations": tool_invocations
    }

def run_experiments():
    results = {}
    
    print("Running Experiment 1: Token & Latency")
    prompt1 = "帮我查一下北京的星巴克，列出前三个。"
    results["1_efficiency"] = {
        "mcp": run_chat_mcp_mode(prompt1),
        "cli": run_chat_cli_mode(prompt1)
    }
    
    print("Running Experiment 2: Hallucination")
    prompt2 = "帮我查一下帝都南站附近的咖啡馆"
    results["2_hallucination"] = {
        "mcp": run_chat_mcp_mode(prompt2),
        "cli": run_chat_cli_mode(prompt2)
    }
    
    print("Running Experiment 3: Error Recovery")
    prompt3 = "查询上海的苹果直营店"
    results["3_error_recovery"] = {
        "mcp": run_chat_mcp_mode(prompt3, force_error="签名校验失败或者关键字不合法，请重新核对参数"),
        "cli": run_chat_cli_mode(prompt3, force_error="签名校验失败或者关键字不合法，请重新核对参数")
    }
    
    print("Running Experiment 4: Context Pollution")
    mcp_history = [
        {"role": "user", "content": "查一下杭州的希尔顿酒店"},
        {"role": "assistant", "content": "", "tool_calls": [{"id":"tc_1", "type":"function", "function":{"name":"search_poi", "arguments":"{\"keywords\":\"希尔顿\", \"city\":\"杭州\"}"}}]},
        {"role": "tool", "tool_call_id": "tc_1", "name": "search_poi", "content": json.dumps({"data": [{"name": "杭州康莱德酒店(希尔顿集团)", "address": "新业路228号"}]})},
        {"role": "assistant", "content": "我为您找到了杭州康莱德酒店。地址是新业路228号。"},
        {"role": "user", "content": "那广州塔附近的日料呢"},
        {"role": "assistant", "content": "", "tool_calls": [{"id":"tc_2", "type":"function", "function":{"name":"search_poi", "arguments":"{\"keywords\":\"日料\", \"city\":\"广州\"}"}}]},
        {"role": "tool", "tool_call_id": "tc_2", "name": "search_poi", "content": json.dumps({"data": [{"name": "摩打食堂(广州塔店)", "address": "阅江西路222号"}]})},
        {"role": "assistant", "content": "我为您找到了摩打食堂，地址是阅江西路222号。"}
    ]
    cli_history = [
        {"role": "user", "content": "查一下杭州的希尔顿酒店"},
        {"role": "assistant", "content": "好的\n```bash\npython cli_tool.py --keywords '希尔顿' --city '杭州'\n```"},
        {"role": "user", "content": "系统执行结果:\n{\"status\": \"success\", \"data\": [{\"name\": \"杭州康莱德酒店(希尔顿集团)\", \"address\": \"新业路228号\"}]}\n请根据结果结合问题继续回答。"},
        {"role": "assistant", "content": "我为您找到了杭州康莱德酒店。"},
        {"role": "user", "content": "那广州塔附近的日料呢"},
        {"role": "assistant", "content": "好的\n```bash\npython cli_tool.py --keywords '日料' --city '广州'\n```"},
        {"role": "user", "content": "系统执行结果:\n{\"status\": \"success\", \"data\": [{\"name\": \"摩打食堂(广州塔店)\", \"address\": \"阅江西路222号\"}]}\n请根据结果结合问题继续回答。"},
        {"role": "assistant", "content": "我为您找到了摩打食堂(广州塔店)，地址是阅江西路222号。"},
    ]
    
    prompt4 = "刚才我们在杭州找到的那家酒店叫什么名字，地址在哪个路段？(考考你的记忆力)"
    results["4_context_pollution"] = {
        "mcp": run_chat_mcp_mode(prompt4, seed_messages=mcp_history),
        "cli": run_chat_cli_mode(prompt4, seed_messages=cli_history)
    }
    
    with open("raw_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Experiment completed! Results saved to raw_results.json")

if __name__ == "__main__":
    run_experiments()
