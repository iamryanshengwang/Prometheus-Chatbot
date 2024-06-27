import re
import sqlite3
import pandas as pd
from py2neo import Graph, Node, Relationship

def read_derived_rules(conn, column_name):
    query = f"""
    SELECT {column_name} FROM T3_table
    WHERE Type = 'Derive' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%✔%'
    """
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    return [row[0] for row in data if row[0] is not None]

def read_derive_onlyfor_rules(conn):
    query = f"""
    SELECT Component, [Project name], Version, Date, Owner, [OD rules], rules FROM T3_table
    WHERE Type = 'Derive' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%Only for%' AND [OD rules] NOT LIKE '%✔%' """
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    components = [row[0] for row in data if row[0] is not None]
    project_names = [row[1] for row in data if row[1] is not None]
    versions = [row[2] for row in data if row[2] is not None]
    dates = [row[3] for row in data if row[3] is not None]
    owners = [row[4] for row in data if row[4] is not None]
    OD_rules = [row[5] for row in data if row[5] is not None]
    rules = [row[6] for row in data if row[6] is not None]
    return components, project_names, versions, dates, owners, OD_rules, rules

def build_derived_KG(conn):
    components = read_derived_rules(conn, 'Component')
    project_name = read_derived_rules(conn, '[Project name]')
    version = read_derived_rules(conn, 'Version')
    date = read_derived_rules(conn, 'Date')
    owner = read_derived_rules(conn, 'Owner')
    OD_rules_raw = read_derived_rules(conn, '[OD rules]')
    OD_rules = [re.sub(r'\bOnly\b.*', '', rule).strip() for rule in OD_rules_raw]
    OD_rules = [re.sub(r'\bSBB\w*\b', '', rule).strip() for rule in OD_rules]
    OD_rules = [re.sub(r'[()]', '', rule).strip() for rule in OD_rules]
    rules = read_derived_rules(conn, 'rules')
    newrules = [line.split(']')[0] for line in rules]
    pattern = r'([✔✘])\s*(.*)'
    data = []
    section_id = 1
    for section in OD_rules:
        items = re.split(r'\s*\|\|\s*|\s*&&\s*|\s*\(\s*|\s*\)\s*', section)
        section_data = []
        for item in items:
            match = re.match(pattern, item)
            if match:
                status, name = match.groups()
                section_data.append((section_id, status, name))
        if section_data:
            data.extend(section_data)
        section_id += 1
    df = pd.DataFrame(data, columns=['Section_id', 'Status', 'name'])

    for i in range(len(components)):
        node1 = Node(
            "Parent",
            Name=newrules[i],
            Component=components[i],
            originalRule=rules[i],
            Type="Derive",
            ProjectName=project_name[i],
            Version=version[i],
            owner=owner[i],
            date=date[i],
            ruleIndex=OD_rules[i])
        g.create(node1)
        section_df = df[df['Section_id'] == i + 1]
        print(section_df)
        for s, ss in section_df.iterrows():
            node2 = Node(
                "Child",
                Name=ss['name'],
                Component=components[i],
                originalRule=rules[i],
                Type="Derive",
                ProjectName=project_name[i],
                Version=version[i],
                owner=owner[i],
                date=date[i],
                ruleIndex=OD_rules[i])
            g.create(node2)
            if ss['Status'] == '✔':
                relationship = Relationship(node2, "should", node1)
            else:
                relationship = Relationship(node2, "should not", node1)
            g.create(relationship)

def build_only_for_KG(conn):
    components1, project_name1, version1, date1, owner1, OD_rules1, rules1 = read_derive_onlyfor_rules(conn)
    newrules1 = [line.split(']')[0] for line in rules1]
    i = 0
    print(len(OD_rules1))
    for num, od in enumerate(OD_rules1):
        if num % 100 == 0:
            print(num)
        index = od.find(':')
        after = od[index:].strip()
        after = after.replace(':', '')
        items = re.split(r'/', after)
        node1 = Node(
            "Parent",
            name = newrules1[i],
            Component = components1[i],
            originalRule = rules1[i],
            comments=rules1[i],
            Type = "Derive",
            projectname = project_name1[i],
            owner = owner1[i],
            date = date1[i],
            ruleIndex = od)
        g.create(node1)
        for item in items:
            node2 = Node(
                "Child",
                name = item,
                Component = components1[i],
                originalRule = rules1[i],
                comments = rules1[i],
                Type = "Derive",
                projectname = project_name1[i],
                owner = owner1[i],
                date = date1[i],
                ruleIndex = od)
            g.create(node2)
            relationship = Relationship(node2, "should", node1)
            g.create(relationship)
        i += 1

def read_select_rules(conn):
    query = f"""
    SELECT Component, [Project name], Version, Date, Owner, [OD rules], rules FROM T3_table
    WHERE Type = 'Select' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%if%' AND [OD rules] LIKE '%Assertion%'"""
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    components = [row[0] for row in data if row[0] is not None]
    project_names = [row[1] for row in data if row[1] is not None]
    versions = [row[2] for row in data if row[2] is not None]
    dates = [row[3] for row in data if row[3] is not None]
    owners = [row[4] for row in data if row[4] is not None]
    OD_rules = [row[5] for row in data if row[5] is not None]
    rules = [row[6] for row in data if row[6] is not None]
    return components, project_names, versions, dates, owners, OD_rules, rules

