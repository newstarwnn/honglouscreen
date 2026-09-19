"""红楼梦数据可视化 Flask 后端入口。

后端职责：
1. 读取并解析《红楼梦》txt 原文。
2. 调用 data 目录下的数据处理模块生成 JSON 数据。
3. 提供 RESTful 风格数据接口给 Vue 前端跨域调用。

本文件不渲染任何 HTML 页面，不编写任何前端样式代码，保证前后端完全解耦。
"""

from __future__ import annotations

from typing import Any, Callable

from flask import Flask, Response, jsonify

from config import API_PREFIX
from data.basicData import build_basic_data
from data.character_frequency import get_top_character_frequency
from data.character_info import build_character_info_data
from data.chapter_count import build_chapter_count_data
from data.chapter_word import build_chapter_wordcloud_data, build_total_wordcloud_data
from data.emotion_score import build_emotion_trend_data


def create_success_response(data: Any, message: str = "ok"):
    """封装统一成功响应结构。"""
    return jsonify({"code": 0, "message": message, "data": data})


def create_error_response(message: str, status_code: int = 500):
    """封装统一错误响应结构。"""
    return jsonify({"code": status_code, "message": message, "data": None}), status_code


def safe_json_route(loader: Callable[[], Any]):
    """统一执行数据处理函数，保证接口异常时也返回标准 JSON。"""
    try:
        return create_success_response(loader())
    except Exception as exc:  # noqa: BLE001 - 接口层需要统一兜底返回 JSON
        return create_error_response(f"数据处理失败：{exc}")


def build_dashboard_data() -> dict[str, Any]:
    """聚合中心大屏首屏数据，避免慢词云计算阻塞整页渲染。"""
    character_info = build_character_info_data()
    return {
        "overview": build_basic_data(),
        "characters": character_info["characters"],
        "frequency": get_top_character_frequency(limit=12),
        "relations": character_info["relations"],
        "wordcloud": [],
        "chapters": build_chapter_count_data(),
        "emotion": build_emotion_trend_data(),
    }


def create_app() -> Flask:
    """创建 Flask 应用并注册全部后端数据接口。"""
    app = Flask(
        __name__,
        static_folder="static",
        static_url_path="/static",
    )
    app.config["JSON_AS_ASCII"] = False
    app.json.ensure_ascii = False

    @app.after_request
    def add_cors_headers(response):
        """配置跨域响应头，支持 Vue 前端通过 HTTP 请求访问后端 JSON API。"""
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        if response.mimetype == "application/json":
            response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    @app.get("/")
    def service_index():
        """后端服务说明接口，只返回 JSON，不参与页面渲染。"""
        return create_success_response(
            {
                "service": "honglou-api",
                "apiPrefix": API_PREFIX,
                "responseType": "json",
                "frontendRender": False,
                "backendUrl": "http://127.0.0.1:5000",
                "frontendUrl": "http://127.0.0.1:5173",
                "openHint": "当前地址是 Flask 后端接口服务；请另开终端启动 Vue 前端后访问 frontendUrl。",
                "apiExamples": [
                    f"{API_PREFIX}/health",
                    f"{API_PREFIX}/basic-data",
                    f"{API_PREFIX}/characters",
                    f"{API_PREFIX}/characters/graph",
                ],
            },
            "红楼梦数据可视化后端服务已启动",
        )

    @app.get("/favicon.ico")
    def favicon():
        """浏览器默认图标请求兜底，避免开发日志出现无意义 404。"""
        return Response(status=204)

    @app.get(f"{API_PREFIX}/health")
    def health_check():
        """健康检查接口。"""
        return create_success_response({"service": "honglou-api", "status": "running"})

    @app.get(f"{API_PREFIX}/dashboard")
    def get_dashboard_data():
        """中心数据大屏聚合接口：一次返回首屏所有图表所需 JSON 数据。"""
        return safe_json_route(build_dashboard_data)

    @app.get(f"{API_PREFIX}/basic-data")
    def get_basic_data():
        """基础数据接口：章节数、总字数、人物数量等概览数据。"""
        return safe_json_route(build_basic_data)

    @app.get(f"{API_PREFIX}/characters")
    def get_character_info():
        """人物信息接口：15 位核心人物简介、出场统计和关系数据。"""
        return safe_json_route(lambda: build_character_info_data()["characters"])

    @app.get(f"{API_PREFIX}/characters/frequency")
    def get_character_frequency():
        """人物出场频率接口：返回出场次数 TOP12 人物数据。"""
        return safe_json_route(lambda: get_top_character_frequency(limit=12))

    @app.get(f"{API_PREFIX}/chapters/wordcloud")
    def get_chapter_wordcloud():
        """章节词云接口：返回全书词云和分章节词云数据。"""
        return safe_json_route(build_chapter_wordcloud_data)

    @app.get(f"{API_PREFIX}/chapters/wordcloud-total")
    def get_total_wordcloud():
        """中心大屏轻量词云接口：只返回全书 TOP 关键词，避免阻塞首屏。"""
        return safe_json_route(lambda: build_total_wordcloud_data(total_limit=90))

    @app.get(f"{API_PREFIX}/chapters/count")
    def get_chapter_count():
        """章节字数接口：返回每章字数与散点图数据源。"""
        return safe_json_route(build_chapter_count_data)

    @app.get(f"{API_PREFIX}/chapters/emotion")
    def get_emotion_data():
        """情感数据接口：返回每章悲伤、喜悦和综合情绪走势数据。"""
        return safe_json_route(build_emotion_trend_data)

    @app.get(f"{API_PREFIX}/characters/graph")
    def get_character_graph():
        """人物关系图谱接口：返回 ECharts 力导向图所需节点和边数据。"""
        return safe_json_route(lambda: build_character_info_data()["relations"])

    # 兼容早期前端请求路径，仍统一由 app.py 返回 JSON 数据。
    app.add_url_rule(f"{API_PREFIX}/overview", "overview_alias", get_basic_data, methods=["GET"])
    app.add_url_rule(f"{API_PREFIX}/characters/relations", "relations_alias", get_character_graph, methods=["GET"])
    app.add_url_rule(f"{API_PREFIX}/wordcloud", "wordcloud_alias", get_chapter_wordcloud, methods=["GET"])
    app.add_url_rule(f"{API_PREFIX}/emotion", "emotion_alias", get_emotion_data, methods=["GET"])
    app.add_url_rule(f"{API_PREFIX}/chapters", "chapters_alias", get_chapter_count, methods=["GET"])

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
