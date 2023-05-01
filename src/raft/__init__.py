from raft.client import DistDict
from raft.config import SERVERS
client = DistDict(SERVERS)

client['a'] = 'b'
