"""D3: the sole approved acceptance change, isolated from renderer/audio."""
CONTRACT_ID='ATS_SYNC_2026-10-B'
CONTRACT_STATUS='3.0.2-A1 integration approved; shared A input preserved'
SEED_ERROR='must be an integer between 0 and 2147483647'
_installed=False

def apply_seed_guard():
    global _installed
    if _installed:return
    from .pro_schema import Checker
    original=Checker.number
    def number(self,value,path,lo,hi,integer=False):
        if path=='$.style.seed':
            if isinstance(value,bool) or not isinstance(value,int) or not 0<=value<=2147483647:
                self.error(path,SEED_ERROR)
            return
        return original(self,value,path,lo,hi,integer)
    Checker.number=number
    _installed=True

