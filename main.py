from v1.system.crypto_trading_system import (
    create_system,
)


app = create_system(
    system_name="bull_market_with_cogito_2",
    initial_cash=10_000_000,
    fee_rate=0.08,
    coin="KRW-BTC",
    start_date="2020-10-01 09:00:00",
    end_date="2021-04-13 09:00:00",
    candle_unit="1d",
    limit=40,
)
if __name__ == "__main__":
    app.run()
