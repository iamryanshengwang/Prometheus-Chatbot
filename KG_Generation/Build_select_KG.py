import re
import sqlite3
import pandas as pd
from py2neo import Graph, Node, Relationship


def read_select_rules():
    query = f"""
    SELECT Component, [Project name], Version, Date, Owner, [OD rules], rules FROM T3_table
    WHERE Type = 'Select' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%if%' AND [OD rules] LIKE '%Assertion%'"""
    conn = sqlite3.connect('T3.db')
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    components = [row[0] for row in data if row[0] is not None]
    project_names = [row[1] for row in data if row[1] is not None]
    versions = [row[2] for row in data if row[2] is not None]
    dates = [row[3] for row in data if row[3] is not None]
    owners = [row[4] for row in data if row[4] is not None]
    OD_rules = [row[5] for row in data if row[5] is not None]
    rules = [row[6] for row in data if row[6] is not None]
    return components, project_names, versions, dates, owners, OD_rules, rules


components, project_name, version, date, owner, OD_rules, rules = read_select_rules()
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
g = Graph('neo4j://localhost:7687', auth = ('neo4j', '12345678'))
g.run("MATCH (n) DETACH DELETE n")
print(len(components))
for i in range(len(components)):
    if i%100 == 0:
        print(i)
    sec_df = df2[df2['Section_id'] == i + 1]
    for a, aa in sec_df.iterrows():
        node1 = Node(
            "Parent",
            name = aa['name2'],
            Component = components[i],
            originalRule = rules[i],
            Type = "Select",
            projectname = project_name[i],
            Version = version[i],
            owner = owner[i],
            date = date[i],
            ruleIndex = OD_rules[i])
        g.create(node1)
        section_df = df1[df1['Section_id'] == i + 1]
        for s, ss in section_df.iterrows():
            node2 = Node(
                "Child",
                name = ss['name1'],
                Component = components[i],
                originalRule = rules[i],
                Type = "Select",
                projectname = project_name[i],
                Version = version[i],
                owner = owner[i],
                date = date[i],
                ruleIndex = OD_rules[i])
            g.create(node2)
            if ss['Status1'] == '✔':
                relationship = Relationship(node2, "should", node1)
            else:
                relationship = Relationship(node2, "should not", node1)
            g.create(relationship)