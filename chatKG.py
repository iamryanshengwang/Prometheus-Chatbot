import pandas as pd
from py2neo import Graph
from AgentFunction.downloadAVLT3 import Similarity


def search_rule_cross_project(entity, projectname):
    projectname = Similarity(projectname, 't3')
    print(projectname)

    g = Graph('http://10.184.41.18:7474', auth=('neo4j', '12345678'), name='neo4j')
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
        print(df.shape)
        return df
    else:
        print('未找到相关部件或规则')
        return '未找到相关部件或规则'
