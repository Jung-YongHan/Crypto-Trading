from multi_agent_system.trading_system.system.crypto_trading_system import (
    create_system,
)

app = create_system(
    system_name="test",
    initial_cash=10_000_000,
    fee_rate=0.08,
    coin="KRW-BTC",
    start_date="2024-09-01 09:00:00",
    end_date="2024-09-02 09:00:00",
    candle_unit="1d",
)

if __name__ == "__main__":
    app.run()
