from clove import constants

networks = constants.NETWORKS_WITH_API

print(networks)

def audit_contract(network, txid):
    assert network in networks, 'The network ID ({}) provided is not currently supported'.format(network)
    print(network)

