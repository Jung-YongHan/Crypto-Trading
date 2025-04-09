from typing import List


def calculate_sma(data: List[float], period: int) -> str:
    """
    Calculate the Simple Moving Average (SMA) of a given data series.
    """
    if period <= 0:
        raise ValueError("Period must be a positive integer.")

    sma = []
    for i in range(len(data)):
        if i < period - 1:
            sma.append(None)  # Not enough data to calculate SMA
        else:
            sma.append(sum(data[i - period + 1 : i + 1]) / period)

    return f"{sma}"
