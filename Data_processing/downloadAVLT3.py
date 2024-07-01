import re
from lxml import etree
from fuzzywuzzy import process
import pandas as pd
from Data_Prepare.GetCookies import keep_seesion


def GetAVL(question):
    try:
        if 'avl' in question[1].lower():
            return getAVLInfo(question[0])
        elif 't3' in question[1].lower():
            return getT3Info(question[0])
        else:
            return f'Prompt出错, 无法处理该请求, Prompt输出{question}'
    except IndexError:
        return f"没有该{question[1].lower()}项目"


def getAVLInfo(projectName):
    # Similarity
    projectName = Similarity(projectName, 'AVL')

    # catch Viewstate
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}

    session = keep_seesion('NAVL')

    getVIEWSTATEurl = 'http://10.122.66.105/NAVL/Default.aspx?vp=viewavllist'
    VIEWSTATE = etree.HTML(session.get(getVIEWSTATEurl, headers=headers).text).xpath('//*[@id="__VIEWSTATE"]/@value')

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
                etree.HTML(response.text).xpath('//*[@id="VP_GvList_ctl02"]/td[3]/a/@href')[0].replace('viewavlpartavl',
                                                                                                       'viewavlver')

    # download
    response = session.get(url=getAVLurl, headers=headers)
    downloadLink = 'http://10.122.66.105/NAVL/' + etree.HTML(response.text).xpath('//*[@id="VP_HlExport"]/@href')[0]
    response = session.get(url=downloadLink, headers=headers)
    content_disposition = response.headers.get('Content-Disposition')
    pattern = r'filename=(.+)'
    filename = re.search(pattern, content_disposition).group(1).replace('%20', ' ')

    return f'{filename} AVL download link as below:<br> {downloadLink}'


def getT3Info(projectName):
    # Similarity
    projectName = Similarity(projectName, 't3')

    # catch Viewstate
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}

    session = keep_seesion('T3')

    getVIEWSTATEurl = 'http://10.122.66.105/t3/Default.aspx?vp=viewlist'
    VIEWSTATE = etree.HTML(session.get(getVIEWSTATEurl, headers=headers).text).xpath(
        '//*[@id="__VIEWSTATE"]/@value')

    # get newest T3 url
    T3NameData = {
        'VP$ScriptManager1': 'VP$UpList|VP$TxtChassis',
        'VP$DdlChassis': '-1',
        'VP$TxtChassis': projectName,
        '__EVENTTARGET': 'VP$TxtChassis',
        '__VIEWSTATEGENERATOR': '42A6D4D6',
        '__VIEWSTATEENCRYPTED': '',
        '__ASYNCPOST': 'true',
        '__VIEWSTATE': VIEWSTATE[0]
    }
    response = session.post(getVIEWSTATEurl, headers=headers, data=T3NameData)
    getT3url = 'http://10.122.66.105' + etree.HTML(response.text).xpath('//*[@id="VP_GvList_ctl02"]/td[3]/a/@href')[0]

    # download
    response = session.get(url=getT3url, headers=headers)
    downloadLink = 'http://10.122.66.105/T3/' + etree.HTML(response.text).xpath('//*[@id="VP_HlExport"]/@href')[0]
    response = session.get(url=downloadLink, headers=headers)
    content_disposition = response.headers.get('Content-Disposition')
    pattern = r'filename=(.+)'
    filename = re.search(pattern, content_disposition).group(1).replace('%20', ' ')

    return f'{filename} T3 download link as below:<br> {downloadLink}'

def Similarity(projectName,type):
    # Similarity
    template = pd.read_excel("./Data_Prepare/AVLT3 TML.xlsx")
    if type == "ALL":
        Project = template['Project name']
    else:
        Project = template.loc[template['System'] == type]['Project name']
    processProjects = Project.str.lower().replace(['thinkcentre', ' ', 'yangtian'], ['tc', '', 'yt'],
                                                     regex=True).tolist()

    matchDict = {
        'qitian': 'qt',
        '启天': 'qt',
        'yangtian': 'yt',
        '扬天': 'yt',
        'thinkcentre': 'tc',
        'thinkcenter': 'tc',
    }
    for key, value in matchDict.items():
        projectName = projectName.lower().replace(" ", "").replace(key, value)

    my_dict = dict(zip(processProjects, Project.tolist()))

    matches = process.extract(projectName, processProjects, limit=1)
    most_similar_project_name, similarity_score = matches[0]
    most_similar_project_name = my_dict[most_similar_project_name]
    print(f'最相似的项目名: {most_similar_project_name}, 相似度: {similarity_score}')
    if similarity_score > 50:
        projectName = most_similar_project_name
    return projectName
