import pandas as pd
from py2neo import Graph, Node, Relationship


def get_projectname():
    g = Graph('http://localhost:7474', auth=('neo4j', 'ys1203303'), name='allkg')
    cypher = 'match (n) return n.projectname'
    result = g.run(cypher)
    df = pd.DataFrame(result.data())
    projectname = df['n.projectname'].unique()
    return projectname


# def get_KG_value():
#     g = Graph('http://10.184.41.18:7474', auth=('neo4j', '12345678'), name='neo4j')
#     cypher = 'match (n) return n.name'
#     result = g.run(cypher)
#     df = pd.DataFrame(result.data())
#     value = df['n.name'].unique()
#     return value


# 只是单跳关系
# def search_related_component(entity, projectname):
#     cypher = f"Match (n) -[]-(p) WHERE n.name =~ '(?i).*{entity}.*' AND n.projectname =~ '(?i).*{projectname}.*' return n.comments,p.name, n.projectname"
#     result = g.run(cypher)
#     df = pd.DataFrame(result.data()).drop_duplicates()
#     new_column_names = {'n.comments': '相关规则', 'p.name': '关联部件', 'n.projectname': 'T3名称'}
#     df.rename(columns=new_column_names, inplace=True)
#     print(df.to_markdown(index=False))


def search_rule_cross_project(entity, projectname):
    g = Graph('http://localhost:7474', auth=('neo4j', 'ys1203303'), name='allkg')
    if projectname and projectname != 'All':
        projectname = projectname.replace("(", "\\(").replace(")", "\\)")
    else:
        projectname = ""
    cypher = f"MATCH (n) WHERE n.name =~ '(?i).*{entity}.*' AND n.projectname =~ '(?i).*{projectname}.*' RETURN n.name, n.comments, n.projectname,n.Component,n.owner,n.date"
    result = g.run(cypher)
    df = pd.DataFrame(result.data()).drop_duplicates()
    new_column_names = {'n.name': '部件名称', 'n.comments': '相关规则', 'n.projectname': 'T3名称','n.Component':'位于','n.owner':'负责人','n.date':'T3日期'}
    df.rename(columns=new_column_names, inplace=True)
    if not df.empty:
        # print(f"用知识图谱查询到的数据如下:")
        # print(df.shape)
        return df
    else:
        print('未找到相关部件或规则')
        return '未找到相关部件或规则'