from multiprocessing import Pool
from lxml import etree
import pandas as pd
from Data_Prepare.GetCookies import keep_seesion


def Getprojectname(question):
    projectname = question[0]
    getT3url, headers = getT3Info(projectname)
    urls = getT3rule(getT3url)
    with Pool(processes=4) as pool:
        results = pool.map(fetch_url, urls)
        pool.close()
        pool.join()
    T3totalRule = pd.concat([r for r in results if r is not None]).drop_duplicates(subset='rules').reset_index(drop=True).rename_axis('Index').to_csv()
    return T3totalRule


def getT3Info(projectName):
    # catch Viewstate
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}
    session = keep_seesion('T3')

    getVIEWSTATEurl = 'http://10.122.66.105/t3/Default.aspx?vp=viewlist'
    VIEWSTATE = etree.HTML(session.get(getVIEWSTATEurl, headers=headers).text).xpath('//*[@id="__VIEWSTATE"]/@value')

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
    print(getT3url)
    return getT3url, headers


def getT3rule(getT3url):
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}

    session = keep_seesion('T3')
    response = session.get(getT3url, headers=headers)

    T3sheet = etree.HTML(response.text).xpath('//*[@id="sheetlist"]/li/a/text()')
    sheet_names = ['BASE-EXTSPKR', 'BASE2', 'SP', 'VA', 'CFC-SM', 'HD-CD', 'HD-CD 2', 'RHD-DD', 'CA-FM-STA', 'MECH',
                   'SMA',
                   'OSL', 'KYB_PD', 'KYB', 'PD']

    read_sheet_names = list(filter(lambda x: x in sheet_names, T3sheet))
    T3links = []
    for i in read_sheet_names:
        T3link = 'http://10.122.66.105/' + etree.HTML(response.text).xpath(f"//a[text()='{i}']/@href")[0]
        T3links.append(T3link)
    textlinks = [i.replace('viewsec11', 'viewsec12') for i in T3links]

    urls = T3links + textlinks
    return urls


def fetch_url(url):
    userAgent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 " \
                "Safari/537.36 "
    headers = {'User-Agent': userAgent}

    comp_dict = {
        'sid=11': 'BASE-EXTSPKR',
        'sid=81': 'BASE2',
        'sid=13': 'SP',
        'sid=14': 'VA',
        'sid=15': 'CFC-SM',
        'sid=16': 'HD-CD',
        'sid=82': 'HD-CD 2',
        'sid=17': 'RHD-DD',
        'sid=18': 'CA-FM-STA',
        'sid=19': 'MECH',
        'sid=20': 'SMA',
        'sid=24': 'OSL',
        'sid=34': 'KYB_PD',
        'sid=26': 'KYB',
        'sid=27': 'PD'
    }
    session = keep_seesion('T3')
    response = session.get(url, headers=headers)
    comp = comp_dict[url[-6:]]
    print(url)
    if 'viewsec11' in url:
        selectrules = etree.HTML(response.text).xpath("//table[@id='VP_GvSeRuleList']//tr/td[2]/text()")
        deriverules = etree.HTML(response.text).xpath("//table[@id='VP_GvDeRuleList']//tr/td[3]/text()")
        deriveSBB = etree.HTML(response.text).xpath("//table[@id='VP_GvDeRuleList']//tr/td[2]/span/@title")
        deriveSBBrules = [x + ' is ' + y for x, y in zip(deriveSBB, deriverules)]
        data_frames = []
        if selectrules:
            selectrulesDF = pd.DataFrame({
                'rules': selectrules,
                'Component': comp,
                'Type': 'select',
            })
            data_frames.append(selectrulesDF)
        if deriveSBBrules:
            deriveSBBrulesDF = pd.DataFrame({
                'rules': deriveSBBrules,
                'Component': comp,
                'Type': 'derive',
            })
            data_frames.append(deriveSBBrulesDF)
        if data_frames:
            componentTotal = pd.concat(data_frames)
            return componentTotal
    elif 'viewsec12' in url:
        textrules = etree.HTML(response.text).xpath("//*/td[2]/text()")
        if textrules:
            textrulesDF = pd.DataFrame({
                'rules': textrules,
                'Component': comp,
                'Type': 'text rule',
            })
            return textrulesDF