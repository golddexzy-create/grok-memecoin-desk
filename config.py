from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    live_trading: bool = Field(default=False, alias="LIVE_TRADING")
    private_key: Optional[str] = Field(default=None, alias="PRIVATE_KEY")
    solana_rpc_url: str = Field(
        default="https://api.mainnet-beta.solana.com", alias="SOLANA_RPC_URL"
    )

    min_liquidity_usd: float = Field(default=15000.0, alias="MIN_LIQUIDITY_USD")
    max_dev_holdings_pct: float = Field(default=10.0, alias="MAX_DEV_HOLDINGS_PCT")
    require_lp_locked: bool = Field(default=True, alias="REQUIRE_LP_LOCKED")
    min_lp_locked_pct: float = Field(default=80.0, alias="MIN_LP_LOCKED_PCT")

    paper_starting_balance: float = Field(default=64.0, alias="PAPER_STARTING_BALANCE")
    max_position_pct: float = Field(default=5.0, alias="MAX_POSITION_PCT")
    take_profit_pct: float = Field(default=40.0, alias="TAKE_PROFIT_PCT")
    stop_loss_pct: float = Field(default=25.0, alias="STOP_LOSS_PCT")

    poll_interval_seconds: int = Field(default=30, alias="POLL_INTERVAL_SECONDS")
    max_candidates_per_cycle: int = Field(default=15, alias="MAX_CANDIDATES_PER_CYCLE")

    rugcheck_api_key: Optional[str] = Field(default=None, alias="RUGCHECK_API_KEY")
    helius_api_key: Optional[str] = Field(default=None, alias="HELIUS_API_KEY")
    birdeye_api_key: Optional[str] = Field(default=None, alias="BIRDEYE_API_KEY")
    jupiter_api_key: Optional[str] = Field(default=None, alias="JUPITER_API_KEY")
    xai_api_key: Optional[str] = Field(default=None, alias="XAI_API_KEY")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
