# -*- coding: utf-8 -*-
'''
Created on 2015-5-12
@author: zqh
'''

from webmgr.action import actlog
from webmgr.action.remote.utils import tythread
from webmgr.action.remote import execute_remote_py, getMachinePids


def action(options):
    '''
    '''
    params = {}
    params['options'] = options
    haserror = tythread.mutil_thread_machine_action(params, _thread_action_removelogs)
    if haserror :
        actlog.error('remove all logs error !')
        return 0
    return 1

def _thread_action_removelogs(controls):
    '''
    这个方法运行再多线程当中
    '''
    params = controls['params']
    machine = controls['machine']
    options = params['options']

    controls['percent'] = '++++'
    
    # 启动本机的所有进程
    params = ['rmlogs']
    result, outputs = execute_remote_py(options, machine, params)
    if result != 0 :
        controls['done'] = 1
        controls['result'] = 2
        controls['percent'] = 'done'
        controls['outputs'] = outputs
        return
    controls['done'] = 1
    controls['result'] = 1
    controls['outputs'] = outputs

