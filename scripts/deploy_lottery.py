from scripts.helpful_scripts import (
    get_account,
    get_contract,
    fund_with_link,
    LOCAL_BLOCKCHAIN_ENVIROMENTS,
)
from brownie import Lottery, config, network
import time


def deploy_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        Account = get_account()
    else:
        Account = get_account(id="kobaAccount")
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": Account},
        publish_source=config["networks"][network.show_active()].get(
            "verify", False
        ),  # get "verify" key but if there is no "verify" there, default "False".
    )
    return lottery


def start_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        Account = get_account()
    else:
        Account = get_account(id="kobaAccount")
    lottery = Lottery[-1]
    tx = lottery.startLottery({"from": Account})
    tx.wait(1)  # wait for last transaction to go through
    print("The lottery is started!")


def enter_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        Account = get_account()
    else:
        Account = get_account(id="kobaAccount")
    lottery = Lottery[-1]
    Value = lottery.getEntranceFee() + 100000000
    tx = lottery.enter({"from": Account, "value": Value})
    tx.wait(1)
    print(
        "You succesfully entered a lottery with address: {}".format(
            lottery.players(lottery.getArrayLength() - 1)
        )
    )
    print("All contestants: ")
    totalNum = 0
    while totalNum < lottery.getArrayLength():
        print(lottery.players(totalNum))
        totalNum += 1


def end_lottery():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIROMENTS:
        Account = get_account()
    else:
        Account = get_account(id="kobaAccount")
    lottery = Lottery[-1]
    # we have to fund the contract with LINK token
    fund_with_link(lottery.address).wait(1)
    lottery.endLottery({"from": Account}).wait(1)
    """ 
    when we call end lottery function, we are making the request to chainlink node 
    and the chainlink node will respond by calling the fulfilRandomness function
    so we have to wait for the callback, so we use time.sleep()
    ...
    we also need chainlink nodes to watch the network we are on to recieve the result
    """
    time.sleep(180)
    print(f"The random number: {lottery.randomness()}")
    print(f"{lottery.recentWinner()} is the new winner!")


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
