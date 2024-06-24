import pandas as pd
from py2neo import Graph, Node
import re


def build_rels(dfIF, dfTHEN, rule, relShould, projectname):
    dfIFTHEN = pd.concat([dfIF, dfTHEN]).reset_index(drop=True)
    columns = len(dfIFTHEN.columns) - 1

    for k in range(columns):
        relationship_type = 'should' if relShould else 'shouldnot'
        relationship_description = '搭配' if relShould else '不搭配'
        create_relationship(dfIFTHEN.columns[k], dfIFTHEN.columns[k+1], relationship_type, relationship_description, rule, projectname)


def create_relationship(start_node, end_node, rel_type, rel_name, rule, projectname):
    query = "match(p:`%s`),(q:`%s`) where p.ruleIndex=q.ruleIndex AND q.ruleIndex='%s' AND p.projectname=q.projectname='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
        start_node, end_node, rule, projectname, rel_type, rel_name)
    try:
        g.run(query)
    except Exception as e:
        print(e)


def processOD(template, projectname):
    mask = template['OD rules'].str.contains(r"The OD of .*?")
    ODTextRule = template[mask]
    for index, row in ODTextRule.iterrows():
        string = row['OD rules']
        ODcomments = row['rules']
        owner = row['Owner']
        date = row['Date']
        Component = row['Component']

        # print(string)
        ODThen = string.split('is ')
        ODThenSplit = ODThen[1].split(') || (')
        realOD = [ODThen[0] + i for i in ODThenSplit]

        for stringOD in realOD:
            matches = re.findall(r'The OD of \((.*?)\) x', stringOD)
            dfODIF = pd.DataFrame()
            for i in matches:
                data = {i.replace(' ', '_'): [i]}
                dfODIF = pd.DataFrame(data)
                node = Node(dfODIF.columns[0], name=list(dfODIF.iloc[:, 0])[0],
                            Labels=dfODIF.columns[0], ruleIndex=stringOD, originRule=string, projectname=projectname,comments=ODcomments,
                            owner=owner, Component=Component, date=date)
                g.create(node)

            matches = re.findall(r'\$_DT.*?_\$.equals\(".*?"\)', stringOD)
            listOD = []
            for match in matches:
                ODChar = re.findall(r'\$_DT(.*?)_\$', match)
                ODChar = [s.replace('_', ' ').title().replace(' ', '_') for s in ODChar]
                ODVaule = re.findall(r'\((.*?)\)', match)
                ODVaule = [s.replace('"', '') for s in ODVaule]
                dict = {ODChar[0]: ODVaule[0]}
                listOD.append(dict)

            dfODThen = pd.DataFrame()
            result = {}
            for item in listOD:
                key = list(item.keys())[0]
                value = item[key]
                if key in result:
                    result[key].append(value)
                else:
                    result[key] = [value]

            for key, value in result.items():
                df = pd.DataFrame({key: value})
                listV = list(df.values)
                for each in listV:
                    node = Node(df.columns[0], name=each[0], Labels=df.columns[0], ruleIndex=stringOD,
                                originRule=string, projectname=projectname,comments=ODcomments,owner=owner,Component=Component,date=date)
                    g.create(node)
                df = df.explode(key).reset_index(drop=True)
                dfODThen = pd.concat([dfODThen, df]).reset_index(drop=True)
            # print(dfODThen)
            relShould = True
            build_rels(dfODIF, dfODThen, stringOD, relShould, projectname)


