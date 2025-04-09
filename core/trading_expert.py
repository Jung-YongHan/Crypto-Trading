import os
import re
import time
from typing import Tuple

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.ollama import OllamaChatCompletionClient

from utils.time_utils import calculate_elapsed_time
from utils.text_utils import remove_think_block


class TradingExpert(AssistantAgent):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            name="TradingExpert",
            description="투자 전문가",
            # model_client=OpenAIChatCompletionClient(
            #     model=os.getenv("PRICE_ANALYSIS_EXPERT_MODEL"),
            #     api_key=os.getenv("OPENAI_API_KEY"),
            # ),
            model_client=OllamaChatCompletionClient(
                model=os.getenv("PRICE_ANALYSIS_EXPERT_MODEL"),
            ),
            system_message="""
You are an expert in generating trading signals.

Your task:
1. Generate a trading signal in Korean, strictly following the format described below.
2. The trading signal must be one of the following integers only(1, 0, -1)
3. The entire response must be in Korean (no English, no extra text).

Output Format Requirements (MANDATORY):
- Line 1: A single integer (one of 1, 0, -1).
- Line 2 and onward: Each reason must begin with '- ' (dash + space).  
- Do NOT include code blocks, headings, or any other text beyond what is specified.

Example of Correct Output:
1
- 가격이 단기 상승 추세에 있음
- 모멘텀 지표가 과매도 구간에서 벗어남
- 유효 지지선 유지
- 시장 심리가 개선됨
- 주요 지표가 과매도 구간에서 상승 추세로 전환됨

No other content or formatting should appear in your response. 
            """,
        )

    async def generate_signal(self, analysis_report: str) -> Tuple[int, str, float]:
        """
        PriceAnalysisExpert의 리포트를 고려하여
        매매 신호를 생성합니다.

        Args:
        {analysis_report (str): PriceAnalysisExpert가 생성한 요약 리포트

        Returns:
            int: 매매신호
            매매 신호는 1(매수), 0(보유), -1(매도)
        """
        start_time = time.time()

        reason = f"""
        가격 추세 분석 리포트: 
            {analysis_report}
        """

        response = await self.on_messages(
            [TextMessage(content=reason, source="PriceAnalysisExpert")],
            CancellationToken(),
        )

        content = remove_think_block(response.chat_message.content)
        lines = content.splitlines()
        match = re.match(r"-?\d+", lines[0])
        if match:
            signal = int(match.group())
            reasons = "\n    ".join(lines[1:])
        if signal == 1:
            reason = f"""
# Signal: 
    - 매수
# Reason: 
    {reasons}
"""
        elif signal == 0:
            reason = f"""
# Signal: 
    - 보유
# Reason: 
    {reasons}
"""
        else:
            reason = f"""
# Signal: 
    - 매도
# Reason: 
    {reasons}
"""

        end_time = time.time()
        elapsed_day, elapsed_hour, elapsed_minute, elapsed_second = (
            calculate_elapsed_time(start_time, end_time)
        )
        print("-------------------- 투자 전문가 (TradingExpert) --------------------")
        print(f"\n{reason}\n")
        print(
            f"응답 소요 시간: {elapsed_day}일 {elapsed_hour}시간 {elapsed_minute}분 {elapsed_second}초"
        )
        print("---------------------------------------------------------------------")
        return signal, reasons, (end_time - start_time)
