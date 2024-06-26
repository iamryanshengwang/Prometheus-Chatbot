# multiple_choice = '''
# 为了更好地解决用户的问题，你需要针对不同类别的用户问题抽取出关键信息，下面是类别选项以及用户的问题形式，
# 类别A：用户查询物料编码(PN)是什么物料。物料编码(PN)是一个长度为10位的以S或SBB开始的英文数字串。用户可能的提问方式有："xxxxxxxxxx是什么"或"xxxxxxxxxx是什么物料"等，请你结合上下文信息返回该物料PN，输出格式：[类别A,xxxxxxxxxx],
# 类别B：用户查询某个项目是谁负责的，或者谁负责什么项目，用户可能的提问方式有："xx项目的owner是谁"或"xx项目是谁在看"或"xx项目是谁负责"或"xxx看什么项目"等，请你结合上下文信息返回负责人名称或者项目名称，输入格式：[类别B,项目名称]或[类别B,负责人名称],
# 类别C：用户查询物料编码(PN)在什么项目上使用。物料编码(PN)是一个长度为10位的以S或SBB开始的英文数字串。用户可能的提问方式有："xxxxxxxxxx的使用情况"或"xxxxxxxxxx在什么项目上使用"等，请你结合上下文信息返回该物料PN，输出格式：[类别C,xxxxxxxxxx],
# 类别D：用户查询某个项目的某个部件的T3规则，或者部件搭配问题，该查询会用到知识图谱，强调规则和限制以及知识图谱的使用，用户可能的提问方式有："告诉我xx项目的cpu rule"或"xx项目的HDD的T3规则是什么"或"180W能不能上6400"等，请你结合上下文信息返回项目名称和部件名称，用户可能只说明了项目名称或者只说明了部件名称，这时候，请返回对应名称为空字符串，输出格式：[类别D,项目名称,部件名称],
# 类别E：用户查询项目中的以下等部件：主板、CPU、内存条、硬盘、ODD、读卡器、显卡、wifi、外插卡、Base、电源、包材、Label、COPT等等。用户可能提问的方式有："告诉我xx项目的显卡有哪些"或"xx项目的读卡器料号是什么"或"xx项目的CPU scope"或"xx项目上了什么内存"等，请你结合上下文信息返回项目名称和部件名称，输出格式：[类别E,项目名称,部件名称],
# 类别G：用户想要下载所需项目的AVL或者T3文档，注意！你不需要下载文件，请你结合上下文信息返回项目名称和系统类别，系统类别只有AVL和T3两种，输出格式：[类别G,项目名称,系统类别],
# 类别Z：其他，如果用户提供的信息不够清晰，或者查询意图不够明确，类别A到类别G的全部类别都不满足时，选择此类别, 请你结合上下文信息返回用户问题，输出格式：[类别Z,用户问题]
# '''

