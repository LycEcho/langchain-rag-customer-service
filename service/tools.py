from langchain.tools import Tool
import json
from datetime import datetime, timedelta


class Tools:

    # 工具1：提取JSON数据（保留原逻辑，供代理使用）
    def extract_json_from_question(self,question):
        """从客户问题中提取关键信息并生成JSON"""
        current_date = "2025-03-03"
        rules = {
            "今天": current_date,
            "昨天": (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d"),
            "明天": (datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
            "订单": "order",
            "发货": "shipment",
            "购买": "purchase",
        }
        json_data = {}

        # 模糊匹配日期关键词
        date_keywords = ["今天", "昨天", "明天"]
        date_found = False
        for keyword in date_keywords:
            if keyword in question:
                if keyword in rules:  # 精确匹配已知规则
                    json_data["date"] = rules[keyword]
                    date_found = True
                else:  # 未知日期处理
                    json_data["error"] = f"未找到 {keyword} 的日期规则"
                break

        # 类型匹配保持原逻辑
        type_found = False
        for key in ["订单", "发货", "购买", "买", "包裹"]:  # 添加"包裹"关键词
            if key in question:
                json_data["type"] = rules.get(key, "shipment")  # 默认包裹相关查询为发货类型
                type_found = True
                break

        # 如果没有找到任何信息，添加提示
        if not date_found and not type_found:
            json_data["message"] = "未找到日期或类型信息，请提供更多细节"

        return json.dumps(json_data, ensure_ascii=False)

    # 工具2：网络搜索（模拟实现，实际中可调用真实API）
    def web_search(self,query):
        """通过网络搜索获取订单、发货或购买信息"""
        current_date = "2025-03-03"
        if "订单" in query and "2025" in query:
            return f"搜索结果：假设为ABC公司，{current_date}的订单包括：订单1（商品A，数量10），订单2（商品B，数量5）。"
        elif "发货" in query and "昨天" in query:
            yesterday = (datetime.strptime(current_date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
            return f"搜索结果：{yesterday}的发货情况：已发货3个包裹，分别是包裹A、包裹B和包裹C。"
        elif "购买" in query and "明天" in query:
            tomorrow = (datetime.strptime(current_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
            return f"搜索结果：{tomorrow}的购买计划：计划购买商品X（数量20）和商品Y（数量15）。"
        return "暂无相关信息，请提供更具体的问题或上下文。"

    # 工具3：X平台搜索（模拟实现，实际中可调用X API）
    def x_search(self,query):
        """搜索X平台上的相关帖子"""
        if "订单" in query:
            return "X帖子：用户@abc_company提到，2025年3月3日的订单包括商品A和商品B。"
        elif "发货" in query:
            return "X帖子：用户@logistics提到，昨天发货了3个包裹。"
        elif "购买" in query:
            return "X帖子：用户@buyer计划明天购买商品X和商品Y。"
        return "X上暂无相关信息。"

    def get(self):
        return [
            Tool(
                name="extract_json",
                func=self.extract_json_from_question,
                description="从用户问题中提取日期和类型信息，返回JSON格式。输入应为原始问题，输出示例：{'date':'2025-03-03','type':'order'}"
            ),
            Tool(
                name="web_search",
                func=self.web_search,
                description="从网络搜索订单、发货或购买信息。"
            ),
            Tool(
                name="x_search",
                func=self.x_search,
                description="这里可以找到用户讲了什么"
            )
        ]