def build_select_KG(conn):
    components, project_name, version, date, owner, OD_rules, rules = read_select_rules(conn)
    OD_rules = [re.sub(r'\bSBB\w*\b', '', rule).strip() for rule in OD_rules]
    pattern = r'([✔✘])\s*(.*)'
    data = []
    data2 = []
    section_id = 1
    for section in OD_rules:
        section = section.replace('Assertion --', '')
        section = section.replace('(', '')
        section_data = []
        if_data = []
        if_index = section.find(", if")
        before_if = section[:if_index].strip()
        after_if = section[if_index:].strip()
        befores = re.split(r'\s*\|\|\s*|\s*&&\s*', before_if)
        after_if = after_if.replace(", if", '')
        afters = re.split(r'\s*\|\|\s*|\s*&&\s*', after_if)
        for before in befores:
            match1 = re.match(pattern, before)
            if match1:
                status1, name1 = match1.groups()
                name1 = name1.replace(')', '')
                name1 = name1.replace('(', '')
                section_data.append((section_id, status1, name1))
        for after in afters:
            match2 = re.match(pattern, after)
            if match2:
                status2, name2 = match2.groups()
                name2 = name2.replace(')', '')
                name2 = name2.replace('(', '')
                if_data.append((section_id, status2, name2))
        if section_data:
            data.extend(section_data)
        if if_data:
            data2.extend(if_data)
        section_id += 1
    df1 = pd.DataFrame(data, columns=['Section_id', 'Status1', 'name1'])
    df2 = pd.DataFrame(data2, columns=['Section_id', 'Status2', 'name2'])
    OD_rules = [re.sub(r'[()]', '', rule).strip() for rule in OD_rules]
    print(len(components))
    for i in range(len(components)):
        if i % 100 == 0:
            print(i)
        sec_df = df2[df2['Section_id'] == i + 1]
        for a, aa in sec_df.iterrows():
            node1 = Node(
                "Parent",
                name=aa['name2'],
                Component=components[i],
                originalRule=rules[i],
                Type="Select",
                projectname=project_name[i],
                Version=version[i],
                owner=owner[i],
                date=date[i],
                ruleIndex=OD_rules[i])
            g.create(node1)
            section_df = df1[df1['Section_id'] == i + 1]
            for s, ss in section_df.iterrows():
                node2 = Node(
                    "Child",
                    name=ss['name1'],
                    Component=components[i],
                    originalRule=rules[i],
                    Type="Select",
                    projectname=project_name[i],
                    Version=version[i],
                    owner=owner[i],
                    date=date[i],
                    ruleIndex=OD_rules[i])
                g.create(node2)
                if ss['Status1'] == '✔':
                    relationship = Relationship(node2, "should", node1)
                else:
                    relationship = Relationship(node2, "should not", node1)
                g.create(relationship)

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

def build_textrule_KG(conn):
    query = "SELECT * FROM [T3_table] WHERE [Type] = 'Text rule'"
    template = pd.read_sql_query(query, conn)
    project_list = template['Project name'].unique()
    print(len(project_list))

    for index, projectname in enumerate(project_list[:]):
        # try:
        #     print(index, projectname)
        #     project_OD_rule = template[template['Project name'] == projectname].copy()
        #     project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: re.sub(r"SBB.{7}", "", x))
        #     project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: x.replace('()', ''))
        #     processIfThen(project_OD_rule, projectname)
        #     processOD(project_OD_rule, projectname)
        # except:
        #     print('error', index, projectname)
        print(index, projectname)
        project_OD_rule = template[template['Project name'] == projectname].copy()
        project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: re.sub(r"SBB.{7}", "", x))
        project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: x.replace('()', ''))
        processIfThen(project_OD_rule, projectname)
        processOD(project_OD_rule, projectname)

# def update_KG(template):
#     g = Graph('http://10.184.41.38:7474', auth=('neo4j', '12345678'), name='neo4j')
#     template = template[template['Type'] == 'Text rule']
#     project_list = template['Project name'].unique()
#     print(len(project_list))
#     for index, projectname in enumerate(project_list[:]):
#         cypher = f"MATCH (n)-[r]-() WHERE n.projectname = '{projectname}' DELETE r, n"
#         g.run(cypher)
#         try:
#             project_OD_rule = template[template['Project name'] == projectname].copy()
#             project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: re.sub(r"SBB.{7}", "", x))
#             project_OD_rule["OD rules"] = project_OD_rule["OD rules"].apply(lambda x: x.replace('()', ''))
#             processIfThen(project_OD_rule, projectname)
#             processOD(project_OD_rule, projectname)
#             print(index, projectname)
#         except Exception as e:
#             print('error', index, projectname)
#             print(e)

if __name__ == '__main__':
    # g = Graph('http://10.184.41.18:7474', auth=('neo4j', '12345678'), name='neo4j')
    g = Graph('http://localhost:7474', auth=('neo4j', 'ys1203303'), name = 'allkg')
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
    conn = sqlite3.connect(r'T3.db')
    build_textrule_KG(conn)
    build_only_for_KG(conn)
    build_derived_KG(conn)
    build_select_KG(conn)
    conn.close
