import hashlib
import random
from copy import deepcopy
from dataclasses import field, dataclass
from enum import Enum
from typing import List, Set, Tuple


class Exchange(Enum):
    BAL = 0
    OPT_ONE = 1  # i am altruistic
    OPT_TWO = 2  # you are altruistic
    ABORT = 3


class Nature(Enum):
    ALTRUISTIC = 0
    RATIONAL = 1
    BYZANTINE = 2


@dataclass
class FullNode:
    id: int
    max_bal: int
    max_opt: int
    mempool: Set[str] = field(init=False, default_factory=set)
    frozen_mempool: Set[str] = field(init=False, default_factory=set)
    subscriptions: List[int] = field(init=False, default_factory=list)
    nature: Nature = Nature.ALTRUISTIC
    byzantine_level = 0.1
    banned_since: int = -1

    def set_nature(self, nature: Nature):
        self.nature = nature

    def set_rational(self):
        self.set_nature(Nature.RATIONAL)

    def set_byzantine(self):
        self.set_nature(Nature.BYZANTINE)

    @staticmethod
    def _compute_tx_id(tx: str):
        return hashlib.sha256(tx.encode()).hexdigest()

    def set_mempool(self, mempool: List[str]):
        self.mempool = set(mempool)
        self.frozen_mempool = deepcopy(self.mempool)

    def set_subscriptions(self, ids: List[int]):
        self.subscriptions = ids

    @staticmethod
    def get_partner_id(peer_list, token, id):
        partner_index = int(token, 16) % len(peer_list)
        partner_id = peer_list[partner_index] if id != peer_list[partner_index] else (peer_list[
                                                                                          partner_index] + 1) % len(
            peer_list)
        assert (partner_id != id)
        return partner_id

    def will_byzantine(self):
        if self.nature == Nature.BYZANTINE and random.uniform(0, 1) < self.byzantine_level:
            return True

    def _select_exchange_type(self, needed: Set[str], promised: Set[str]):

        # if we both have max_bal to exchange
        if len(needed) >= self.max_bal and len(promised) >= self.max_bal:
            return Exchange.BAL, self.max_bal
        if len(needed) == len(promised) and len(needed) > 0:
            return Exchange.BAL, len(needed)
        # if i have more than i can receive
        elif len(promised) > len(needed) > 0:
            return Exchange.BAL, len(needed)
        # if we dont have anything to share
        elif len(needed) == 0 and len(promised) == 0:
            return Exchange.ABORT, -1
        # if i dont have anything im interested in
        elif len(needed) == 0:
            if self.nature == Nature.ALTRUISTIC:
                return Exchange.OPT_ONE, self.max_opt
            return Exchange.ABORT, -1
        # if i dont have anything to share
        elif len(promised) == 0:
            return Exchange.OPT_TWO, self.max_opt
        # if i need more than i can give
        elif len(needed) > len(promised) > 0:
            return Exchange.BAL, len(promised)

    def select_exchange_txs(self, exchange_type: Exchange, needed: Set[str], promised: Set[str], n: int) -> Tuple[
        List[str], List[str]]:
        if exchange_type == Exchange.BAL:
            return random.sample(needed, n), random.sample(promised, n)
        elif exchange_type == Exchange.OPT_ONE:
            return [], promised if len(promised) < self.max_opt else random.sample(promised, self.max_opt)
        elif exchange_type == Exchange.OPT_TWO:
            return needed if len(needed) < self.max_opt else random.sample(needed, self.max_opt), []

    def exchange_txs(self, partner):
        partner_mempool = partner.frozen_mempool

        # i give this
        promised = self.frozen_mempool.difference(partner_mempool)
        # i need this
        needed = partner_mempool.difference(self.frozen_mempool)
        # print('needed {}, promised {}'.format(len(needed), len(promised)))

        exchange_type, exchange_number = self._select_exchange_type(needed, promised)
        if exchange_type == Exchange.ABORT:
            # print('{} with {}, exchange type {}'.format(self.id, partner.id, exchange_type))
            return exchange_type, len(self.mempool), len(partner.mempool), -1, -1

        if partner.nature != Nature.ALTRUISTIC and exchange_type == Exchange.OPT_TWO:
            # print("partner not altruistic!")
            return exchange_type, len(self.mempool), len(partner.mempool), -1, -1

        needed, promised = self.select_exchange_txs(exchange_type, needed, promised, exchange_number)
        # print('{} with {}, exchange type {}, needed: {}, promised: {}, exchange_number {}'.format(self.id, partner.id,
        # exchange_type, len(needed), len(promised), exchange_number))

        duplicates, mempool_size = self.add_to_mempool(needed)
        partner_duplicates, partner_mempool_size = partner.add_to_mempool(promised)
        return exchange_type, mempool_size, partner_mempool_size, duplicates, partner_duplicates

    def add_to_mempool(self, txs: List[str]):
        duplcates = 0
        for tx in txs:
            if tx in self.mempool:
                duplcates += 1
            else:
                self.mempool.add(tx)
        return duplcates, len(self.mempool)

    def recompute_pow(self, pow_difficulty):
        if self.banned_since == -1:
            self.banned_since = 0
        elif 0 < self.banned_since < pow_difficulty:
            self.banned_since += 1
        else:
            self.banned_since = -1
            return False
        return True

    def init_mempool(self):
        self.frozen_mempool = deepcopy(self.mempool)
