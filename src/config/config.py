import re
from os import path
from dotenv import dotenv_values


class load_config:
    def __init__(self):
        cfg_path = path.join(path.abspath(path.dirname(__file__)), "config")
        config = dotenv_values(cfg_path)
        self._load_cfg(config)
        self._load_tbw_cfg(config.get("TBW_CFG_PATH"))

    def _load_tbw_cfg(self, tbw_cfg_path):
        tbw_config = dotenv_values(tbw_cfg_path)
        self.atomic = int(tbw_config.get("ATOMIC"))
        self.tbw_voter_share = float(tbw_config.get("VOTER_SHARE"))
        self.tbw_delegate_share = sum(
            [float(i) for i in re.split(":|,", tbw_config.get("KEEP"))[1::2]]
        )
        self.tbw_interval = int(tbw_config.get("INTERVAL"))
        self.delegate = tbw_config.get("DELEGATE")
        self.blacklist_addr = tbw_config.get("BLACKLIST_ADDR")

    def _load_cfg(self, config):
        self.exporter_addr = config.get("EXPORTER_ADDR")
        self.exporter_port = int(config.get("EXPORTER_PORT"))
        self.tbw_db_path = config.get("TBW_DB_PATH")
        self.core_api_port = int(config.get("CORE_API_PORT"))
        self.core_api_addr = config.get("CORE_API_ADDR")
        self.cg_token_id = config.get("COINGECKO_TOKEN_ID")
        self.cg_trading_pair = config.get("COINGECKO_TRADING_PAIR")
