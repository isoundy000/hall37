# -*- coding=utf-8
'''
Created on 2016年6月20日

@author: zhaol
'''
import freetime.util.log as ftlog
import poker.entity.events.tyeventbus as pkeventbus
import poker.util.timestamp as pktimestamp
from hall.entity import hallconf, datachangenotify
from hall.entity.hallconf import HALL_GAMEID
from hall.entity.todotask import TodoTaskHelper, TodoTaskShowInfo, TodoTaskShowRewards
from poker.entity.biz.content import TYContentRegister
from poker.entity.biz.item.item import TYAssetUtils
from poker.entity.biz.message import message as pkmessage
from poker.entity.dao import gamedata
from poker.entity.events.tyevent import EventConfigure


class HallLoginRewardsItem(object):
    def __init__(self):
        self.items = None
        self.conditions = None
        self.mail = None

    def decodeFromDict(self, d):
        from hall.entity.hallusercond import UserConditionRegister
        self.conditions = UserConditionRegister.decodeList(d.get('conditions', []))
        rewardContent = d.get('rewardContent')
        if rewardContent:
            self.items = TYContentRegister.decodeFromDict(rewardContent)
        self.mail = d.get('mail', '')
        return self

    def sendRewards(self, userId, gameId, clientId):
        bSend = True

        for cond in self.conditions:
            if not cond.check(gameId, userId, clientId, pktimestamp.getCurrentTimestamp()):
                bSend = False

        if bSend:
            from hall.entity import hallitem
            userAssets = hallitem.itemSystem.loadUserAssets(userId)
            assetList = userAssets.sendContent(gameId
                                               , self.items
                                               , 1
                                               , True
                                               , pktimestamp.getCurrentTimestamp()
                                               , 'LOGIN_REWARD'
                                               , 0)

            if assetList:
                if ftlog.is_debug():
                    ftlog.debug('hall_login_reward.sendReward gameId=', gameId,
                                'userId=', userId,
                                'rewards=', [(atup[0].kindId, atup[1]) for atup in assetList])
                # 记录登录奖励获取时间
                gamedata.setGameAttr(userId, HALL_GAMEID, 'login_reward', pktimestamp.getCurrentTimestamp())
                # 通知更新
                changedDataNames = TYAssetUtils.getChangeDataNames(assetList)
                datachangenotify.sendDataChangeNotify(gameId, userId, changedDataNames)
                pkmessage.send(gameId, pkmessage.MESSAGE_TYPE_SYSTEM, userId, self.mail)
                from poker.util import strutil
                _, cVer, _ = strutil.parseClientId(clientId)
                if cVer < 3.90:
                    TodoTaskHelper.sendTodoTask(gameId, userId, TodoTaskShowInfo(self.mail, True))
                else:
                    rewardsList = []
                    for assetItemTuple in assetList:
                        '''
                        0 - assetItem
                        1 - count
                        2 - final
                        '''
                        assetItem = assetItemTuple[0]
                        reward = {}
                        reward['name'] = assetItem.displayName
                        reward['pic'] = assetItem.pic
                        reward['count'] = assetItemTuple[1]
                        rewardsList.append(reward)

                    if ftlog.is_debug():
                        ftlog.debug('hall_login_reward.TodoTaskShowRewards rewardsList: ', rewardsList)

                    TodoTaskHelper.sendTodoTask(gameId, userId, TodoTaskShowRewards(rewardsList))


_loginRewards = []
_inited = False


def _reloadConf():
    global _loginRewards

    _loginRewards = []

    conf = hallconf.getLoginRewardConf()
    rewards = conf.get('rewards', [])
    for reward in rewards:
        rItem = HallLoginRewardsItem().decodeFromDict(reward)
        _loginRewards.append(rItem)

    ftlog.debug('hall_login_reward._reloadConf successed config=', _loginRewards)


def _onConfChanged(event):
    global _inited

    if _inited and event.isModuleChanged('login_reward'):
        ftlog.debug('hall_login_reward._onConfChanged')
        _reloadConf()


def _initialize():
    global _inited

    ftlog.debug('hall_login_reward._initialize begin')
    if not _inited:
        _inited = True
        _reloadConf()
        pkeventbus.globalEventBus.subscribe(EventConfigure, _onConfChanged)
    ftlog.debug('hall_login_reward._initialize end')


def sendLoginReward(userId, gameId, clientId):
    global _loginRewards
    if ftlog.is_debug():
        ftlog.debug('hall_login_reward.sendLoginReward userId:', userId
                    , ' gameId:', gameId
                    , ' clientId:', clientId)

    for reward in _loginRewards:
        reward.sendRewards(userId, gameId, clientId)
