import streamlit as st
import pandas as pd
from py2neo import Graph

# Function to get project names
def get_projectname():
    g = Graph('http://localhost:7474', auth=('neo4j', 'ys1203303'), name='allkg')
    cypher = 'MATCH (n) RETURN n.projectname'
    result = g.run(cypher)
    df = pd.DataFrame(result.data())
    projectname = df['n.projectname'].unique()
    return projectname

# Function to get KG values
def get_KG_value():
    g = Graph('http://localhost:7474', auth=('neo4j', 'ys1203303'), name='allkg')
    cypher = 'MATCH (n) RETURN n.name'
    result = g.run(cypher)
    df = pd.DataFrame(result.data())
    value = df['n.name'].unique()
    return value

# Function to search for rules across projects
def search_rule_cross_project(entity, projectname):
    g = Graph('http://localhost:7474', auth=('neo4j', 'ys1203303'), name='allkg')
    if projectname and projectname != 'All':
        projectname = projectname.replace("(", "\\(").replace(")", "\\)")
    else:
        projectname = ""
    cypher = f"MATCH (n) WHERE n.name =~ '(?i).*{entity}.*' AND n.projectname =~ '(?i).*{projectname}.*' RETURN n.name, n.comments, n.projectname, n.Component, n.owner, n.date"
    result = g.run(cypher)
    df = pd.DataFrame(result.data()).drop_duplicates()
    new_column_names = {'n.name': '部件名称', 'n.comments': '相关规则', 'n.projectname': 'T3名称', 'n.Component': '位于', 'n.owner': '负责人', 'n.date': 'T3日期'}
    df.rename(columns=new_column_names, inplace=True)
    return df

# Streamlit UI
st.title("Knowledge Graph Query Interface")

entity = st.text_input("Enter the entity name:")
projectname = st.selectbox("Select the project name:", ["All"] + list(get_projectname()))

if st.button("Search"):
    result_df = search_rule_cross_project(entity, projectname)
    if isinstance(result_df, pd.DataFrame) and not result_df.empty:
        st.write("Results found:")
        st.dataframe(result_df)
    else:
        st.write("No related components or rules found.")
