# -*- coding:utf-8 -*-
import os
import re
import time
import requests
import pandas as pd
from lxml import etree
from openpyxl.reader.excel import load_workbook
from py2neo import Graph
import re
from T3sqlite.Download_T3_Data import download_t3
from T3sqlite.Process_T3 import Process_T3
from T3sqlite.Build_text_KG import processIfThen, processOD
from GetCookies import keep_seesion

def getAVLT3info(owner_name):
    T3ProjectList = []
    for i in owner_name:
        url = 'http://10.122.66.105/t3/WS/AjaxChassis.aspx?q=' + i
        response = requests.get(url, headers=headers).text
        response = response.replace('value', "\"value\"")
        response = eval(response)
        for j in response:
            T3ProjectList.append((j['value'], i))

    return T3ProjectList


def compareT3(T3ProjectList, update_date):
    dfT3 = pd.DataFrame(T3ProjectList, columns=['Project name', 'Owner'])
    dfT3['System'] = 't3'
    TML = dfT3.reset_index(drop=True)
    TML['废除'] = 'TBD'

    # 对比TML并覆盖
    old_sheet = pd.ExcelFile('./T3sqlite/AVLT3 TML.xlsx').sheet_names[-1]
    oldTML = pd.read_excel('./T3sqlite/AVLT3 TML.xlsx', sheet_name=old_sheet)
    for index, row in TML.iterrows():
        value = oldTML[(oldTML['Project name'] == row['Project name']) & (oldTML['System'] == row['System'])]['废除']
        try:
            TML.loc[(TML['Project name'] == row['Project name']) & (TML['System'] == row['System']), '废除'] = value.values[0]
        except IndexError:
            pass

    TML['Version'] = 'EOL'

    VersionT3 = list(TML.loc[(TML['废除'] == 'N') & (TML['System'] == 't3'), 'Project name'])
    session = keep_seesion('T3')
    getT3dateurl = 'http://10.122.66.105/t3/Default.aspx?vp=viewlist'
    VIEWSTATE = etree.HTML(session.get(getT3dateurl, headers=headers).text).xpath(
        '//*[@id="__VIEWSTATE"]/@value')
    for index, i in enumerate(VersionT3):
        T3POSTData = {
            '__VIEWSTATEGENERATOR': '42A6D4D6',
            '__VIEWSTATEENCRYPTED': '',
            'VP$DdlChassis': '-1',
            'VP$TxtChassis': i,
            '__ASYNCPOST': 'true',
            'VP$ScriptManager1': 'VP$UpList|VP$TxtChassis',
            '__EVENTTARGET': 'VP$TxtChassis',
            '__EVENTARGUMENT': '',
            '__LASTFOCUS': '',
            '__VIEWSTATE': VIEWSTATE[0],
        }
        response = session.post(getT3dateurl, headers=headers, data=T3POSTData)
        try:
            date = etree.HTML(response.text).xpath('//*[@id="VP_GvList_ctl02"]/td[5]/text()')[0]
            print(index, i, date)
            TML.loc[(TML['Project name'] == i) & (TML['System'] == 't3'), 'Version'] = date
        except IndexError:
            print(index, i + '未找到！')
            TML.loc[(TML['Project name'] == i) & (TML['System'] == 't3'), 'Version'] = '未release'

    # 对比新旧TML得出更新的T3项目
    NonEOLnew = TML.loc[(TML['废除'] == 'N') & (TML['System'] == 't3')]
    NonEOLold = oldTML.loc[(oldTML['废除'] == 'N') & (oldTML['System'] == 't3')]
    merged_df = pd.merge(NonEOLold, NonEOLnew, on='Project name', how='right', suffixes=('_old', '_new'))
    updated_versions = merged_df[merged_df['Version_old'] != merged_df['Version_new']]
    print(updated_versions[['Project name', 'Version_old', 'Version_new']].to_markdown())

    locate = './T3sqlite/AVLT3 TML.xlsx'
    with pd.ExcelWriter(locate, engine='openpyxl', mode='a') as writer:
        TML.to_excel(writer, sheet_name=update_date, index=True)

    sheet_names = list(pd.read_excel(locate, sheet_name=None).keys())
    workbook = load_workbook(locate)
    for sheet_name in sheet_names[:-2]:
        workbook.remove(workbook[sheet_name])
    workbook.save(locate)

    return list(updated_versions['Project name'])

def update_KG(template):
    g = Graph('http://10.184.45.228:7474', auth=('neo4j', '12345678'), name='neo4j')
    template = template[template['Type'] == 'Text rule']
    project_list = template['Project name'].unique()
    print(len(project_list))
    for index, projectname in enumerate(project_list[:]):
        cypher = f"MATCH (n)-[r]-() WHERE n.projectname = '{projectname}' DELETE r, n"
        g.run(cypher)
        try:
            project_OD_rule = template[template['Project name'] == projectname].copy()
            project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: re.sub(r"SBB.{7}", "", x))
            project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: x.replace('()', ''))
            processIfThen(project_OD_rule, projectname)
            processOD(project_OD_rule, projectname)
            print(index, projectname)
        except Exception as e:
            print('error', index, projectname)
            print(e)


def main():
    global headers
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}

    owner_name = ["huangwf2", "liubin37", "lijx21", "liushuang21", "huanghx11", "censq2",
                  "shangjw1", "wangzb10", "zhangcl4", "zhaolei21", 'zhangying72', 'shiyy12']

    date = time.strftime("%y-%m-%d %H%M", time.localtime())

    T3ProjectList = getAVLT3info(owner_name)
    Need_update_T3list = compareT3(T3ProjectList, date)

    downloadpath = './T3sqlite/SourceT3list'
    if not os.path.exists(downloadpath):
        os.mkdir(downloadpath)

    for i in Need_update_T3list:
        download_t3(i)

    updateDF = Process_T3(date)
    # update_KG(updateDF)
