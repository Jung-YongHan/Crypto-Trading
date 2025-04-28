import os
import time
from typing import List, Dict, Tuple

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken, FunctionCall
from autogen_core.tools import FunctionTool
from autogen_agentchat.messages import ToolCallRequestEvent, ToolCallExecutionEvent

from core.prompts import (
    PRICE_ANALYSIS_EXPERT_SYSTEM_MESSAGE,
)
from utils.model_utils import get_model_client
from utils.ta_functions import TAITools
from utils.text_utils import remove_think_block
from utils.time_utils import calculate_elapsed_time


class PriceAnalysisExpert(AssistantAgent):
    def __init__(self, limit: int) -> None:
        self.data = []
        self.tai_tools = TAITools(self)

        super().__init__(
            name="PriceAnalysisExpert",
            description="Crypto Price Analysis Expert",
            model_client=get_model_client(os.getenv("PRICE_ANALYSIS_EXPERT_MODEL")),
            tools=[
                FunctionTool(
                    func=self.tai_tools.calculate_moving_average,
                    description="Calculate moving average. Usage: calculate_moving_average(5, 'close')",
                ),
                FunctionTool(
                    func=self.tai_tools.calcualte_volatility_analysis,
                    description="Calculate volatility analysis. Usage: calcualte_volatility_analysis(14)",
                ),
                FunctionTool(
                    func=self.tai_tools.compare_high_low,
                    description="Calculate high and low price. Usage: compare_high_low(14)",
                ),
                FunctionTool(
                    func=self.tai_tools.calculate_rsi,
                    description="Calculate RSI. Usage: calculate_rsi(14)",
                ),
                FunctionTool(
                    func=self.tai_tools.calculate_macd,
                    description="Calculate MACD. Usage: calculate_macd(12, 26, 9)",
                ),
            ],
            system_message=PRICE_ANALYSIS_EXPERT_SYSTEM_MESSAGE,
        )
        self.limit = limit

    async def analyze_trend(
        self, price_data: List[Dict], current_info: Dict
    ) -> Tuple[str, float]:
        """
        수집된 가격 데이터를 통해 단기적인 가격 추세를 분석 및 요약 리포트 반환.

        Args:
            price_data (List[Dict]): 수집된 가격 데이터

        Returns:
            str: 가격 추세에 대한 요약 리포트 (예: "단기적으로 상승 추세가 예상됩니다.")
        """
        start_time = time.time()

        content = f"""
Portfolio Status:        
- current_cash : {current_info["current_cash"]}
- current_position(coin) : {current_info["current_position"]}
        """
        self.data = price_data
        response = await self.on_messages(
            [TextMessage(content=content, source="DataCollector")],
            CancellationToken(),
        )

        print("=== Tool Usage History ===")
        for idx, msg in enumerate(response.inner_messages):
            print(f"[Step {idx+1}] {msg.__class__.__name__}:")
            print(f" - Source: {msg.source}")
            if isinstance(msg, ToolCallRequestEvent):
                for content in msg.content:
                    if isinstance(content, FunctionCall):
                        print(f" - Function: {content.name}")
                        print(f" - Arguments: {content.arguments}")
                    else:
                        print(f" what content? {content}")
            elif isinstance(msg, ToolCallExecutionEvent):
                print(f" - Result: {msg.content[:200]}...")  # 처음 200자만 출력
            print("-" * 50)

        analysis_report = remove_think_block(response.chat_message.content)

        end_time = time.time()
        elapsed_day, elapsed_hour, elapsed_minute, elapsed_second = (
            calculate_elapsed_time(start_time, end_time)
        )
        print("-------------- 가격 분석 전문가 (PriceAnalysisExpert) ---------------")
        print(f"\n{analysis_report}\n")
        print(
            f"응답 소요 시간: {elapsed_day}일 {elapsed_hour}시간 {elapsed_minute}분 {elapsed_second}초"
        )
        print("---------------------------------------------------------------------")
        return analysis_report, (end_time - start_time)
