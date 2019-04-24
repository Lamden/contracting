from ...db.orm import Variable, Hash, ForeignVariable, ForeignHash
from ...db.contract import Contract

# Define the locals that will be available for smart contracts at runtime
exports = {
    'Variable': Variable,
    'Hash': Hash,
    'ForeignVariable': ForeignVariable,
    'ForeignHash': ForeignHash,
    '__Contract': Contract
}