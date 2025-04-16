import os
import re
import time
from typing import Tuple

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken

from core.prompts import TRADING_EXPERT_SYSTEM_MESSAGE
from utils.model_utils import get_model_client
from utils.time_utils import calculate_elapsed_time
from utils.text_utils import remove_think_block


class TradingExpert(AssistantAgent):
    def __init__(
        self,
    ) -> None:
        super().__init__(
            name="TradingExpert",
            description="Trading Expert",
            model_client=get_model_client(os.getenv("TRADING_EXPERT_MODEL")),
            system_message=TRADING_EXPERT_SYSTEM_MESSAGE,
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

        signal, reasons = self.parse_signal_and_reasons(content)

        if signal == 1:
            reason = f"""
# Signal: 
    - Buy
# Reason: 
    {reasons}
"""
        elif signal == 0:
            reason = f"""
# Signal: 
    - Hold
# Reason: 
    {reasons}
"""
        elif signal == -1:
            reason = f"""
# Signal: 
    - Sell
# Reason: 
    {reasons}
"""
        else:
            raise ValueError(f"{content}에서 신호를 찾을 수 없습니다.")

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

    def parse_signal_and_reasons(self, content: str):
        """content에서 신호와 이유를 추출합니다.
        신호는 1, 0, -1 중 하나로 표현됩니다.
        이유는 '-'로 시작하는 문장으로 표현됩니다.

        Args:
            content (str): 신호와 이유가 포함된 문자열

        Returns:
            _type_: 신호(int), 이유(str)
        """
        # 1) 신호 추출
        signal_pattern = re.compile(r"^\s*(-1|0|1)\s*$", re.MULTILINE)
        signal_match = signal_pattern.search(content)
        if signal_match:
            signal = int(signal_match.group(1))
        else:
            # 신호가 없는 경우에 대한 예외 처리
            signal = None

        # 2) 모든 이유 추출
        reason_pattern = re.compile(r"^\s*-\s+(.*)", re.MULTILINE)
        reason_matches = reason_pattern.findall(content)

        # 리스트를 합치거나, 필요한 형태로 가공
        reasons = "\n    ".join(reason_matches)

        return signal, reasons
