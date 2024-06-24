from Prompt_Design import QA_Prompt


def T3_Prompt(infolist):
    projectname = infolist[0]
    version = infolist[1]
    date = infolist[2]
    owner = infolist[3]
    T3_Prompt = f'这是一份项目名为{projectname}的T3文档，格式为csv格式，版本为{version}，发布日期为{date}，T3 owner是{owner},由他负责,T3文档表示了该台式机项目存在如下部件组装规则\n' + QA_Prompt.QA_PROMPT
    return T3_Prompt


T3rule_PROMPT = """请提取用户问题中的项目名称。
例子：
用户提问关于M800T的cpu规则是什么。
用户提问关于P900的HDD规则。
提取出的项目名称和系统类别分别是：
M800T
P900
请以[项目名称]的格式输出,只需要项目名称，不需要其他内容
"""

def T3rule(T3rule):
    T3rule_PROMPT2 = f"""以下是一份关于联想台式机的T3文档，T3文档是限制电脑各个部件之间搭配关系的文档。
    以下规则是通过csv格式展现的，请分析这份T3文档，回答用户问题
    {T3rule}
    """
    return T3rule_PROMPT2