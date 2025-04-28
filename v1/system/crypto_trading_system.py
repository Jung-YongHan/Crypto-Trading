import asyncio
import time
from datetime import datetime, timedelta
from typing import Tuple

from autogen_core import CancellationToken
from dotenv import load_dotenv

from v1.core.constants import (
    TIME_DELTA_MAP,
    DEFAULT_UNIT,
)
from v1.core.data_analyzer import DataAnalyzer
from v1.core.data_collector import DataCollector
from v1.core.portfolio_manager import (
    PortfolioManager,
)
from v1.core.price_analysis_expert import (
    PriceAnalysisExpert,
)
from v1.core.trading_expert import TradingExpert
from v1.system.record_manager import RecordManager
from v1.utils.time_utils import calculate_elapsed_time


class CryptoTradingSystem:
    def __init__(
        self,
        system_name: str,
        initial_cash: float,
        fee_rate: float,
        coin: str,
        start_date: str,
        end_date: str,
        candle_unit: str,
        limit: int = 0,
    ):
        self.system_name = system_name
        self.initial_cash = initial_cash
        self.fee_rate = fee_rate
        self.coin = coin
        self.start_date = start_date
        self.end_date = end_date
        self.candle_unit = candle_unit
        self.limit = limit

        self.data_collector = DataCollector(limit=limit)
        self.price_analysis_expert = PriceAnalysisExpert(limit=limit)
        self.trading_expert = TradingExpert()
        self.portfolio_manager = PortfolioManager(
            initial_cash=initial_cash, fee_rate=fee_rate
        )
        self.record_manager = RecordManager(system_name=system_name)

        # 설정한 투자 기간 동안 동적으로 바뀔 변수들
        self.tmp_start_date = start_date
        self.tmp_end_date = end_date

    async def run(self):
        """
        전체 투자 프로세스를 순차적으로 실행

        1. 지정된 기간의 일부(예: 5%)만 우선 수집
        2. PriceAnalysisExpert로 가격 추세 리포트 생성
        3. 가격 추세 리포트 및 ReflectionExpert의 보고서를 참고하여 TradingExpert 매매 신호 생성
        4. 매매 실행 후 성찰 보고서를 갱신
        5. 반복 수행
        """
        print("######################### 투자 시스템 시작 ##########################")
        print("---------------------------------------------------------------------")
        print("시스템명:", self.system_name)
        print("투자 시작 캔들:", self.start_date)
        print("투자 종료 캔들:", self.end_date)
        print("투자 대상 코인:", self.coin)
        print("캔들 단위:", self.candle_unit)
        print("초기 현금:", self.portfolio_manager.current_cash)
        print("---------------------------------------------------------------------")
        start_time = time.time()

        # # 1) 첫 수행 시, 지정된 기간의 일부(예: 5%)만 우선 수집
        # self.tmp_end_date = await self._calculate_partial_end_date(
        #     start_date=self.start_date,
        #     end_date=self.end_date,
        #     portion=0.05,
        #     candle_unit=self.candle_unit,
        # )

        await self.collect_dummy_data()

        self.tmp_end_date = self.start_date

        while True:
            if self.tmp_end_date >= self.end_date:
                break

            data = await self.data_collector.collect_price_data(
                coin=self.coin,
                start_date=self.start_date,
                end_date=self.tmp_end_date,
                candle_unit=self.candle_unit,
            )

            current_info = {
                "current_cash": self.portfolio_manager.current_cash,
                "current_position": self.portfolio_manager.current_position,
            }

            # 2) 수집된 데이터 기반 가격 분석 리포트 생성
            analysis_report, analysis_time = (
                await self.price_analysis_expert.analyze_trend(
                    price_data=data, current_info=current_info
                )
            )
            await self.price_analysis_expert.on_reset(CancellationToken())

            analysis_report = await self.generate_report(
                analysis_report=analysis_report
            )

            # 3) 분석 리포트 기반 매매 신호를 생성
            signal, signal_reason, trade_time = (
                await self.trading_expert.generate_signal(
                    analysis_report=analysis_report
                )
            )
            await self.trading_expert.on_reset(CancellationToken())

            # 4) 다음 틱 데이터 수집
            self.tmp_start_date, self.tmp_end_date = await self.set_dates(
                self.tmp_end_date, self.candle_unit
            )
            price_data = await self.data_collector.collect_price_data(
                self.coin, self.tmp_start_date, self.tmp_end_date, self.candle_unit
            )

            current_cash = self.portfolio_manager.current_cash
            current_position = self.portfolio_manager.current_position

            # 5) 매매 실행
            if price_data:
                latest_open = price_data[-1]["open"]
                self.portfolio_manager.record_trade(
                    date=price_data[-1]["date"],
                    action=signal,
                    open_price=latest_open,
                )

            print(
                f"-------------- {self.tmp_end_date} 기준 포트폴리오 현황 -------------\n"
            )
            if signal == 1:
                print("Position: Buy")
            elif signal == 0:
                print("Position: Hold")
            else:
                print("Position: Sell")
            print(
                f"\nCash: {self.portfolio_manager.current_cash}, Amount of Coins: {self.portfolio_manager.current_position}"
            )
            print(
                "---------------------------------------------------------------------"
            )

            self.record_manager.record_step(
                {
                    "datetime": price_data[-2]["date"],
                    "open": price_data[-2]["open"],
                    "high": price_data[-2]["high"],
                    "low": price_data[-2]["low"],
                    "close": price_data[-2]["close"],
                    "volume": price_data[-2]["volume"],
                    "next_action": signal,
                    "current_cash": current_cash,
                    "current_position": current_position,
                    "price_analysis_report": analysis_report,
                    "trading_reason": signal_reason,
                    "response_time_analysis": analysis_time,
                    "response_time_trade": trade_time,
                }
            )

        if self.portfolio_manager.current_position > 0:
            # 전체 코인을 팔아서 현금화
            self.portfolio_manager.record_trade(
                date=self.tmp_end_date,
                action=-1,
                open_price=price_data[-1]["close"],
            )

        data_path = f"data/{self.system_name}.csv"
        performance_metrics = DataAnalyzer(data_path).performance_metrics()

        print("***멀티 에이전트 시스템 전략 성과 지표***")
        print(f"최종 수익률: {performance_metrics['return_pct']:.2f}%")
        print(f"최대 낙폭: {performance_metrics['mdd']:.2f}%")
        print(
            f"승률: {performance_metrics['win_rate']}% ({performance_metrics['total_trades']})"
        )
        print(f"샤프 지수: {performance_metrics['sharpe_index']:.2f}\n")
        await self.backtest_buy_and_hold()

        end_time = time.time()
        elapsed_day, elapsed_hour, elapsed_minute, elapsed_second = (
            calculate_elapsed_time(start_time, end_time)
        )
        print(
            f"총 소요 시간: {elapsed_day}일 {elapsed_hour}시간 {elapsed_minute}분 {elapsed_second}초"
        )

        self.record_manager.record_step(
            {
                "datetime": price_data[-1]["date"],
                "open": price_data[-1]["open"],
                "high": price_data[-1]["high"],
                "low": price_data[-1]["low"],
                "close": price_data[-1]["close"],
                "volume": price_data[-1]["volume"],
                "next_action": None,
                "current_cash": self.portfolio_manager.current_cash,
                "current_position": self.portfolio_manager.current_position,
                "price_analysis_report": None,
                "trading_reason": None,
                "response_time_analysis": None,
                "response_time_trade": None,
            }
        )

        print(
            f"######################## 투자 시스템 종료 ############################\n"
        )

    async def collect_dummy_data(self):
        """
        백테스팅 전 limit 기간만큼의 더미 데이터를 미리 수집합니다(기술 지표 분석을 위해).
        limit이 없다면 약 40개 데이터 수집(macd 계산을 위해)
        """
        fmt = "%Y-%m-%d %H:%M:%S"
        start_dt = datetime.strptime(self.start_date, fmt)
        limit = self.limit if self.limit > 0 else 40
        adjusted_start_dt_1 = start_dt - timedelta(days=limit - 1)
        adjusted_start_dt_2 = (start_dt - timedelta(days=1)).strftime(fmt)
        tmp_start_date = adjusted_start_dt_1.strftime(fmt)

        _ = await self.data_collector.collect_price_data(
            coin=self.coin,
            start_date=tmp_start_date,
            end_date=adjusted_start_dt_2,
            candle_unit=self.candle_unit,
        )

    async def generate_report(self, analysis_report: str) -> str:
        """
        포트폴리오 및 가격 분석 리포트에 기반한 최종 리포트를 생성합니다.

        Args:
            analysis_report (str): 가격 분석 리포트

        Returns:
            str: 생성된 리포트
        """
        report = f"""
# Current Portfolio:
- Cash: {self.portfolio_manager.current_cash}
- Amount of Coins: {self.portfolio_manager.current_position}

# Price Analysis Report:
{analysis_report}
        """
        return report

    async def _calculate_partial_end_date(
        self,
        start_date: str,
        end_date: str,
        portion: float,
        candle_unit: str,
    ) -> str:
        """
        시작일과 종료일을 바탕으로, candle 단위에 맞게 portion 비율만큼의 캔들을 포함하는 시점 계산, 문자열 반환

        Args:
            start_date (str): 시작 날짜 (예: "2024-10-01 09:00:00")
            end_date (str): 종료 날짜 (예: "2024-10-09 09:00:00")
            portion (float): 비율 (예: 0.05 -> 5%)
            candle_unit (str): 캔들 단위 (예: "1d", "1h", "15m", "5m", "1m")

        Returns:
            str: 부분 종료 날짜 (캔들 간격에 맞게 정렬됨)
        """
        fmt = "%Y-%m-%d %H:%M:%S"
        start_dt = datetime.strptime(start_date, fmt)
        end_dt = datetime.strptime(end_date, fmt)

        total_delta = end_dt - start_dt

        # candle 단위의 timedelta 생성 (TIME_DELTA_MAP 활용)
        candle_delta_args = TIME_DELTA_MAP.get(
            candle_unit, TIME_DELTA_MAP[DEFAULT_UNIT]
        )
        candle_interval = timedelta(**candle_delta_args)

        # 전체 캔들 수 (실수 값)
        total_candles = total_delta / candle_interval

        # portion에 해당하는 캔들 수 (정수로 내림)
        partial_candles = int(total_candles * portion)
        # 최소 1개의 캔들을 포함하도록 설정
        if partial_candles < 1:
            partial_candles = 1

        partial_end_dt = start_dt + candle_interval * partial_candles
        return partial_end_dt.strftime(fmt)

    async def set_dates(self, end_date: str, candle_unit: str) -> Tuple[str, str]:
        """
        시작일과 종료일을 설정합니다.

        Args:
            end_date (str): 종료 날짜
            candle_unit(str): 캔들 단위

        Returns:
            Tuple[str, str]: 시작일, 종료일
        """
        fmt = "%Y-%m-%d %H:%M:%S"

        start_dt = datetime.strptime(end_date, fmt)
        end_dt = datetime.strptime(end_date, fmt)

        delta_args = TIME_DELTA_MAP.get(candle_unit, TIME_DELTA_MAP[DEFAULT_UNIT])
        new_end_dt = end_dt + timedelta(**delta_args)
        return start_dt.strftime(fmt), new_end_dt.strftime(fmt)

    async def backtest_buy_and_hold(self):
        buy_amount = self.data_collector.total_collected_data[self.limit - 1]["open"]
        sell_amount = self.data_collector.total_collected_data[-1]["close"]
        # 수익률 계산
        profit = (sell_amount - buy_amount) / buy_amount * 100
        print(f"*Buy and Hold 전략 수익률: {profit:.2f}%")


class AsyncCryptoTradingSystem(CryptoTradingSystem):
    def __init__(
        self,
        system_name: str,
        initial_cash: float,
        fee_rate: float,
        coin: str,
        start_date: str,
        end_date: str,
        candle_unit: str,
        limit: int,
    ):
        super().__init__(
            system_name=system_name,
            initial_cash=initial_cash,
            fee_rate=fee_rate,
            coin=coin,
            start_date=start_date,
            end_date=end_date,
            candle_unit=candle_unit,
            limit=limit,
        )

    def run(self):
        asyncio.run(super().run())


def create_system(
    system_name: str,
    initial_cash: float,
    fee_rate: float,
    coin: str,
    start_date: str,
    end_date: str,
    candle_unit: str,
    limit: int = 0,
):
    load_dotenv()

    return AsyncCryptoTradingSystem(
        system_name=system_name,
        initial_cash=initial_cash,
        fee_rate=fee_rate,
        coin=coin,
        start_date=start_date,
        end_date=end_date,
        candle_unit=candle_unit,
        limit=limit,
    )
