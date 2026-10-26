"""Standalone experimental arithmetic lab, not a Foundation Math runtime plugin."""
__all__=['calculate','verify','BUDGETS','DomainError','VerificationError']
def __getattr__(name):
    if name=='calculate':
        from .producer import calculate
        return calculate
    if name in ('verify','VerificationError'):
        from . import verifier
        return getattr(verifier,name)
    if name in ('BUDGETS','DomainError'):
        from . import contract
        return getattr(contract,name)
    raise AttributeError(name)
