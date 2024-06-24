import requests
from lxml import etree
from Data_Prepare.GetCookies import keep_seesion
from AgentFunction.downloadAVLT3 import Similarity


def GetProjectInfo(info):
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}
    ProjectList = []

    url = 'http://10.122.66.105/navl/WS/AjaxProject.aspx?q=' + info
    response = requests.get(url, headers=headers).text
    response = response.replace('value', "\"value\"")
    response = eval(response)
    for j in response:
        ProjectList.append((j['value']))
    Projects = ', '.join(ProjectList)
    if len(ProjectList) == 0:
        return f'I can not find the owner/project info of {info}'
    else:
        # return f'{info}负责的项目是{Projects},共{len(ProjectList)}个'
        return f'{info} is responsible for {Projects}, with a total of {len(ProjectList)}.'


def GetInfo(info):
    info = Similarity(info, 'ALL')
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
        'VP$TxtFolderFilter': info,
        '__EVENTTARGET': 'VP$TxtFolderFilter',
        '__VIEWSTATEGENERATOR': '8D19A1CC',
        '__VIEWSTATEENCRYPTED': '',
        '__ASYNCPOST': 'true',
        '__VIEWSTATE': VIEWSTATE[0]
    }
    response = session.post(getVIEWSTATEurl, headers=headers, data=AVLNameData)
    owner = etree.HTML(response.text).xpath('//*[@id="VP_GvList_ctl02"]/td[5]/text()')[0]
    projectname = etree.HTML(response.text).xpath('//option[@selected="selected"]/text()')[0]
    return f'{owner} is responsible for {projectname}.'
