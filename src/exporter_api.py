#!/usr/bin/env python
import time
from config.config import load_config
from prometheus_client import start_http_server, REGISTRY
from modules.exporter import tbw_metric_exporter

if __name__ == "__main__":
    cfg = load_config()

    start_http_server(cfg.exporter_port, cfg.exporter_addr)
    REGISTRY.register(tbw_metric_exporter())

    while True:
        time.sleep(5)
