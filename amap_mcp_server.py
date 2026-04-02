"""
Mock MCP Server for protocol overhead measurement.
Simulates schema payloads at various scale factors to show the
"Protocol Tax" growth curve as more tools are onboarded.
"""
import json
import copy

# --- Base Tool Definitions (3 tools, matching amap_cli.py) ---
BASE_TOOLS = [
    {
        "name": "search_poi",
        "description": "搜索地点POI（兴趣点），支持关键字与城市过滤。返回名称、类型、地址与经纬度。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keywords": {"type": "string", "description": "要搜索的关键字，如：星巴克、医院"},
                "city": {"type": "string", "description": "城市名称，如：北京、上海"},
                "limit": {"type": "integer", "description": "返回结果数量上限", "default": 3}
            },
            "required": ["keywords"]
        }
    },
    {
        "name": "plan_route",
        "description": "规划驾驶或步行的多点路径，返回距离、时间和分段导航指令。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "起点坐标，格式: lng,lat"},
                "destination": {"type": "string", "description": "终点坐标，格式: lng,lat"},
                "strategy": {
                    "type": "string",
                    "enum": ["fastest", "shortest", "avoid_highway"],
                    "description": "路线偏好策略"
                }
            },
            "required": ["origin", "destination"]
        }
    },
    {
        "name": "get_static_map",
        "description": "获取静态地图切片图的URL，可用于嵌入文档或消息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "center": {"type": "string", "description": "地图中心坐标，格式: lng,lat"},
                "zoom": {"type": "integer", "description": "缩放级别 1-17", "default": 10},
                "size": {"type": "string", "description": "输出分辨率，格式: width*height", "default": "400*400"}
            },
            "required": ["center"]
        }
    }
]

# Extra realistic tool stubs for scale simulation
EXTRA_TOOL_TEMPLATES = [
    {"name": "geocode", "description": "将结构化地址转为经纬度坐标（地理编码）。"},
    {"name": "reverse_geocode", "description": "将经纬度坐标逆向转为结构化地址（逆地理编码）。"},
    {"name": "ip_locate", "description": "根据IP地址定位所在城市与区县。"},
    {"name": "weather_query", "description": "查询指定城市的实时天气与未来预报。"},
    {"name": "district_query", "description": "查询行政区划信息（省/市/区县层级）。"},
    {"name": "traffic_status", "description": "查询指定道路的实时路况态势。"},
    {"name": "bus_route", "description": "查询公交/地铁换乘方案。"},
    {"name": "walking_route", "description": "规划步行导航路线。"},
    {"name": "cycling_route", "description": "规划骑行导航路线。"},
    {"name": "around_poi", "description": "搜索指定坐标周边的POI（周边搜索）。"},
    {"name": "polygon_poi", "description": "在多边形区域内搜索POI。"},
    {"name": "poi_detail", "description": "查询单个POI的详细信息（评分、营业时间等）。"},
    {"name": "input_tips", "description": "输入提示（搜索建议/自动补全）。"},
    {"name": "coordinate_convert", "description": "坐标系转换（GPS/百度/MapBar -> 高德）。"},
    {"name": "static_map_marker", "description": "在静态地图上标注自定义Marker。"},
    {"name": "distance_matrix", "description": "批量计算多起点到多终点的距离矩阵。"},
    {"name": "geofence_create", "description": "创建地理围栏并注册触发回调。"},
    {"name": "geofence_status", "description": "查询设备是否在指定围栏内。"},
    {"name": "truck_route", "description": "规划货车专用导航路线（限高限重）。"},
    {"name": "future_route", "description": "基于预测路况规划未来出发的最优路线。"},
]

def _make_tool_stub(tmpl, idx):
    """Generate a realistic tool schema stub from a template."""
    return {
        "name": tmpl["name"],
        "description": tmpl["description"],
        "inputSchema": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": f"{tmpl['name']}的主要输入参数"},
                "param2": {"type": "string", "description": f"可选的辅助参数"},
            },
            "required": ["param1"]
        }
    }


class MockMCPServer:
    """
    Simulates an MCP Server that exposes all tools upfront via tools/list.
    Supports scale_factor to model real-world platforms with many endpoints.
    """

    def get_tools_list(self, tool_count: int = 3) -> dict:
        """
        Return the full MCP tools/list response payload.
        tool_count: how many tools to expose (3, 10, 20, etc.)
        """
        tools = list(BASE_TOOLS)  # start with real 3

        # pad with realistic stubs to reach desired count
        extras_needed = max(0, tool_count - len(tools))
        for i in range(extras_needed):
            tmpl = EXTRA_TOOL_TEMPLATES[i % len(EXTRA_TOOL_TEMPLATES)]
            tools.append(_make_tool_stub(tmpl, i))

        return {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": tools}
        }

    def get_openai_tools_format(self, tool_count: int = 3) -> list:
        """
        Return tools in the OpenAI function-calling format—this is what
        actually gets injected into the LLM system prompt by most clients.
        """
        mcp_tools = self.get_tools_list(tool_count)["result"]["tools"]
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["inputSchema"]
                }
            }
            for t in mcp_tools
        ]
