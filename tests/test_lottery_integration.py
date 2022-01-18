from brownie import network
from scripts.deploy_lottery import deploy_lottery, get_account
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIROMENTS,
    get_account,
    fund_with_link,
)
import pytest
import time


def test_can_pick_winner():
    print("we are on : " + network.show_active() + " network!")
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        pytest.skip
    Lottery = deploy_lottery()
    Account = get_account()
    Lottery.startLottery({"from": Account})
    Lottery.enter({"from": Account, "value": Lottery.getEntranceFee() + 100})
    Lottery.enter({"from": Account, "value": Lottery.getEntranceFee() + 100})
    fund_with_link(Lottery)
    Lottery.endLottery({"from": Account}).wait(5)
    time.sleep(180)
    assert Lottery.recentWinner() == Account
    assert Lottery.balance() == 0
