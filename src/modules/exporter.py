from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from config.config import load_config
from client import ArkClient
from modules.sql import tbwdb
import os


class tbw_metric_exporter(object):
    def __init__(self):
        self.cfg = load_config()

        self.dposlib = ArkClient(
            "http://{0}:{1}/api".format(self.cfg.core_api_addr, self.cfg.core_api_port)
        )

        self.collect()

    def collect(self):
        if os.path.isfile(self.cfg.tbw_db_path):
            self.tbwdb = tbwdb(self.cfg.tbw_db_path)

        yield (self._collect_config())
        yield (self._collect_payout())
        yield (self._collect_blockchain())
        yield (self._collect_delegate())
        yield (self._collect_network())

    def _collect_config(self):
        g = GaugeMetricFamily("tbw_config", "Tbw config parameters", labels=["param"])

        g.add_metric(["atomic"], self.cfg.atomic)
        g.add_metric(["payout_interval_block"], self.cfg.tbw_interval)
        g.add_metric(["payout_voter_share"], self.cfg.tbw_voter_share)
        g.add_metric(["payout_delegate_share"], self.cfg.tbw_delegate_share)

        return g

    def _collect_payout(self):
        g = GaugeMetricFamily(
            "tbw_payout", "Current Tbw payout data", labels=["payout"]
        )

        try:
            g.add_metric(
                ["pending_voters_payout"],
                (
                    lambda: 0,
                    lambda: self.tbwdb.pending_voters_payout().fetchall()[0][0],
                )[len(self.tbwdb.pending_voters_payout().fetchall())](),
            )
            g.add_metric(
                ["pending_delegate_payout"],
                (
                    lambda: 0,
                    lambda: self.tbwdb.pending_delegate_payout().fetchall()[0][0],
                )[len(self.tbwdb.pending_delegate_payout().fetchall())](),
            )
            g.add_metric(
                ["block_before_payout"],
                self.cfg.tbw_interval
                - len(self.tbwdb.blocks().fetchall()) % self.cfg.tbw_interval,
            )
            g.add_metric(
                ["total_delegate_rewards"],
                (
                    lambda: 0,
                    lambda: self.tbwdb.delegate_total_rewards().fetchall()[0][0],
                )[
                    len(self.tbwdb.delegate_total_rewards().fetchall())
                    and self.tbwdb.delegate_total_rewards().fetchall()[0][0] != None
                ](),
            )
            g.add_metric(
                ["total_voters_rewards"],
                (lambda: 0, lambda: self.tbwdb.voters_total_rewards().fetchall()[0][0])[
                    len(self.tbwdb.voters_total_rewards().fetchall())
                    and self.tbwdb.voters_total_rewards().fetchall()[0][0] != None
                ](),
            )
        except:
            pass

        return g

    def _collect_blockchain(self):
        g = GaugeMetricFamily(
            "tbw_blockchain", "Current Tbw blockchain data", labels=["blockchain"]
        )

        self.active_delegates = self.dposlib.node.configuration()["data"]["constants"][
            "activeDelegates"
        ]
        g.add_metric(["height"], self.dposlib.blocks.last()["data"]["height"])
        g.add_metric(
            ["active_delegates"],
            self.active_delegates,
        )
        g.add_metric(
            ["d_cur_round"],
            self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"]["blocks"][
                "last"
            ]["height"]
            // self.active_delegates,
        )
        g.add_metric(
            ["b_cur_round"],
            self.dposlib.blocks.last()["data"]["height"] // self.active_delegates,
        )
        try:
            g.add_metric(
                ["t_cur_round"],
                (
                    lambda: 0,
                    lambda: self.tbwdb.last_block_heigh().fetchall()[0][0]
                    // self.active_delegates,
                )[len(self.tbwdb.last_block_heigh().fetchall())](),
            )
        except:
            pass

        return g

    def _collect_delegate(self):
        g = GaugeMetricFamily(
            "tbw_delegate", "Current Tbw delegate data", labels=["delegate"]
        )

        g.add_metric(
            ["delegate_voters_number"],
            len(self.dposlib.delegates.voters(delegate_id=self.cfg.delegate)["data"]),
        )
        g.add_metric(
            ["delegate_rank"],
            self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"]["rank"],
        )
        g.add_metric(
            ["delegate_forged_token"],
            self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"]["forged"][
                "total"
            ],
        )
        g.add_metric(
            ["delegate_forged_block"],
            self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"]["blocks"][
                "produced"
            ],
        )
        g.add_metric(
            ["delegate_last_t_forged"],
            self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"]["blocks"][
                "last"
            ]["timestamp"]["unix"],
        )

        return g

    def _collect_network(self):
        g = GaugeMetricFamily(
            "tbw_network", "Current Tbw network data", labels=["network"]
        )

        g.add_metric(["peers_number"], self.dposlib.peers.all()["meta"]["count"])

        return g
