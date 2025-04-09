import os
import time
from typing import List, Dict, Tuple

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_core.tools import FunctionTool
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient

from utils.ta_functions import calculate_sma
from utils.text_utils import remove_think_block
from utils.time_utils import calculate_elapsed_time


class PriceAnalysisExpert(AssistantAgent):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            name="PriceAnalysisExpert",
            description="암호화폐 가격 데이터 분석 전문가",
            # model_client=OpenAIChatCompletionClient(
            #     model=os.getenv("PRICE_ANALYSIS_EXPERT_MODEL"),
            #     api_key=os.getenv("OPENAI_API_KEY"),
            # ),
            model_client=OllamaChatCompletionClient(
                model=os.getenv("PRICE_ANALYSIS_EXPERT_MODEL"),
            ),
            # tools=[FunctionTool(calculate_sma, description="단순 이동 평균(SMA) 계산")],
            system_message="""
You are an expert in cryptocurrency price data analysis.
All of your responses must be in Korean.

Your goals:
1) Provide a concise analysis report on the short-term price trend.
2) Do NOT list individual price data (e.g., open, close, high, low, volume).
3) Incorporate only the essential results or numeric indicators (no raw data listing).

Mandatory Output Format:
- Line 1: A short sentence (max 20 words) summarizing the short-term trend.
- Line 2 and onward: 2 to 4 bullet points, each starting with "- " (dash + space), explaining key observations or reasoning.

Example:
- 단기적으로 완만한 상승 추세가 이어질 가능성이 큽니다.
- 이동 평균이 일정 기간 동안 상승 곡선을 유지하고 있음
- 최근 거래량이 이전 대비 꾸준히 증가하는 모습
- 시장 심리 지표가 개선세를 보이며 매수세가 유입됨

Important Notes:
- Do NOT include extra text, disclaimers, or raw data.
- Do NOT provide date-by-date or candle-by-candle breakdown.

You must not deviate from this format or these rules.
            """,
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
