import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple

from bootstrapnode import BootstrapNode
from fullnode import FullNode, Exchange
from plotter import violin_plot, grouped_bar_plot


class Behavior(Enum):
    PROTOCOL = 0
    BYZANTINE = 1


@dataclass(unsafe_hash=True)
class TradeInstance:
    sender: int
    receiver: int
    exchange_type: Exchange
    sender_duplicates: int
    receiver_duplicates: int
    sender_mempool: Tuple[int, int]
    receiver_mempool: Tuple[int, int]
    bn_id: int
    behavior: Behavior


@dataclass
class Analyzer:
    fns: List[FullNode] = field(init=False, default_factory=list)
    bns: List[BootstrapNode] = field(init=False, default_factory=list)
    # epoch -> full_node_id -> exchange_id
    exchages: Dict[int, Dict[int, List[str]]] = field(init=False, default_factory=dict)
    trades: Dict[str, TradeInstance] = field(init=False, default_factory=dict)
    # index is epoch, each inside dict consist of key: fn_id, value: mempool size
    mempools: Dict[int, Dict[int, int]] = field(init=False, default_factory=dict)
    peer_lists: Dict[int, Dict[int, List[int]]] = field(init=False, default_factory=dict)

    def init(self, fns: List[FullNode], bns: List[BootstrapNode]):
        self.fns = fns
        self.bns = bns

    def add_peer_lists(self, epoch: int):
        if epoch not in self.peer_lists: self.peer_lists[epoch] = {}
        for bn in self.bns:
            self.peer_lists[epoch][bn.id] = deepcopy(bn.peers)

    def generate_new_exchange(self, epoch: int, fn_id: int):
        if epoch not in self.exchages: self.exchages[epoch] = {}
        if fn_id not in self.exchages[epoch]: self.exchages[epoch][fn_id] = []

    def add_trade(self, epoch, fn_id, trade_id: str):
        self.exchages[epoch][fn_id].append(trade_id)

    @staticmethod
    def _generate_trade_id():
        return uuid.uuid4().hex

    def generate_new_trade(self, epoch, sender, receiver, type, sender_dupl, receiver_dupl, sender_mempool_before,
                           sender_mempool_before_after, receiver_mempool_before, receiver_mempool_before_after, bn_id,
                           behavior):
        trade_id = self._generate_trade_id()
        trade = TradeInstance(sender, receiver, type, sender_dupl, receiver_dupl,
                              (sender_mempool_before, sender_mempool_before_after),
                              (receiver_mempool_before, receiver_mempool_before_after), bn_id, behavior)
        self.add_trade(epoch, sender, trade_id)
        self.generate_new_exchange(epoch, receiver)
        self.add_trade(epoch, receiver, trade_id)
        self.trades[trade_id] = trade

    def save_mempools(self, epoch: int):
        self.mempools[epoch] = {}
        for fn in self.fns:
            self.mempools[epoch][fn.id] = len(fn.mempool)

    def analyze(self):
        print("Start analyzing ...")

        x, y = self.fn_distribution_per_bn_and_epoch()
        grouped_bar_plot(x, y, 'Number of peer per epoch per bootstrap node', 'Peer registered', 'Epoch',
                         ('BN1', 'BN2', 'BN3', 'BN4'))

        y, x = self.mempool_per_epoch_size_plot()
        violin_plot(y, x, 'Global view of network mempools', 'Mempool sizes', 'Epoch')

        y, x = self.number_of_trade_per_epoch()
        violin_plot(y, x, 'Peer\'s exchange number per epoch', 'Exchange number', 'Epoch')

        y, x = self.duplicates_per_epoch()
        violin_plot(y, x, 'Number of duplicates per epoch', 'Duplicates number', 'Epoch')

        x, y = self.exchange_type_per_epoch()
        grouped_bar_plot(x, y, 'Trade types per epoch', 'Trade type total', 'Epoch', ('BAL', 'OPT', 'ABORT'))

    # DATA_MANIPULATION
    def mempool_per_epoch_size_plot(self):
        return [list(mempool.values()) for mempool in self.mempools.values()], list(range(len(self.mempools.values())))

    def fn_distribution_per_bn_and_epoch(self):
        data = [[] for _ in range(len(self.bns))]
        for bn in self.bns:
            for epoch in self.peer_lists.keys():
                data[bn.id].append(len(self.peer_lists[epoch][bn.id]))
        return data, list(range(len(data[0])))

    def number_of_trade_per_epoch(self):
        data = [[] for _ in self.exchages.keys()]
        for epoch in self.exchages.keys():
            for exchange in self.exchages[epoch].values():
                to_add = 0
                for exchange_id in exchange:
                    if self.trades[exchange_id].exchange_type != Exchange.ABORT:
                        to_add += 1
                data[epoch].append(to_add)
        return data, list(range(len(self.exchages.keys())))

    def duplicates_per_epoch(self):
        data = [[] for _ in self.exchages.keys()]
        for epoch in self.exchages.keys():
            epoch_trade = set()
            for peer_trades in self.exchages[epoch].values():
                for trade_id in peer_trades:
                    epoch_trade.add(self.trades[trade_id])
            for trade in epoch_trade:
                if trade.receiver_duplicates >= 0:
                    data[epoch].append(trade.receiver_duplicates)
                if trade.sender_duplicates >= 0:
                    data[epoch].append(trade.sender_duplicates)
                if len(data[epoch]) == 0:
                    data[epoch].append(0)
        return data, list(range(len(self.exchages.keys())))

    def exchange_type_per_epoch(self):
        data = [[], [], []]
        for epoch in self.exchages.keys():
            epoch_trade = set()
            for peer_trades in self.exchages[epoch].values():
                for trade_id in peer_trades:
                    epoch_trade.add(self.trades[trade_id])
            data[0].append(len(list(filter(lambda x: x.exchange_type == Exchange.BAL, epoch_trade))))
            data[1].append(len(list(
                filter(lambda x: x.exchange_type == Exchange.OPT_TWO or x.exchange_type == Exchange.OPT_ONE,
                       epoch_trade))))
            data[2].append(len(list(filter(lambda x: x.exchange_type == Exchange.ABORT, epoch_trade))))
        return data, list(range(len(data[0])))
