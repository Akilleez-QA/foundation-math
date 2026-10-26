"""Experimental local domain. Lazy exports keep verifier-only imports separate."""
__all__=['BUDGETS','DomainError','VirtualCharacter','calculate','verify']
def __getattr__(name):
    if name in ('BUDGETS','DomainError'):
        from . import contract
        return getattr(contract,name)
    if name in ('VirtualCharacter','calculate'):
        from . import producer
        return getattr(producer,name)
    if name=='verify':
        from .verifier import verify
        return verify
    raise AttributeError(name)