multiple_choice = '''
用户会围绕PN编码、项目名称、负责人名称、部件名称这四个关键信息提出几类问题，你的任务是将用户的问题进行分类，并针对不同类别的用户问题抽取出上面提到的关键信息，
PN编码是一个以S开头，长度为10的英文数字字符串，例如：SA31C41403。
项目名称多种多样，例如：扬天490、90t gen5、QT660等等。
负责人名称是人名汉语拼音或拼音缩写，可能带有数字后缀，例如：huanghx11。
部件名称可能是具体的部件名称例如：6400、3050等等，也可能是抽象的部件名称例如：显卡、CPU等等。
接下来是问题的分类，以及要抽取以上的哪几种关键信息。
类别A：用户查询物料编码(PN)的信息。用户可能的提问方式有："xxxxxxxxxx是什么"或"xxxxxxxxxx是什么物料"或"上面的PN是什么物料"等，该类问题中用户会提供具体的PN编码或明确的提到“PN”或“编码”这一关键词，输出格式：[类别A,xxxxxxxxxx],
类别B1：用户查询某个项目的负责人名称，用户可能的提问方式有："xx项目的owner是谁"或"xx项目是谁在看"或"xx项目是谁负责"或"上面的项目是谁负责"或"这个项目是在看"等，该类问题中用户会提供具体的项目名称或明确的提到“项目”这一关键词，输入格式：[类别B1,项目名称],
类别B2：用户查询负责人名称负责的项目名称，用户可能的提问方式有："xxx看什么项目"或"他还负责哪些项目"等，该类问题中用户会提供具体的责任人名称或明确的提到人称代词这一关键词，输出格式：[类别B2,负责人名称],
类别C：用户查询物料编码(PN)在什么项目上使用，用户可能的提问方式有："xxxxxxxxxx的使用情况"或"xxxxxxxxxx在什么项目上使用"或"上面的PN在什么项目上使用"等，该类问题中用户会提供具体的PN编码或明确的提到“PN”或“编码”这一关键词，输出格式：[类别C,xxxxxxxxxx],
类别D：用户查询某个项目和某个部件的T3规则或搭配问题，用户可能的提问方式有："告诉我xx项目的cpu rule"或"xx项目的HDD的T3规则是什么"或"180W能不能上6400"等，该类问题中用户会提供具体的项目名称和部件名称，强调知识图谱的使用和规则的限制，输出格式：[类别D,项目名称,部件名称],
类别E：用户查询某个项目中的抽象部件具体是哪些，抽象部件的描述为以下中的一种：主板、CPU、内存条、硬盘、ODD、读卡器、显卡、wifi、外插卡、Base、电源、包材、Label、COPT。用户可能提问的方式有："告诉我xx项目的显卡有哪些"或"xx项目的读卡器料号是什么"或"xx项目的CPU scope"或"xx项目上了什么内存"等，输出格式：[类别E,项目名称,部件名称],
类别G：用户想要下载所需项目的AVL或者T3文档，注意！你不需要下载文件，请你项目名称和系统类别即可，系统类别只有AVL和T3两种，用户可能的提问方式有："帮我下载一份它的AVL"或"下载一个xx项目的T3"，该类问题中用户会提供具体的项目名称或明确的提到“下载”这一关键词，输出格式：[类别G,项目名称,系统类别],
类别Z：其他，如果类别A到类别G的全部类别都完全不能满足时，选择此类别, 请直接返回用户问题，输出格式：[类别Z,用户问题]
'''

# multiple_choice = '''
# 用户会围绕PN编码、项目名称、负责人名称、部件名称这四个信息提出几类问题，你的任务是将用户的问题进行分类，
# PN编码是一个以S开头，长度为10的英文数字字符串，例如：SA31C41403。
# 项目名称多种多样，例如：扬天490、90t gen5、QT660等等。
# 负责人名称是人名汉语拼音或拼音缩写，可能带有数字后缀，例如：huanghx11。
# 部件名称可能是具体的部件名称例如：6400、3050等等，也可能是抽象的部件名称例如：显卡、CPU等等。
# 接下来是问题的分类，以及要抽取以上的哪几种关键信息。
# 类别A：用户查询物料编码(PN)的信息。输出格式：[类别A],
# 类别B1：用户查询某个项目的负责人名称。输出格式：[类别B1],
# 类别B2：用户查询负责人名称负责的项目名称。输出格式：[类别B2],
# 类别C：用户查询物料编码(PN)在什么项目上使用。输出格式：[类别C],
# 类别D：用户查询某个项目和某个部件的T3规则或搭配问题。输出格式：[类别D],
# 类别E：用户查询某个项目中的抽象部件具体是哪些，抽象部件的描述为以下中的一种：主板、CPU、内存条、硬盘、ODD、读卡器、显卡、wifi、外插卡、Base、电源、包材、Label、COPT。输出格式：[类别E],
# 类别G：用户想要下载所需项目的AVL或者T3文档，注意！你不需要下载文件，请你项目名称和系统类别即可，系统类别只有AVL和T3两种。输出格式：[类别G],
# 类别Z：其他，如果类别A到类别G的全部类别都完全不一致时，选择此类别。输出格式：[类别Z]
# '''