def processIfThen(template, projectname):
    def fun1(i):
        dfIF = pd.DataFrame()
        relShould = True
        for j in i:
            key, value = j.split(' is ')
            df = pd.DataFrame({key: value.split(' / ')}).explode(key).reset_index(drop=True)
            column_names = df.columns.tolist()[0]
            listV = list(df.values)
            for each in listV:
                node = Node(column_names, name=each[0], Labels=column_names, ruleIndex=rule, originRule=string3,
                            projectname=projectname, comments=comments,owner=owner,Component=Component,date=date)
                g.create(node)
            dfIF = pd.concat([dfIF, df]).reset_index(drop=True)

        return relShould, dfIF

    def fun2(dfTHEN):
        df = pd.DataFrame({key: value.split(' / ')}).explode(key).reset_index(drop=True)
        column_names = df.columns.tolist()[0]
        listV = list(df.values)
        for each in listV:
            node = Node(column_names, name=each[0], Labels=column_names, ruleIndex=rule, originRule=string3,
                        projectname=projectname, comments=comments,owner=owner,Component=Component,date=date)
            g.create(node)
        dfTHEN = pd.concat([dfTHEN, df]).reset_index(drop=True)
        return dfTHEN

    mask = template['OD rules'].str.contains(r"IF.*?, THEN.*")
    ifThenTextRule = template[mask]
    for index, row in ifThenTextRule.iterrows():
        string3 = row['OD rules']
        comments = row['rules']
        owner = row['Owner']
        date = row['Date']
        Component = row['Component']
        string3 = string3.replace(', AND VICE-VERSA', '') if ', AND VICE-VERSA' in string3 else string3
        # 找到if和then的位置
        if_string = string3[string3.find('IF') + 2:string3.find('THEN')].strip()
        then_string = string3[string3.find('THEN') + 4:].strip()

        # 根据OR进行分割
        if_or_lists = if_string.split(' OR ')
        IFCV = [i.split('AND') for i in if_or_lists]
        IFCV = [[s.replace(',', '').strip() for s in lst] for lst in IFCV]

        then_or_lists = then_string.split(' OR ')
        THENCV = [i.split('AND') for i in then_or_lists]
        THENCV = [[s.replace(',', '').strip() for s in lst] for lst in THENCV]

        splitIFTHEN = []
        for i in if_or_lists:
            for j in then_or_lists:
                splitIFTHEN.append('if ' + i + 'then ' + j)

        count = 0
        if len(THENCV) == 1:
            for i in IFCV:
                rule = splitIFTHEN[count]
                relShould, dfIF = fun1(i)
                dfTHEN = pd.DataFrame()
                for k in THENCV:
                    for o in k:
                        try:
                            key, value = o.split(' should be ')
                        except ValueError:
                            key, value = o.split(' should NOTbe ')
                            relShould = False
                        dfTHEN = fun2(dfTHEN)
                build_rels(dfIF, dfTHEN, rule, relShould,projectname)
                count = count + 1
        else:
            dfTHEN = pd.DataFrame()
            for k in THENCV:
                rule = splitIFTHEN[count]
                for o in k:
                    try:
                        key, value = o.split(' should be ')
                    except ValueError:
                        key, value = o.split(' should NOTbe ')
                        relShould = False
                    dfTHEN = fun2(dfTHEN)

                for i in IFCV:
                    relShould, dfIF = fun1(i)
                build_rels(dfIF, dfTHEN, rule, relShould, projectname)
                count = count + 1


def build_KG():
    global g
    g = Graph('http://10.184.41.18:7474', auth=('neo4j', '12345678'), name='neo4j')
    cypher = '''
    MATCH (n)
    WITH n LIMIT 1000
    DETACH DELETE n
    RETURN count(n) AS remainingNodes
    '''
    result = g.run(cypher).data()[0]["remainingNodes"]
    while result > 0:
        result = g.run(cypher).data()[0]["remainingNodes"]
        print(result)

    sheet = pd.ExcelFile('./T3sqlite/T3 rule total project.xlsx').sheet_names[-1]
    template = pd.read_excel('./T3sqlite/T3 rule total project.xlsx', sheet_name=sheet)
    template = template[template['Type'] == 'Text rule']
    project_list = template['Project name'].unique()
    print(len(project_list))
    for index, projectname in enumerate(project_list[:]):
        try:
            print(index, projectname)
            project_OD_rule = template[template['Project name'] == projectname].copy()
            project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: re.sub(r"SBB.{7}", "", x))
            project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: x.replace('()', ''))
            processIfThen(project_OD_rule, projectname)
            processOD(project_OD_rule, projectname)
        except:
            print('error', index, projectname)


def update_KG(template):
    g = Graph('http://10.184.41.38:7474', auth=('neo4j', '12345678'), name='neo4j')
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
