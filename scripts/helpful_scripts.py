from brownie import (
    accounts,
    network,
    config,
    Contract,
    MockV3Aggregator,
    VRFCoordinatorMock,
    LinkToken,
    interface,
)
from web3 import Web3

FORKED_LOCAL_ENVIROMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIROMENTS = ["development", "ganache-local"]

DECIMALS = 8
STARTING_PRICE = 200000000000


def get_account(index=None, id=None):
    # Three methods of getting account:
    # 1. accounts[index]
    # 2. accounts.add("env")
    # 3. accounts.load("id")
    if index:
        return accounts[index]
    if id:
        return accounts.load(id)
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENTS
        or network.show_active() in FORKED_LOCAL_ENVIROMENTS
    ):
        return accounts[0]
        # by default, forked envrioment doesn't come with its own accounts
        # we have to create our own custom mainnet fork:
        # for infura:
        # "brownie networks add development mainnet-fork-dev cmd=ganache-cli host=http://127.0.0.1 fork='https://mainnet.infura.io/v3/9b8ac960613d4e8c8ca331c82bd92b21' accounts=10 mnemonic=brownie port=8545"
        # for alchemy (preffered):
        # "brownie networks add development mainnet-fork-dev cmd=ganache-cli host=http://127.0.0.1 fork=https://eth-mainnet.alchemyapi.io/v2/iMVebpdRq-i7QXx0KPAl4B99tUrGJfP1 accounts=10 mnemonic=brownie port=8545"
    # default:
    return accounts.add(config["wallets"]["from_key"])


# mapping (dictionary):
contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """
    This function will grab the contract addresses from the brownie config
    if defindec, otherwise, it will deploay a mock version of that contract,
    and return that mock contract.

    Args:
        contract_name (string)

    Returns:
        brownie.network.contract.ProjectContract: the most recently deployed version
        of this contract
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        if len(contract_type) <= 0:  # if no Mock contract is deployed, we deploy it
            deploy_mocks()
        contract = contract_type[-1]  # same as <contract>[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
    return contract


def deploy_mocks(decimals=DECIMALS, starting_price=STARTING_PRICE):
    # deploy our version of price feed contract - known as "Mocking"
    print(f"The active network is {network.show_active()}")
    print("Deploying Mocks...")
    MockV3Aggregator.deploy(decimals, starting_price, {"from": get_account()})
    link_token = LinkToken.deploy({"from": get_account()})
    VRFCoordinatorMock.deploy(link_token.address, {"from": get_account()})
    print("Mocks Deployed!\n")


def fund_with_link(
    contract_address, account=None, _link_token=None, amount=100000000000000000
):
    Account = (
        account if account else get_account()
    )  # set it to account if sombody sent it, otherwise get_account()

    link_token = _link_token if _link_token else get_contract("link_token")

    # fund the contract
    tx = link_token.transfer(contract_address, amount, {"from": Account})
    # OR
    # first import interface from brownie and
    # by using LinkTokenInterface:
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contract_address, amount, {"from": Account})
    tx.wait(1)
    print("Contract Funded with Link!")
    return tx
