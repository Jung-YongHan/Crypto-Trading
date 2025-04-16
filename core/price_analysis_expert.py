import os
import time
from typing import List, Dict, Tuple

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.prompts import PRICE_ANALYSIS_EXPERT_SYSTEM_MESSAGE
from utils.model_utils import get_model_client
from utils.text_utils import remove_think_block
from utils.time_utils import calculate_elapsed_time


class PriceAnalysisExpert(AssistantAgent):
    def __init__(self) -> None:
        super().__init__(
            name="PriceAnalysisExpert",
            description="Crypto Price Analysis Expert",
            model_client=get_model_client(os.getenv("PRICE_ANALYSIS_EXPERT_MODEL")),
            system_message=PRICE_ANALYSIS_EXPERT_SYSTEM_MESSAGE,
        )

    async def analyze_trend(self, price_data: List[Dict]) -> Tuple[str, float]:
        """
        수집된 가격 데이터를 통해 단기적인 가격 추세를 분석 및 요약 리포트 반환.

        Args:
            price_data (List[Dict]): 수집된 가격 데이터

        Returns:
            str: 가격 추세에 대한 요약 리포트 (예: "단기적으로 상승 추세가 예상됩니다.")
        """
        start_time = time.time()

        content = f"""
        {price_data}
        """

        response = await self.on_messages(
            [TextMessage(content=content, source="DataCollector")],
            CancellationToken(),
        )

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
