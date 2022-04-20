from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
from pycoingecko import CoinGeckoAPI
from config.config import load_config
from client import ArkClient
from modules.sql import tbwdb
import os
import re


class tbw_metric_exporter(object):
    def __init__(self):
        self.cfg = load_config()

        try:
            self.dposlib = ArkClient(
                "http://{0}:{1}/api".format(
                    self.cfg.core_api_addr, self.cfg.core_api_port
                )
            )
        except Exception as m:
            self.dposlib = 0
            pass

        try:
            self.cg = CoinGeckoAPI()
            self.cg.ping()
        except:
            self.cg = 0
            pass

        self.collect()

    def collect(self):
        if os.path.isfile(self.cfg.tbw_db_path):
            self.tbwdb = tbwdb(self.cfg.tbw_db_path)

        yield (self._collect_config())
        yield (self._collect_payout())
        yield (self._collect_blockchain())
        yield (self._collect_delegate())
        yield (self._collect_voters())
        yield (self._collect_network())
        yield (self._collect_token())
        yield (self._collect_transactions())
        yield (self._collect_reward_calc())

    def _collect_config(self):
        g = GaugeMetricFamily("tbw_config", "Tbw config parameters", labels=["param"])

        g.add_metric(["atomic"], self.cfg.atomic)
        g.add_metric(["payout_interval_block"], self.cfg.tbw_interval)
        g.add_metric(["payout_voter_share"], self.cfg.tbw_voter_share)
        g.add_metric(["payout_delegate_share"], self.cfg.tbw_delegate_share)

        return g

    def _collect_payout(self):
        g = GaugeMetricFamily("tbw_payout", "Tbw payout data", labels=["payout"])

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
                ["staged_payout"],
                (lambda: 0, lambda: self.tbwdb.staged_payout().fetchall()[0][0],)[
                    len(self.tbwdb.staged_payout().fetchall())
                    and self.tbwdb.staged_payout().fetchall()[0][0] != None
                ](),
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
            g.add_metric(["error"], 1)
            return g

        return g

    def _collect_blockchain(self):
        g = GaugeMetricFamily(
            "tbw_blockchain", "Blockchain data", labels=["blockchain"]
        )

        try:
            self.active_delegates = self.dposlib.node.configuration()["data"][
                "constants"
            ]["activeDelegates"]
            g.add_metric(["height"], self.dposlib.blocks.last()["data"]["height"])
            g.add_metric(
                ["active_delegates"],
                self.active_delegates,
            )
            g.add_metric(
                ["d_cur_round"],
                self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"][
                    "blocks"
                ]["last"]["height"]
                // self.active_delegates,
            )
            g.add_metric(
                ["b_cur_round"],
                self.dposlib.blocks.last()["data"]["height"] // self.active_delegates,
            )
        except:
            g.add_metric(["error"], 1)
            pass

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
            g.add_metric(["error"], 1)
            pass

        return g

    def _collect_delegate(self):
        g = GaugeMetricFamily("tbw_delegate", "Tbw delegate data", labels=["delegate"])

        try:
            voters_list = self.dposlib.delegates.voters(delegate_id=self.cfg.delegate)[
                "data"
            ]
            rl_voters_list = []
            voters_balance = 0
            rl_voters_balance = 0
            for voter in voters_list:
                voters_balance += int(voter["balance"])
                if voter["address"] not in self.cfg.blacklist_addr.split(","):
                    rl_voters_list.append(voter)
                    rl_voters_balance += int(voter["balance"])
            g.add_metric(["voters_number"], len(rl_voters_list))
            g.add_metric(["voters_balance"], voters_balance)
            g.add_metric(["rl_voters_balance"], rl_voters_balance)
            rank = self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"][
                "rank"
            ]
            g.add_metric(["rank"], rank)
            try:
                g.add_metric(
                    ["block_reward"],
                    self.dposlib.node.configuration()["data"]["constants"][
                        "dynamicReward"
                    ]["ranks"][str(rank)],
                )
            except:
                g.add_metric(
                    ["block_reward"],
                    self.dposlib.node.configuration()["data"]["constants"]["reward"],
                )
            g.add_metric(
                ["forged_token"],
                self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"][
                    "forged"
                ]["total"],
            )
            g.add_metric(
                ["forged_block"],
                self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"][
                    "blocks"
                ]["produced"],
            )
            g.add_metric(
                ["tstamp_last_forged"],
                self.dposlib.delegates.get(delegate_id=self.cfg.delegate)["data"][
                    "blocks"
                ]["last"]["timestamp"]["unix"],
            )
            g.add_metric(
                ["wallet_valance"],
                self.dposlib.wallets.get(
                    wallet_id=self.dposlib.delegates.get(delegate_id=self.cfg.delegate)[
                        "data"
                    ]["address"]
                )["data"]["balance"],
            )
        except:
            g.add_metric(["error"], 1)
            pass

        return g

    def _collect_voters(self):
        g = GaugeMetricFamily("tbw_voters", "Delegate voters list", labels=["voters"])

        try:
            voters_list = self.dposlib.delegates.voters(delegate_id=self.cfg.delegate)[
                "data"
            ]
            for voter in voters_list:
                g.add_metric(
                    [voter["address"]], int(voter["balance"]) / self.cfg.atomic
                )
        except:
            g.add_metric(["error"], 1)
            pass

        return g

    def _collect_network(self):
        g = GaugeMetricFamily(
            "tbw_network", "network data", labels=["network", "version"]
        )

        try:
            g.add_metric(["peers_number"], self.dposlib.peers.all()["meta"]["count"])

            peers_version = dict()
            peers_data = self.dposlib.peers.all()["data"]
            for peer in peers_data:
                if peer["version"] in peers_version.keys():
                    peers_version[peer["version"]] += 1
                else:
                    peers_version[peer["version"]] = 1

            for version in peers_version:
                g.add_metric(["peer_version", version], peers_version[version])
        except:
            g.add_metric(["error"], 1)

        return g

    def _collect_token(self):
        g = GaugeMetricFamily("tbw_token", "token data", labels=["token"])

        if self.cg:
            self.token_price = self.cg.get_price(
                ids=self.cfg.cg_token_id, vs_currencies=self.cfg.cg_trading_pair
            )[self.cfg.cg_token_id][self.cfg.cg_trading_pair]
            g.add_metric(["price"], self.token_price)
        else:
            g.add_metric(["error"], 1)
            return g

        return g

    def _collect_transactions(self):
        g = GaugeMetricFamily(
            "tbw_transactions", "transactions", labels=["address", "datetime"]
        )

        try:
            self.transactions = self.tbwdb.processed_transactions().fetchall()
            if len(self.transactions):
                for transaction in self.transactions:
                    g.add_metric(
                        [transaction[0], transaction[2]],
                        float(transaction[1]) / self.cfg.atomic,
                    )
            else:
                g.add_metric(["0", "0"], 0)
        except:
            g.add_metric(["error"], 1)
            return g

        return g

    def _cal_bl_reward(self, voters_balance, delegates, block_rewards):
        del_votes = []
        for delegate in delegates:
            del_votes.append(int(delegate["votes"]))
        i = 0
        sdel_votes = sorted(del_votes, reverse=True)
        for votes in sdel_votes:
            if sdel_votes.index(votes) > 53:
                return 0
            if votes <= voters_balance:
                if sdel_votes.index(votes) + 1 > 53:
                    return 0
                return block_rewards["ranks"][str(sdel_votes.index(votes) + 1)]
        return 0

    def _collect_reward_calc(self):
        g = GaugeMetricFamily(
            "tbw_reward_calc",
            "Tbw reward calc data",
            labels=["new_vote", "blk_reward", "payout_interval_reward"],
        )

        rl_voters_balance = 0
        voters_balance = 0

        voters_list = self.dposlib.delegates.voters(delegate_id=self.cfg.delegate)[
            "data"
        ]
        delegates = self.dposlib.delegates.all()["data"]

        for voter in voters_list:
            voters_balance += int(voter["balance"])
            if voter["address"] not in self.cfg.blacklist_addr.split(","):
                rl_voters_balance += int(voter["balance"])

        try:
            block_rewards = self.dposlib.node.configuration()["data"]["constants"][
                "dynamicReward"
            ]
            block_reward = self._cal_bl_reward(voters_balance, delegates, block_rewards)
        except:
            block_reward = self.dposlib.node.configuration()["data"]["constants"][
                "reward"
            ]

        vshare = block_reward * self.cfg.tbw_voter_share
        for balance in range(200, 20200, 200):
            g.add_metric(
                [
                    "False",
                    str(balance / rl_voters_balance * vshare),
                    str(balance / rl_voters_balance * vshare * self.cfg.tbw_interval),
                ],
                balance,
            )
            vvshare = (
                self._cal_bl_reward(
                    voters_balance + balance * self.cfg.atomic, delegates, block_rewards
                )
                * self.cfg.tbw_voter_share
            )
            g.add_metric(
                [
                    "True",
                    str(
                        balance
                        / (rl_voters_balance + balance * self.cfg.atomic)
                        * vvshare
                    ),
                    str(
                        balance
                        / (rl_voters_balance + balance * self.cfg.atomic)
                        * vvshare
                        * self.cfg.tbw_interval
                    ),
                ],
                balance,
            )
        return g
