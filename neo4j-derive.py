import re
import sqlite3
import pandas as pd
import streamlit as st
from py2neo import Graph, Node, Relationship
def read_derived_rules(column_name):
    query = f"""
    SELECT {column_name} FROM T3_table
    WHERE Type = 'Derive' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%✔%'
    """
    conn = sqlite3.connect('T3.db')
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return [row[0] for row in data if row[0] is not None]
def read_derive_onlyfor_rules():
    query = f"""
    SELECT Component, [Project name], Version, Date, Owner, [OD rules], rules FROM T3_table
    WHERE Type = 'Derive' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%Only for%' AND [OD rules] NOT LIKE '%✔%' """
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
components = read_derived_rules('Component')
project_name = read_derived_rules('[Project name]')
version = read_derived_rules('Version')
date = read_derived_rules('Date')
owner = read_derived_rules('Owner')
OD_rules_raw = read_derived_rules('[OD rules]')
OD_rules = [re.sub(r'\bOnly\b.*', '', rule).strip() for rule in OD_rules_raw]
OD_rules = [re.sub(r'\bSBB\w*\b', '', rule).strip() for rule in OD_rules]
OD_rules = [re.sub(r'[()]', '', rule).strip() for rule in OD_rules]
rules = read_derived_rules('rules')
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
g = Graph('neo4j://localhost:7687', auth = ('neo4j', 'ys1203303'))
g.run("MATCH (n) DETACH DELETE n") 
for i in range(len(components)):
        node1 = Node(
            "parent",
            Name = newrules[i],
            Component = components[i],
            originalRule = rules[i],
            Type = "Derive",
            ProjectName = project_name[i],
            Version = version[i],
            owner = owner[i], 
            date = date[i],
            ruleIndex = OD_rules[i])
        g.create(node1) 
        section_df = df[df['Section_id'] == i + 1] 
        print(section_df) 
        for s, ss in section_df.iterrows():
            node2 = Node(
                "son", 
                Name = ss['name'],
                Component = components[i],
                originalRule = rules[i],
                Type = "Derive",
                ProjectName = project_name[i],
                Version = version[i],
                owner = owner[i], 
                date = date[i],
                ruleIndex = OD_rules[i])
            g.create(node2)
            if ss['Status'] == '✔':
                relationship = Relationship(node2, "should", node1) 
            else:
                relationship = Relationship(node2, "should not", node1) 
            g.create(relationship) 
components1, project_name1, version1, date1, owner1, OD_rules1, rules1 = read_derive_onlyfor_rules()
newrules1 = [line.split(']')[0] for line in rules1]
i = 0
for od in OD_rules1:
    index = od.find(':') 
    after = od[index:].strip()
    after = after.replace(':', '') 
    items = re.split(r'/', after) 
    node1 = Node(
        "parent",
        Name = newrules1[i],
        Component = components1[i],
        originalRule = rules1[i],
        Type = "Derive",
        ProjectName = project_name1[i],
        Version = version1[i],
        owner = owner1[i], 
        date = date1[i],
        ruleIndex = od)
    g.create(node1) 
    for item in items:
        node2 = Node(
            "son", 
            Name = item,
            Component = components1[i],
            originalRule = rules1[i],
            Type = "Derive",
            ProjectName = project_name1[i],
            Version = version1[i],
            owner = owner1[i], 
            date = date1[i],
            ruleIndex = od)
        g.create(node2)
        relationship = Relationship(node2, "should", node1) 
        g.create(relationship) 
    i += 1 
st.title("Neo4j Graph Data")
search_term = st.text_input("Enter search term:")
if search_term:
    query = f"""
    MATCH (n)
    WHERE n.Name CONTAINS '{search_term}'
    RETURN n.Name as Name, n.Component as Component, n.originalRule as OriginalRule, n.Type as Type, n.ProjectName as ProjectName, n.Version as Version, n.owner as Owner, n.date as Date
    """
    result = g.run(query).data()
    if result:
        df = pd.DataFrame(result)
        st.write(df)
    else:
        st.write("No results found")
st.write("Full Graph Data:")
query = """
MATCH (n)
RETURN n.Name as Name, n.Component as Component, n.originalRule as OriginalRule, n.Type as Type, n.ProjectName as ProjectName, n.Version as Version, n.owner as Owner, n.date as Date
"""
result = g.run(query).data()
if result:
    df = pd.DataFrame(result)
    st.write(df)
else:
    st.write("No data found in the graph")