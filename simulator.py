import random
from dataclasses import field, dataclass
from math import ceil
from typing import List, Dict

from analyzer import Analyzer, Behavior
from bootstrapnode import BootstrapNode
from config import Config
from fullnode import FullNode, Exchange


@dataclass
class Simulator:
    config_path: str = field(default='conf.yaml')
    config: Config = field(init=False)
    bns: List[BootstrapNode] = field(default_factory=list)
    fns: List[FullNode] = field(default_factory=list)
    data: List[str] = field(default_factory=list)
    banned: Dict[int, FullNode] = field(default_factory=dict)
    r = random
    glob_unique_txs = 0
    analyzer: Analyzer = Analyzer()

    def __post_init__(self):
        self._read_config()
        self._set_random()
        self._generate_txs()
        self._generate_bns()
        self._generate_fns()
        self.analyzer.init(self.fns, self.bns)

    def start_simulation(self):
        self._print_starting_sentence()

        epoch_number = self.config.get('EPOCHS')
        pow_difficulty = self.config.get('POW_EXPENSIVENESS')

        for epoch in range(epoch_number):
            # remove bad peers and re-sort peer list
            self.remove_bad_peers(epoch)
            # add redeemed peers
            self.add_redeemed_peers()
            # mempool state per epoch
            self.init_peers_mempools()
            # save current peer lists
            self.analyzer.add_peer_lists(epoch)
            # save current mempools
            self.analyzer.save_mempools(epoch)
            # start sending messages:
            for fn in self.fns:
                self.analyzer.generate_new_exchange(epoch, fn.id)
                for bn_id in fn.subscriptions:
                    bn = self.bns[bn_id]

                    token = bn.get_epoch_token(fn.id)
                    # if i am banned
                    if not token:
                        still_banned = fn.recompute_pow(pow_difficulty)
                        if not still_banned: bn.add_to_next_epoch(fn.id)
                        continue
                    partner_id = fn.get_partner_id(bn.peers, token, fn.id)
                    # print('I am {} and i will contact {}'.format(fn.id, partner_id))
                    partner = self.fns[partner_id]

                    if fn.will_byzantine():
                        # print('I am byzantine {} with bn {} (0)'.format(fn.id, bn_id))
                        bn.add_pom(epoch, fn.id)
                        self.analyzer.generate_new_trade(epoch, fn.id, partner_id, Exchange.ABORT, 0, 0,
                                                         len(fn.frozen_mempool), -1, len(partner.frozen_mempool),
                                                         -1, bn.id, Behavior.BYZANTINE)
                        continue
                    if partner.will_byzantine():
                        # print('I am byzantine {} with bn {} (1)'.format(partner.id, bn_id))
                        bn.add_pom(epoch, partner.id)
                        self.analyzer.generate_new_trade(epoch, fn.id, partner_id, Exchange.ABORT, 0, 0,
                                                         len(fn.frozen_mempool), -1, len(partner.frozen_mempool),
                                                         -1, bn.id, Behavior.BYZANTINE)
                        continue

                    exchange_type, mem_size, partner_mem_size, dupl, partner_dupl = fn.exchange_txs(partner)
                    self.analyzer.generate_new_trade(epoch, fn.id, partner_id, exchange_type, dupl, partner_dupl,
                                                     len(fn.frozen_mempool), mem_size, len(partner.frozen_mempool),
                                                     partner_mem_size, bn.id, Behavior.PROTOCOL)

            self.print_mempool_state()
            print('Done epoch {}'.format(epoch))
        print('Done simulation')
        self.analyzer.analyze()

    def _generate_txs(self):
        tx_number = self.config.get('TX_TOTAL')
        tx_mean = self.config.get('TX_MEAN_SIZE')
        tx_stdev = self.config.get('TX_STDEV_SIZE')

        for _ in range(tx_number):
            tx_size = self._get_tx_size(tx_mean, tx_stdev)
            tx_content = bytearray(random.getrandbits(8) for _ in range(tx_size)).hex()
            self.data.append(tx_content)

    def remove_bad_peers(self, epoch: int):
        for bn in self.bns:
            to_be_banned = bn.poms[epoch - 1] if epoch - 1 in bn.poms else []
            for peer in bn.peers:
                if peer in to_be_banned:
                    bn.peers.remove(peer)
            bn.sort_peers()

    @staticmethod
    def _get_tx_size(mean, stdev):
        return ceil(random.normalvariate(mean, stdev))

    def _read_config(self):
        self.config = Config(self.config_path)

    def _generate_bns(self):
        bn_number = self.config.get('BOOTSTRAP_NODE_TOTAL')

        self.bns = [BootstrapNode(id) for id in range(bn_number)]

    def _set_random(self):
        seed = self.config.get('SEED')
        self.r.seed(seed)

    def get_txs_set(self):
        mempool_size = self.config.get('MEMPOOL_TOTAL')
        return random.sample(self.data, mempool_size)

    def get_subscriptions(self, fn_id):
        subscription_number = self.config.get('SUBSCRIPTION_TOTAL')
        bn_number = self.config.get('BOOTSTRAP_NODE_TOTAL')

        to_be_subscribed = self.bns if subscription_number == bn_number \
            else [bn for bn in random.sample(self.bns, subscription_number)]
        for bn in to_be_subscribed:
            bn.set_peer(fn_id)

        return [bn.id for bn in to_be_subscribed]

    def init_peers_mempools(self):
        for fn in self.fns:
            fn.init_mempool()

    def _generate_fns(self):
        node_number = self.config.get('FULL_NODE_TOTAL')
        byzantine_number = self.config.get('BYZANTINE_FULL_NODES')
        rational_number = self.config.get('RATIONAL_FULL_NODES')
        max_bal = self.config.get('MAX_BAL_EX')
        max_opt = self.config.get('MAX_OPT_EX')
        assert (node_number >= byzantine_number + rational_number)

        for id in range(node_number):
            mempool = self.get_txs_set()
            subscriptions = self.get_subscriptions(id)
            fn = FullNode(id, max_bal, max_opt)
            if id < byzantine_number:
                fn.set_byzantine()
            elif id < byzantine_number + rational_number:
                fn.set_rational()
            fn.set_mempool(mempool)
            fn.set_subscriptions(subscriptions)
            self.fns.append(fn)

    def _print_starting_sentence(self):
        bn_number = self.config.get('BOOTSTRAP_NODE_TOTAL')
        node_number = self.config.get('FULL_NODE_TOTAL')
        byzantine_number = self.config.get('BYZANTINE_FULL_NODES')
        rational_number = self.config.get('RATIONAL_FULL_NODES')
        epochs = self.config.get('EPOCHS')
        mempool_number = self.config.get('MEMPOOL_TOTAL')

        self.glob_unique_txs = len(set(sum([list(fn.mempool) for fn in self.fns], [])))

        print("Starting simulation with:"
              "\n- {} bootstrap nodes"
              "\n- {} full nodes ({} byzantine, {} rational)"
              "\n- {} global transactions"
              "\n- {} epochs"
              "\n- {} mempool size"
              .format(bn_number, node_number, byzantine_number, rational_number, self.glob_unique_txs, epochs,
                      mempool_number))

    def add_redeemed_peers(self):
        for bn in self.bns:
            bn.peers.extend(bn.next_epoch_peers)
            bn.next_epoch_peers = []

    def print_mempool_state(self):
        tx_number = self.config.get('TX_TOTAL')
        mempool_sizes = [len(fn.mempool) for fn in self.fns]
        min, max = tx_number, 0

        for size in mempool_sizes:
            if size > max:
                max = size
            if size < min:
                min = size
