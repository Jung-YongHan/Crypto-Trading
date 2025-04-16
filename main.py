from system.crypto_trading_system import (
    create_system,
)


app = create_system(
    system_name="full_market_with_gpt-4o-mini_v2",
    initial_cash=27630641.3872338,
    fee_rate=0.08,
    coin="KRW-BTC",
    start_date="2019-12-07 09:00:00",
    end_date="2025-04-11 09:00:00",
    candle_unit="1d",
    limit=30,
)
if __name__ == "__main__":
    app.run()
