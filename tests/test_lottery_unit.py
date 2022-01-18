from brownie import Lottery, accounts, config, network, exceptions
from scripts.deploy_lottery import deploy_lottery, get_account
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIROMENTS,
    get_account,
    fund_with_link,
    get_contract,
)
from web3 import Web3
import pytest


"""
Unit Test:
    1. A way of testing the smallest pieces of code in an isolated instance (system)
    2. on Development Network
Integration Test:
    1. A way of testing across multiple complex systems
    2. on Testnet
"""


def test_get_entrance_fee():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip()
    Lottery = deploy_lottery()
    # Act
    entrance_fee = Lottery.getEntranceFee()
    # Assert
    # 50 / 20000 = 0.025 eth (on development with Mocks)
    expected_entrance_fee = Web3.toWei(0.025, "ether")
    assert expected_entrance_fee == entrance_fee
    # when testing on mainnet-fork:
    # "brownie networks add development mainnet-fork cmd=ganache-cli host=http://127.0.0.1 fork=https://eth-mainnet.alchemyapi.io/v2/w7mxSt_uN0bgdGSwzA9Zw9xGUrYKYlru accounts=10 mnemonic=brownie port=8545"
    # after creating mainnet-fork network:
    # "brownie test --network mainnet-fork"


def test_cant_enter_unless_started():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip()
    Lottery = deploy_lottery()
    # Act / Assert
    with pytest.raises(exceptions.VirtualMachineError):
        Lottery.enter({"from": get_account(), "value": Lottery.getEntranceFee()})


def test_can_start_and_enter_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip()
    Lottery = deploy_lottery()
    Admin = get_account(id="kobaAccount")
    Account = get_account()
    # Act
    Lottery.startLottery({"from": Admin})
    Lottery.enter({"from": Account, "value": Lottery.getEntranceFee()})
    # Assert
    assert Lottery.players(0) == Account


def test_can_end_lottery():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip()
    Lottery = deploy_lottery()
    Admin = get_account(id="kobaAccount")
    Lottery.startLottery({"from": Admin})
    # Act
    fund_with_link(Lottery.address)
    Lottery.endLottery({"from": Admin}).wait(1)
    # Assert
    assert Lottery.lottery_state() == 2


def test_can_pick_winner_correctly():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip()
    Lottery = deploy_lottery()
    Admin = get_account(id="kobaAccount")
    Lottery.startLottery({"from": Admin})
    Lottery.enter({"from": get_account(index=0), "value": Lottery.getEntranceFee()})
    Lottery.enter({"from": get_account(index=1), "value": Lottery.getEntranceFee()})
    Lottery.enter({"from": get_account(index=2), "value": Lottery.getEntranceFee()})
    Lottery.enter({"from": get_account(index=3), "value": Lottery.getEntranceFee()})
    fund_with_link(Lottery.address)
    # Act
    starting_balance_of_lottery = Lottery.balance()
    print(f"{starting_balance_of_lottery}$ in Contract")
    starting_balance_of_Winner = get_account(index=1).balance()
    print(f"{starting_balance_of_Winner}$ in Winner's Account")
    transaction = Lottery.endLottery({"from": Admin})
    print(transaction)
    # out of all the events look for RequestedRandomness event and in there find requestID
    request_Id = transaction.events["RequestedRandomness"]["requestId"]
    # to dummy getting the random number back from the chainlink node we are going to
    # pretend to be chainlink node and use this callBackWithRandomness function
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(
        request_Id, STATIC_RNG, Lottery.address, {"from": Admin}
    ).wait(1)
    print(f"{get_account(index=1).balance()}$ in Winner's account after winning!")
    # Assert
    # since 777 % 4 = 1 winner should be get_account(index=1)
    assert Lottery.recentWinner() == get_account(index=1)
    assert Lottery.balance() == 0
    assert (
        get_account(index=1).balance()
        == starting_balance_of_lottery + starting_balance_of_Winner
    )
