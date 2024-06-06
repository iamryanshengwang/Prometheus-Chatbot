import re
import sqlite3
import pandas as pd
import streamlit as st
from py2neo import Graph, Node, Relationship
from multiprocessing import Pool

def execute_query(query, db='T3.db'):
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    return data

def read_derived_rules():
    query = """
    SELECT Component, [Project name], Version, Date, Owner, [OD rules], rules FROM T3_table
    WHERE Type = 'Derive' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%✔%'
    """
    data = execute_query(query)
    components, project_names, versions, dates, owners, OD_rules, rules = zip(*data)
    return components, project_names, versions, dates, owners, OD_rules, rules

def read_derive_onlyfor_rules():
    query = """
    SELECT Component, [Project name], Version, Date, Owner, [OD rules], rules FROM T3_table
    WHERE Type = 'Derive' AND [OD rules] IS NOT NULL AND [OD rules] LIKE '%Only for%' AND [OD rules] NOT LIKE '%✔%'
    """
    data = execute_query(query)
    components, project_names, versions, dates, owners, OD_rules, rules = zip(*data)
    return components, project_names, versions, dates, owners, OD_rules, rules

def create_derived(g, args):
    components, project_names, versions, dates, owners, OD_rules_raw, rules = args
    OD_rules = [re.sub(r'\bOnly\b.*', '', rule).strip() for rule in OD_rules_raw]
    OD_rules = [re.sub(r'\bSBB\w*\b', '', rule).strip() for rule in OD_rules]
    OD_rules = [re.sub(r'[()]', '', rule).strip() for rule in OD_rules]
    newrules = [line.split(']')[0] for line in rules]
    pattern = r'([✔✘])\s*(.*)'

    data = []
    for section_id, section in enumerate(OD_rules, start=1):
        items = re.split(r'\s*\|\|\s*|\s*&&\s*|\s*\(\s*|\s*\)\s*', section)
        for item in items:
            match = re.match(pattern, item)
            if match:
                status, name = match.groups()
                data.append((section_id, status, name))

    df = pd.DataFrame(data, columns=['Section_id', 'Status', 'name'])
    
    for i in range(len(components)):
        node1 = Node(
            "parent",
            Name=newrules[i],
            Component=components[i],
            originalRule=rules[i],
            Type="Derive",
            ProjectName=project_names[i],
            Version=versions[i],
            owner=owners[i], 
            date=dates[i],
            ruleIndex=OD_rules[i]
        )
        g.create(node1)
        
        section_df = df[df['Section_id'] == i + 1]
        for _, ss in section_df.iterrows():
            node2 = Node(
                "son",
                Name=ss['name'],
                Component=components[i],
                originalRule=rules[i],
                Type="Derive",
                ProjectName=project_names[i],
                Version=versions[i],
                owner=owners[i], 
                date=dates[i],
                ruleIndex=OD_rules[i]
            )
            g.create(node2)
            relationship = Relationship(node2, "should" if ss['Status'] == '✔' else "should not", node1)
            g.create(relationship)

def create_only_for(g, args):
    components, project_names, versions, dates, owners, OD_rules, rules = args
    newrules = [line.split(']')[0] for line in rules]

    for i, od in enumerate(OD_rules):
        index = od.find(':')
        after = od[index:].strip().replace(':', '')
        items = re.split(r'/', after)
        
        node1 = Node(
            "parent",
            Name=newrules[i],
            Component=components[i],
            originalRule=rules[i],
            Type="Derive",
            ProjectName=project_names[i],
            Version=versions[i],
            owner=owners[i], 
            date=dates[i],
            ruleIndex=od
        )
        g.create(node1)
        
        for item in items:
            node2 = Node(
                "son",
                Name=item,
                Component=components[i],
                originalRule=rules[i],
                Type="Derive",
                ProjectName=project_names[i],
                Version=versions[i],
                owner=owners[i], 
                date=dates[i],
                ruleIndex=od
            )
            g.create(node2)
            relationship = Relationship(node2, "should", node1)
            g.create(relationship)
            
def streamlit_neo4j():
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
        
def main():
    g = Graph('neo4j://localhost:7687', auth=('neo4j', 'ys1203303'))
    g.run("MATCH (n) DETACH DELETE n")
    derived_rules_args = read_derived_rules()
    onlyfor_rules_args = read_derive_onlyfor_rules()
    create_derived(g, derived_rules_args)
    create_only_for(g, onlyfor_rules_args)
    streamlit_neo4j() 

if __name__ == '__main__':
    main()