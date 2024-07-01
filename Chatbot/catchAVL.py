import requests
from lxml import etree
import pandas as pd
from AgentFunction.downloadAVLT3 import Similarity
from Data_Prepare.GetCookies import keep_seesion


def GetPN(question):
    componentdict = {
        '主板': ['MB', 'MB1', 'BB'],
        'cpu': ['SP'],
        '内存条': ['SM'],
        '硬盘': ['HD'],
        'odd': ['OD'],
        '读卡器': ['RHD'],
        '显卡': ['VA'],
        'wifi': ['WIFI'],
        '外插卡': ['LAN', 'PCI'],
        'base': ['MECH_BASE'],
        '电源': ['MECH_BASE'],
        '机构件': ['MECH_LINE'],
        '包材': ['PKG'],
        'label': ['Label'],
        'copt': ['COPT'],
    }
    projectname = question[0].strip()
    projectname = Similarity(projectname, 'AVL')
    compoent = componentdict[question[1].strip().lower()]
    totalDataFrame = pd.DataFrame()
    getAVLurl, headers, session = getAVLInfo(projectname)

    for i in compoent:
        totalDataFrame = pd.concat([totalDataFrame, getComponentInfo(getAVLurl, i, headers, session)]).fillna('')
    if not totalDataFrame.empty:
        return totalDataFrame
    else:
        return f'找不到{projectname}项目的{question[1].strip()}数据,可能是onboard部件'


def getComponentInfo(getAVLurl, component, headers, session):
    try:
        VIEWSTATE = etree.HTML(session.get(getAVLurl, headers=headers).text).xpath(
            '//*[@id="__VIEWSTATE"]/@value')
        AVLInfoPOSTData = {
            'VP$ScriptManager1': 'VP$UpGroup|VP$DdlCategoryFilter',
            'VP$DdlCategoryFilter': component,
            'VP$DdlGroupFilter': '-1',
            '__EVENTTARGET': 'VP$DdlCategoryFilter',
            '__VIEWSTATEGENERATOR': '8D19A1CC',
            '__ASYNCPOST': 'true',
            '__VIEWSTATE': VIEWSTATE[0]
        }
        if component == 'MB':
            response = session.get(getAVLurl, headers=headers, data=AVLInfoPOSTData)
        else:
            response = session.post(getAVLurl, headers=headers, data=AVLInfoPOSTData)
        htmlPage = etree.HTML(response.text)

        chassisnumber = len(htmlPage.xpath("//thead/tr[@id='VP_TgList_ctl00']/td[@class='ff veti']/text()"))
        descriptions = htmlPage.xpath("//tbody/tr/td[@class='description']/span/text()")
        level = htmlPage.xpath("//tbody/tr/td[@class='level']/text()")
        SBBandPN = htmlPage.xpath("//tbody/tr/td[@class='pn']/nobr/div/text()")
        category = htmlPage.xpath("//*[@id='VP_DdlCategoryFilter']/option[@selected='selected']/text()")
        alt = htmlPage.xpath("//tbody/tr/td[@class='qtyalt']")
        status = htmlPage.xpath("//tbody/tr/td[@class='status']")
        TotalChassis = pd.DataFrame()
        for i in range(chassisnumber):
            chassisName = htmlPage.xpath("//thead/tr[@id='VP_TgList_ctl00']/td[@class='ff veti']/text()")[i]
            chassis = htmlPage.xpath("//tbody/tr/td[" + str(i + 1) + "]")
            chassisList = ['' if not i.xpath("./text()") else i.xpath("./text()")[0] for i in chassis]
            chassisInfo = pd.DataFrame({chassisName: chassisList})
            TotalChassis = pd.concat([TotalChassis, chassisInfo], axis=1)
        altList = ['' if not i.xpath("./text()") else i.xpath("./text()")[0] for i in alt]
        statusList = ['' if not i.xpath("./text()") else i.xpath("./text()")[0] for i in status]

        AVL_info = pd.DataFrame({
            # 'category': category[0],
            'descriptions': descriptions,
            'level': level,
            'PN': SBBandPN,
            'alt': altList,
            'status': statusList
        })
        AVL_info = pd.concat([TotalChassis, AVL_info], axis=1)
        if not AVL_info.empty:
            # print(AVL_info.to_markdown(index=False))
            return AVL_info
    except IndexError:
        print('项目未找到！')


def getAVLInfo(projectName):
    # catch Viewstate
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}

    session = keep_seesion('NAVL')

    getVIEWSTATEurl = 'http://10.122.66.105/NAVL/Default.aspx?vp=viewavllist'
    VIEWSTATE = etree.HTML(session.get(getVIEWSTATEurl, headers=headers).text).xpath(
        '//*[@id="__VIEWSTATE"]/@value')

    # get newest AVL url
    AVLNameData = {
        'VP$ScriptManager1': 'VP$UpdatePanel1|VP$TxtFolderFilter',
        'VP$DdlFolderFilter': '-1',
        'VP$TxtFolderFilter': projectName,
        '__EVENTTARGET': 'VP$TxtFolderFilter',
        '__VIEWSTATEGENERATOR': '8D19A1CC',
        '__VIEWSTATEENCRYPTED': '',
        '__ASYNCPOST': 'true',
        '__VIEWSTATE': VIEWSTATE[0]
    }
    response = session.post(getVIEWSTATEurl, headers=headers, data=AVLNameData)
    getAVLurl = 'http://10.122.66.105' + \
                etree.HTML(response.text).xpath('//*[@id="VP_GvList_ctl02"]/td[3]/a/@href')[0]
    print(getAVLurl)
    return getAVLurl, headers, session
