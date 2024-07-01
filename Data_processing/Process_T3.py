# 用于整理下载下来的t3文档，保留sheet，规则和项目名
import pandas as pd
import os
import re
import sqlite3
import shutil
from openpyxl import load_workbook


def DeriveRule(T3name, read_sheet_names):
    ruleDataFrame = pd.DataFrame()

    excel_data = pd.read_excel(T3name, sheet_name=read_sheet_names, header=1)

    for sheet_name, df in excel_data.items():
        try:
            startRow = df[df['Selectable parts'] == 'derived rules'].index[0] + 1
        except IndexError:
            continue

        try:
            endRow = df[df['Selectable parts'] == 'Text Rules'].index[0] - 2
        except IndexError:
            continue

        nrows = endRow - startRow + 1

        deriveRules = df.iloc[startRow:startRow + nrows, 1:4]
        deriveRules = deriveRules.rename(columns={deriveRules.columns[1]: "info"}).fillna('None')
        deriveRules = deriveRules.rename(columns={deriveRules.columns[2]: "OD rules"}).fillna('None')
        deriveRules['rules'] = deriveRules['Selectable parts'].astype(str) + " is " + deriveRules['info']
        deriveRules.drop(['Selectable parts', 'info'], axis=1, inplace=True)
        deriveRules['Component'] = sheet_name

        ruleDataFrame = pd.concat([ruleDataFrame, deriveRules])

    ruleDataFrame = ruleDataFrame.dropna(axis=0, how='all')
    ruleDataFrame.dropna(subset=['rules'], inplace=True)
    ruleDataFrame = ruleDataFrame[ruleDataFrame['rules'].str.startswith('SBB')]
    ruleDataFrame["rules"] = ruleDataFrame["rules"].str.extract(r'SBB.{10}(.*)')[0]
    ruleDataFrame['Type'] = 'Derive'
    ruleDataFrame = ruleDataFrame.reset_index(drop=True)

    print('DeriveRule Done')

    return ruleDataFrame


def SelectRule(T3name, read_sheet_names):
    ruleDataFrame = pd.DataFrame()

    excel_data = pd.read_excel(T3name, sheet_name=read_sheet_names, header=1)

    for sheet_name, df in excel_data.items():
        try:
            startRow = df[df['Selectable parts'] == 'selectable rules'].index[0] + 1
            try:
                endRow = df[df['Selectable parts'] == 'derived rules'].index[0] - 3
            except IndexError:
                try:
                    endRow = df[df['Selectable parts'] == 'Text Rules'].index[0] - 3
                except IndexError:
                    endRow = len(df)
            nrows = endRow - startRow + 1

            SelectRules = df.iloc[startRow:startRow + nrows, 2:4]
            SelectRules = pd.DataFrame(SelectRules)
            SelectRules['Component'] = sheet_name
            ruleDataFrame = pd.concat([ruleDataFrame, SelectRules])
        except IndexError:
            pass

    ruleDataFrame = ruleDataFrame.rename(columns={ruleDataFrame.columns[0]: "rules"})
    ruleDataFrame = ruleDataFrame.rename(columns={ruleDataFrame.columns[1]: "OD rules"})
    ruleDataFrame['Type'] = 'Select'
    print('SelectRule Done')
    return ruleDataFrame


def TextRule(T3name, read_sheet_names):
    ruleDataFrame = pd.DataFrame()

    excel_data = pd.read_excel(T3name, sheet_name=read_sheet_names, header=1)

    for sheet_name, df in excel_data.items():
        try:
            listTemp = list(df['Selectable parts'])
            index_reverse = listTemp[::-1].index('eCim')
            try:
                startRow = df[df['Selectable parts'] == 'Text Rules'].index[0] + 1
                endRow = len(listTemp) - index_reverse -1
                nrows = endRow - startRow + 1
                if endRow < startRow:
                    continue
                textRules = df.iloc[startRow:startRow + nrows, 2:4]
                textRules['Component'] = sheet_name
                ruleDataFrame = pd.concat([ruleDataFrame, textRules])
            except IndexError:
                pass
        except ValueError:
            pass

    if not ruleDataFrame.empty:
        ruleDataFrame = ruleDataFrame.rename(columns={ruleDataFrame.columns[0]: "rules",ruleDataFrame.columns[1]: "OD rules"})
        ruleDataFrame["rules"] = ruleDataFrame["rules"].apply(lambda x: re.sub(r"SBB.{7}", "", x))
        ruleDataFrame["rules"] = ruleDataFrame["rules"].apply(lambda x: x.replace('()', ''))
        ruleDataFrame["rules"] = ruleDataFrame["rules"].apply(lambda x: x.replace('[Cross-tab]', ''))
        ruleDataFrame = ruleDataFrame.drop_duplicates(subset=['rules'])
        ruleDataFrame['Type'] = 'Text rule'
        print('TextRule Done')

    return ruleDataFrame


