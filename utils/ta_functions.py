import numpy as np
import talib


class TAITools:
    def __init__(self, agent):
        self._agent = agent

    def _data(self):
        return self._agent.data

    def calculate_moving_average(self, period: int, field: str) -> str:
        """
        Summary:
            Calculates the moving average for the specified period and field ("open", "high", "low", "close", "volume").
        Args:
            data: Must match the structure of the MAInput model.
            period (int): The period for moving average calculation.
            field (str): The field to calculate the moving average on. Must be one of "open", "high", "low", "close", "volume".
        Returns:
            str: A string containing the moving average result and a brief analysis.

        """
        # 대상 필드로부터 배열 추출
        values = np.array([item[field] for item in self._data()], dtype=np.float64)

        # 이동평균 계산 (SMA)
        ma = talib.SMA(values, timeperiod=period)

        # 최근 이동평균 값
        recent_ma = ma[-1]
        # 최근값
        recent_val = values[-1]

        # 결과 요약
        result = (
            f"[{field} Moving Average Analysis]\n"
            f"- Period: {period}\n"
            f"- Latest {field} Moving Average: {recent_ma:.2f}\n"
            f"- Latest {field}: {recent_val:.2f}\n"
            f"  (Difference from Moving Average: {recent_val - recent_ma:.2f})"
        )
        return result

    def calcualte_volatility_analysis(self, period: int) -> str:
        """
        Summary:
            Calculates volatility indicators (e.g., standard deviation, ATR) and provides a summary of recent volatility.
        Args:
            data (List[Dict]): A list of market data.
            period (int): The period for volatility analysis (e.g., 14).
        Returns:
            str: A string summarizing volatility using standard deviation, ATR, and other metrics.
        """
        highs = np.array([item["high"] for item in self._data()], dtype=np.float64)
        lows = np.array([item["low"] for item in self._data()], dtype=np.float64)
        closes = np.array([item["close"] for item in self._data()], dtype=np.float64)

        # 표준편차 (close 기준)
        std_dev = talib.STDDEV(closes, timeperiod=period, nbdev=1)
        recent_std = std_dev[-1]

        # ATR (Average True Range)
        atr = talib.ATR(highs, lows, closes, timeperiod=period)
        recent_atr = atr[-1]

        result = (
            f"[Volatility Analysis]\n"
            f"- Period: {period}\n"
            f"- Standard Deviation (based on close): {recent_std:.2f}\n"
            f"- ATR: {recent_atr:.2f}\n"
            f"The current price volatility appears to be relatively "
            f"{'high' if recent_std > np.mean(std_dev[-5:]) else 'low'} based on the above metrics."
        )
        return result

    def compare_high_low(self, lookback: int) -> str:
        """
        Summary:
            Analyzes the highest and lowest points within a recent specified range (lookback).
        Args:
            data (List[Dict]): A list of market data.
            lookback (int): The range of recent days or candles to analyze.
        Returns:
            str: A brief summary of the recent highest and lowest values.
        """
        # lookback만큼 최근 데이터
        recent_data = self._data()[-lookback:]
        highs = [item["high"] for item in recent_data]
        lows = [item["low"] for item in recent_data]
        closes = [item["close"] for item in recent_data]

        highest_price = max(highs)
        lowest_price = min(lows)
        current_close = closes[-1]

        result = (
            f"[High/Low Comparison]\n"
            f"- Highest price in the last {lookback} candles (or days): {highest_price:.2f}\n"
            f"- Lowest price in the last {lookback} candles (or days): {lowest_price:.2f}\n"
            f"- Current closing price: {current_close:.2f}\n"
            f"  (Difference from high: {highest_price - current_close:.2f}, "
            f"Difference from low: {current_close - lowest_price:.2f})"
        )
        return result

    def calculate_rsi(self, period: int) -> str:
        """
        Summary:
            Calculates the RSI (Relative Strength Index) for the specified period using the closing prices and provides a brief summary.
        Args:
            data (List[Dict]): A list of market data.
                Example:
                    {
                        "date": str,
                        "open": float,
                        "high": float,
                        "low": float,
                        "close": float,
                        "volume": float
                    }
            period (int, optional): The period for RSI calculation (default is 14).
        Returns:
            str: A string containing the latest RSI value and an indication of whether the market is overbought or oversold.
        """
        closes = np.array([item["close"] for item in self._data()], dtype=np.float64)

        # RSI 계산
        rsi_values = talib.RSI(closes, timeperiod=period)
        recent_rsi = rsi_values[-1]

        # 간단한 해석
        if recent_rsi > 70:
            rsi_trend = "Overbought"
        elif recent_rsi < 30:
            rsi_trend = "Oversold"
        else:
            rsi_trend = "Neutral"
        # Result summary
        result = (
            f"[RSI Indicator Analysis]\n"
            f"- RSI({period}): {recent_rsi:.2f} ({rsi_trend} zone)\n"
        )
        return result

    def calculate_macd(
        self, fastperiod: int, slowperiod: int, signalperiod: int
    ) -> str:
        """
        Summary:
            Calculates the MACD, signal line, and histogram using the specified MACD parameters
            (fastperiod, slowperiod, signalperiod) based on closing prices and provides a summary.
        Args:
            data (List[Dict]): A list of market data.
                Example:
                    {
                        "date": str,
                        "open": float,
                        "high": float,
                        "low": float,
                        "close": float,
                        "volume": float
                    }
            fastperiod (int, optional): The period for the fast EMA (default is 12).
            slowperiod (int, optional): The period for the slow EMA (default is 26).
            signalperiod (int, optional): The period for the signal line (default is 9).
        Returns:
            str: A string summarizing the latest MACD, signal line, histogram values,
                and a brief directional analysis.
        """
        closes = np.array([item["close"] for item in self._data()], dtype=np.float64)

        # MACD 계산
        macd, macd_signal, macd_hist = talib.MACD(
            closes,
            fastperiod=fastperiod,
            slowperiod=slowperiod,
            signalperiod=signalperiod,
        )
        recent_macd = macd[-1]
        recent_signal = macd_signal[-1]
        recent_hist = macd_hist[-1]

        # 간단 방향성 해석
        direction = "상방" if recent_macd > recent_signal else "하방"

        # 결과 요약
        result = (
            f"[MACD Indicator Analysis]\n"
            f"- MACD({fastperiod}, {slowperiod}, {signalperiod})\n"
            f"- MACD: {recent_macd:.2f}, Signal: {recent_signal:.2f}, Hist: {recent_hist:.2f}\n"
            f"  (The MACD is positioned {'above' if direction == '상방' else 'below'} the signal line)\n"
        )
        return result

    def calculate_bollinger_bands(self, period: int, nbdevup: int, nbdevdn: int) -> str:
        """
        Summary:
            Calculates the Bollinger Bands using the specified parameters (period, nbdevup, nbdevdn)
            based on closing prices and provides a summary.
        Args:
            data (List[Dict]): A list of market data.
                Example:
                    {
                        "date": str,
                        "open": float,
                        "high": float,
                        "low": float,
                        "close": float,
                        "volume": float
                    }
            period (int): The period for Bollinger Bands calculation.
            nbdevup (int): The number of standard deviations for the upper band.
            nbdevdn (int): The number of standard deviations for the lower band.
        Returns:
            str: A string summarizing the latest Bollinger Bands values and a brief analysis.
        """
        closes = np.array([item["close"] for item in self._data()], dtype=np.float64)

        # 볼린저 밴드 계산
        upperband, middleband, lowerband = talib.BBANDS(
            closes,
            timeperiod=period,
            nbdevup=nbdevup,
            nbdevdn=nbdevdn,
        )
        recent_upper = upperband[-1]
        recent_middle = middleband[-1]
        recent_lower = lowerband[-1]

        # 최근 종가
        recent_close = closes[-1]

        # 결과 요약
        result = (
            f"[Bollinger Bands Analysis]\n"
            f"- Period: {period}, Upper Band Std Dev: {nbdevup}, Lower Band Std Dev: {nbdevdn}\n"
            f"- Latest Upper Band: {recent_upper:.2f}\n"
            f"- Latest Middle Band: {recent_middle:.2f}\n"
            f"- Latest Lower Band: {recent_lower:.2f}\n"
            f"- Latest Close Price: {recent_close:.2f}\n"
            f"  (Difference from Upper Band: {recent_close - recent_upper:.2f}, "
            f"Difference from Lower Band: {recent_close - recent_lower:.2f})"
        )
        return result
