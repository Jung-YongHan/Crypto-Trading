import os
from typing import Dict, Any

import pandas as pd


class RecordManager:
    def __init__(self, system_name: str):
        self.folder_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../data")
        )
        os.makedirs(self.folder_path, exist_ok=True)

        self.file_path = os.path.join(self.folder_path, f"{system_name}.csv")

        self.column_types = {
            "datetime": "datetime64[ns]",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
            "next_action": "Int64",  # 다음 틱의 종가에 대해 시가에 어떤 액션을 취할지 결정
            "current_cash": "float64",  # 현재 보유 현금
            "current_position": "float64",  # 현재 보유 수량(코인 단위)
            "price_analysis_report": "string",  # 가격 분석 리포트
            "trading_reason": "string",  # 매매 신호 생성 이유
            "response_time_analysis": "Float64",  # 분석 응답 시간
            "response_time_trade": "Float64",  # 투자 결정 응답 시간
        }

        # 👉 이미 파일이 존재하면 지우고 빈 데이터프레임으로 시작
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

        # 새 파일(혹은 방금 삭제한 파일) 기준으로 초기 데이터프레임 생성
        self.df = pd.DataFrame(
            {col: pd.Series(dtype=dtype) for col, dtype in self.column_types.items()}
        )
        self.save()

    def _cast_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """컬럼별 타입 강제 캐스팅"""
        for col, dtype in self.column_types.items():
            if dtype.startswith("datetime"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
            else:
                df[col] = pd.Series(df[col], dtype=dtype)
        return df

    def record_step(self, data: Dict[str, Any]):
        """기존 datetime 있으면 업데이트, 없으면 새로 추가"""
        dt = pd.to_datetime(data.get("datetime"))
        if dt is None:
            raise ValueError("datetime 값은 반드시 존재해야 합니다.")

        # datetime 기준으로 기존 행 있는지 확인
        existing_idx = self.df.index[self.df["datetime"] == dt]

        row = {}
        for col, dtype in self.column_types.items():
            val = data.get(col, None)
            try:
                if dtype.startswith("datetime") and val is not None:
                    row[col] = pd.to_datetime(val)
                else:
                    row[col] = pd.Series([val], dtype=dtype)[0]
            except Exception as e:
                raise ValueError(
                    f"[RecordManager] 컬럼 '{col}' 값 변환 실패: {val} → {dtype} / {e}"
                )

        import warnings

        warnings.filterwarnings("ignore")

        if not existing_idx.empty:
            # 이미 존재하면 해당 행 업데이트
            idx = existing_idx[0]
            for key, value in row.items():
                self.df.at[idx, key] = value
        else:
            # 존재하지 않으면 새 row 추가
            self.df = pd.concat([self.df, pd.DataFrame([row])], ignore_index=True)

        self.save()

    def save(self):
        self.df = self.df.sort_values(by="datetime")  # 기본은 ascending=True → 오름차순
        self.df.to_csv(self.file_path, index=False, encoding="utf-8")

    def get_dataframe(self) -> pd.DataFrame:
        return self.df


if __name__ == "__main__":
    recorder = RecordManager(system_name="hi")

    recorder.record_step(
        {
            "datetime": "2024-10-09T09:00:00",
            "open": 400000,
            "high": 410000,
            "low": 390000,
            "close": 405000,
            "volume": 1000,
            "next_action": 1,
            "current_cash": 1000000,
            "current_position": 0,
            "price_analysis_report": "단기적으로 상승 추세가 예상됩니다.",
            "trading_reason": "매수 신호 발생",
        }
    )

    recorder.record_step(
        {
            "datetime": "2024-10-09T09:00:00",
            "open": 425000,
            "high": 410000,
            "low": 390000,
            "close": 405000,
            "volume": 1000,
            "next_action": 1,
            "current_cash": 1000000,
            "current_position": 0,
            "price_analysis_report": "단기적으로 상승 추세가 예상됩니다.",
            "trading_reason": "매수 신호 발생",
        }
    )