def Process_T3(update_date):
    sheet_names = ['BASE-EXTSPKR', 'BASE2', 'SP', 'VA', 'CFC-SM', 'HD-CD', 'HD-CD 2', 'RHD-DD', 'CA-FM-STA', 'MECH', 'SMA',
                   'OSL', 'KYB_PD', 'KYB', 'PD']
    TotalRuleDataFrame = pd.DataFrame()
    path = os.getcwd() + '/T3sqlite/SourceT3list'
    t3 = os.listdir(path)

    for index, i in enumerate(t3, 1):
        print(i)
        T3name = path + "\\" + i

        df = pd.read_excel(T3name, sheet_name=None)
        read_sheet_names = list(filter(lambda x: x in sheet_names, list(df)))

        info = pd.read_excel(T3name, sheet_name='T3 Info')
        info.fillna('None', inplace=True)
        titleDF = info[info['ThinkCentre Template 3'].str.contains('Title')]
        VersionDF = info[info['ThinkCentre Template 3'].str.contains('Version')]
        DateDF = info[info['ThinkCentre Template 3'].str.contains('Date')]
        Owner = info[info['ThinkCentre Template 3'].str.contains('Owner')]

        deriveRule = DeriveRule(T3name, read_sheet_names)
        selectRule = SelectRule(T3name, read_sheet_names)
        textRule = TextRule(T3name, read_sheet_names)
        ruleDataFrame = pd.concat([selectRule, deriveRule, textRule])
        ruleDataFrame = ruleDataFrame.reset_index(drop=True)
        ruleDataFrame = ruleDataFrame.drop_duplicates(subset=['rules'])

        ruleDataFrame['Project name'] = list(titleDF[titleDF.columns[-1]])[0]
        ruleDataFrame['Version'] = list(VersionDF[VersionDF.columns[-1]])[0]
        ruleDataFrame['Date'] = list(DateDF[DateDF.columns[-1]])[0]
        ruleDataFrame['Owner'] = list(Owner[Owner.columns[-1]])[0]

        TotalRuleDataFrame = pd.concat([ruleDataFrame, TotalRuleDataFrame])

    columns = list(TotalRuleDataFrame.columns)
    columns[1], columns[2] = columns[2], columns[1]
    TotalRuleDataFrame = TotalRuleDataFrame[columns]

    locate = './T3sqlite/T3 rule total project.xlsx'
    old_sheet = pd.ExcelFile(locate).sheet_names[-1]
    oldT3rule = pd.read_excel(locate, sheet_name=old_sheet)

    template = oldT3rule[~oldT3rule['Project name'].isin(TotalRuleDataFrame['Project name'])]
    final_template = pd.concat([template, TotalRuleDataFrame], ignore_index=True)

    with pd.ExcelWriter(locate, engine='openpyxl', mode='a') as writer:
        final_template.to_excel(writer, sheet_name=update_date, index=False)

    sheet_names = list(pd.read_excel(locate, sheet_name=None).keys())
    workbook = load_workbook(locate)
    for sheet_name in sheet_names[:-2]:
        workbook.remove(workbook[sheet_name])
    workbook.save(locate)

    # 创建T3 数据库
    conn = sqlite3.connect('./T3sqlite/T3.db')
    final_template.to_sql('T3_table', conn, if_exists='replace', index=False)
    conn.close()

    shutil.rmtree(path)
    os.mkdir(path)
    return TotalRuleDataFrame
