import random
from dataclasses import field, dataclass
from typing import List, Dict


@dataclass
class BootstrapNode:
    id: int
    peers: List[int] = field(init=False, default_factory=list)
    next_epoch_peers: List[int] = field(init=False, default_factory=list)
    poms: Dict[int, List[int]] = field(init=False, default_factory=dict)
    hexdigits = "0123456789ABCDEF"

    def set_peer(self, fn_id):
        self.peers.append(fn_id)

    def sort_peers(self):
        self.peers.sort()

    def get_epoch_token(self, id):
        if id in self.peers:
            return "".join([self.hexdigits[random.randint(0, 0xF)] for _ in range(64)])

    def add_to_next_epoch(self, peer_id):
        self.next_epoch_peers.append(peer_id)

    def add_pom(self, epoch: int, peer_id: int):
        if epoch in self.poms:
            self.poms[epoch].append(peer_id)
        else:
            self.poms[epoch] = [peer_id]
