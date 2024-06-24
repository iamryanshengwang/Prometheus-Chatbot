import re
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory, StreamlitChatMessageHistory
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, MessagesPlaceholder, \
    HumanMessagePromptTemplate, AIMessagePromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from Prompt_Design.Extract_Prompt import PN_extract, extract_owner, extract_project
from Prompt_Design.auto_KB_prompt import KB_choice
from chatbot import DocChatbot
import os
import pandas as pd
import streamlit as st
from Data_Process.T3_rule_extract import mainProcessT3
from AgentFunction import searchPN, downloadAVLT3, catchAVL, catchT3, catchOwner, chatKG
from Prompt_Design.Router_Prompt import multiple_choice
from Prompt_Design.QA_Prompt import QA_PROMPT
from Prompt_Design.T3_Prompt import T3_Prompt, T3rule_PROMPT, T3rule


def extract_from_chat_history(system_prompt):
    prompt = ChatPromptTemplate(
        messages=[
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template(
                """
                这是历史对话信息{content}\n\n
                这是用户的最新问题{question}\n\n
                """
            )
        ]
    )
    history_content = ''
    for item in st.session_state.messages:
        if item['role'] == 'assistant':
            if type(item['content']) == str:
                history_content += "assistant: " + item['content'] + "\n"
            else:
                history_content += "assistant: " + "\n"
        else:
            history_content += "user: " + item['content'] + "\n"
    conversation = LLMChain(llm=docChatBot.llm, prompt=prompt)
    response = conversation.predict(question=dialog, content=history_content)
    return response.strip("[]").split(",")[0]


def KB(KBMode):

    st.write(f'You choose {KBMode}knowledge base')
    with st.form(f"Process {KBMode} rule", True):
        docChatBot = DocChatbot()
        submitted = st.form_submit_button(f"Start QA {KBMode} Prometheus")
        if submitted:
            st.session_state["messages"] = [
                {"role": "assistant", "content": f"Hi! I am Prometheus({KBMode}), what can I do for you?😊"}]
            docChatBot.load_vector_db_from_local("./data/vector_store", KBMode)
            st.session_state['docChatBot'] = docChatBot
            docChatBot.init_chatchain(QA_PROMPT)
            docChatBot.memory.clear()


def chatbase():
    if 'docChatBot' not in st.session_state:
        docChatBot = DocChatbot()
        st.session_state.docChatBot = docChatBot
    docChatBot = st.session_state['docChatBot']

    if 'messages' not in st.session_state:
        st.session_state["messages"] = [
            {"role": "assistant", "content": f"Hi! I am Prometheus, what can I do for you?😊"}]
    else:
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

    if user_input := st.chat_input():

        if 'docChatBot' not in st.session_state:
            st.error("Please uploaded a document in the side bar and click the 'Process' button.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)
        answer = docChatBot.chatchain({'question': user_input})
        st.session_state.messages.append({'role': 'assistant', 'content': answer['answer']})
        st.chat_message("assistant").write(answer['answer'])

        with st.chat_message("assistant"):
            i = 0
            with st.expander("References"):
                for doc in answer['source_documents']:
                    source_str = os.path.basename(doc.metadata["source"]) if "source" in doc.metadata else ""
                    page_str = doc.metadata['page'] + 1 if "page" in doc.metadata else ""
                    st.write(f"""### Reference [{i + 1}] {source_str} P{page_str}""")
                    st.write(doc.page_content)
                    i += 1


if __name__ == '__main__':
    st.set_page_config(page_title='Welcome to Prometheus', layout="wide")

    modes = ['Agent Mode','Upload Mode', 'Knowledge Mode', 'Chat Mode']
    with st.sidebar:
        st.title("🤖 Welcome to Prometheus ")
        mode = st.selectbox('Select Modes', modes, key='mode')

    if mode == 'Upload Mode':
        with st.sidebar:
            st.write("👉Please uploaded your engineering documents like AVL/T3/etc.")
            with st.form("Upload and Process", True):
                engineeringmode = ['T3', 'Others']
                modeSelect = st.selectbox('Select Modes', engineeringmode)
                uploaded_file = st.file_uploader("Upload Engineering Documents", type=["pdf", "txt", "docx", 'csv', 'xlsx'], accept_multiple_files=True)
                submitted = st.form_submit_button("Start QA")

                if submitted:
                    if uploaded_file:
                        filelist = []
                        # Save the uploaded file to local
                        for i in uploaded_file:
                            local_file_name = f"""./data/uploaded/{i.name}"""
                            filelist.append(local_file_name)
                            with open(local_file_name, "wb") as f:
                                f.write(i.getbuffer())
                                f.close()

                    with st.spinner("Initializing vector db..."):
                        docChatBot = DocChatbot()
                        if modeSelect == 'AVL':
                            pass
                        elif modeSelect == 'T3':
                            T3filename, T3infolist = mainProcessT3(local_file_name)
                            docChatBot.init_vector_db_from_documents([f'data/uploaded/{T3filename}'])
                            T3_Prompt = T3_Prompt(T3infolist)
                            docChatBot.init_chatchain(T3_Prompt)
                        elif modeSelect == 'Others':
                            docChatBot.init_vector_db_from_documents(filelist)
                            # docChatBot.save_vector_db_to_local("./data/vector_store", 'KB2 M90q Gen3')
                            docChatBot.init_chatchain(QA_PROMPT)
                        st.success("Vector db initialized.")
                        st.balloons()

                    st.session_state['docChatBot'] = docChatBot
                    st.session_state["messages"] = [{"role": "assistant",
                                                     "content": "Hi! I am Prometheus, what can I do for you?😊"}]

            with st.container():
                "😀  [DCDL Link](http://dtdl.lenovo.com/home/index.aspx)"
                "😊  [T3 Link](http://dtdl.lenovo.com/home/index.aspx)"
                "😏  [AVL Link](http://dtdl.lenovo.com/home/index.aspx)"
                "😁  [Buglist Link](http://dtdl.lenovo.com/home/index.aspx)"
        chatbase()

    elif mode == 'Knowledge Mode':
        with st.sidebar:
            # 创建一个下拉框
            option = st.selectbox('Please Select Base', ('T3 KB', 'auto select KB'))
            if option == 'T3 KB':
                KB('T3 KB')
                # chatbase()
            elif option == 'auto select KB':
                st.write(f'You choose auto knowledge base')
                with st.form(f"Process auto rule", True):
                    docChatBot = DocChatbot()
                    submitted = st.form_submit_button(f"Start QA auto Prometheus")
                    if submitted:
                        st.session_state["messages"] = [
                            {"role": "assistant", "content": f"Hi! I am Prometheus(auto), what can I do for you?😊"}]
        if option == 'T3 KB':
            chatbase()
        else:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"], unsafe_allow_html=True)

            docChatBot = DocChatbot()
            if dialog := st.chat_input():
                st.session_state.messages.append({"role": "user", "content": dialog})
                st.chat_message("user").write(dialog)
                response = docChatBot.llm([SystemMessage(content=KB_choice),
                                           HumanMessage(content="M90q Gen1的SS时间是什么时候"),
                                           AIMessage(content='知识库1 SS'),
                                           HumanMessage(content="M90q Gen2的cost是多少"),
                                           AIMessage(content='知识库2 cost'),
                                           HumanMessage(content=dialog)]).content
                print('===start===')
                print('知识库为', response)

                KB_list1 = [f'Knowledge Base {i} SS' for i in range(1,31)]
                KB_list2 = [f'Knowledge Base {i} cost' for i in range(1,31)]

                KB_list = KB_list1+KB_list2

                found = False
                for item in KB_list:
                    if item == response:
                        item = item.replace('Knowledge Base ', 'KB')
                        found = True
                        break
                if found:
                    docChatBot = DocChatbot()
                    docChatBot.load_vector_db_from_local("./data/vector_store", item)
                    st.session_state['docChatBot'] = docChatBot
                    docChatBot.init_chatchain(QA_PROMPT)
                    docChatBot.memory.clear()

                    answer = docChatBot.chatchain({'question': dialog})
                    st.session_state.messages.append({'role': 'assistant', 'content': answer['answer']})
                    st.chat_message("assistant").write(answer['answer'])

                    with st.chat_message("assistant"):
                        i = 0
                        with st.expander("References"):
                            for doc in answer['source_documents']:
                                source_str = os.path.basename(
                                    doc.metadata["source"]) if "source" in doc.metadata else ""
                                page_str = doc.metadata['page'] + 1 if "page" in doc.metadata else ""
                                st.write(f"""### Reference [{i + 1}] {source_str} P{page_str}""")
                                st.write(doc.page_content)
                                i += 1
                else:
                    st.session_state.messages.append({'role': 'assistant', 'content': response})
                    st.chat_message("assistant").write(response)


    elif mode == 'Chat Mode':
        msgs = StreamlitChatMessageHistory(key="special_app_key")
        memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, chat_memory=msgs)
        with st.sidebar:
            with st.form("Chat", True):
                st.write('You can chat with Prometheus!')
                submitted = st.form_submit_button("Start Chat")
                if submitted:
                    memory.clear()
                    st.session_state["messages"] = [
                        {"role": "assistant", "content": f"Hi! I am Prometheus, what can I do for you?😊"}]

        if 'messages' in st.session_state:
            for msg in st.session_state.messages:
                st.chat_message(msg["role"]).write(msg["content"])

        prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(
                    """You are a professional Lenovo Desktop Computing Business Unit (DCBU) AI assistant.Your name is 
                    Prometheus.You realize many knowledge about computer.\n You can only answer questions about the 
                    technology, IT, and computer industries. If the user asks an unrelated question, answer no \n"""
                ),
                MessagesPlaceholder(variable_name="chat_history"),
                HumanMessagePromptTemplate.from_template("{question}")
            ]
        )
        docChatBot = DocChatbot(temperature=0.7)
        conversation = LLMChain(llm=docChatBot.llm, prompt=prompt, memory=memory)
        if dialog := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": dialog})
            st.chat_message("user").write(dialog)
            response = conversation({"question": dialog})
            st.session_state.messages.append({'role': 'assistant', 'content': response['text']})
            st.chat_message("assistant").write(response['text'])

    elif mode == 'Agent Mode':
        with st.sidebar:
            with st.form("Chat", True):
                st.write('You can chat with Prometheus!')
                submitted = st.form_submit_button("Start Chat")
                if submitted:
                    st.session_state["messages"] = [
                        {"role": "assistant", "content": f"Hi! I am Prometheus, what can I do for you?😊"}]

            with st.container():
                "你可以试试："
                "😎  A. 查询PN/SBB信息"
                "😊  B. 查询项目Owner/Owner负责的项目"
                "🤔  C. 查询SBB/PN scope"
                "😏  D. 知识图谱跨T3项目查询规则"
                "😀  E. 查询AVL项目的部件scope"
                "🥳  F. 查询T3项目的规则"
                "😁  G. 查询项目AVL/T3最新链接"

        if 'messages' not in st.session_state:
            st.session_state["messages"] = [{"role": "assistant", "content": f"Hi! I am Prometheus, what can I do for you?😊"}]
        else:
            for msg in st.session_state.messages:
                if type(msg['content']) == list:
                    role_write = st.chat_message(msg["role"])
                    for item in msg['content']: role_write.write(item, unsafe_allow_html=True)
                else:
                    st.chat_message(msg["role"]).write(msg["content"], unsafe_allow_html=True)

        docChatBot = DocChatbot()
        if dialog := st.chat_input():
            st.session_state.messages.append({"role": "user", "content": dialog})
            st.chat_message("user").write(dialog)
            prompt = ChatPromptTemplate(
                messages=[
                    SystemMessagePromptTemplate.from_template(multiple_choice),
                    HumanMessagePromptTemplate.from_template('SBB1234567是什么物料？'),
                    AIMessagePromptTemplate.from_template('[类别A,SBB1234567]'),
                    HumanMessagePromptTemplate.from_template("{question}")
                ]
            )
            conversation = LLMChain(llm=docChatBot.llm, prompt=prompt)
            response = conversation.predict(question=dialog)
            print('===start===')
            result_list = response.strip("[]").split(",")
            print('路由为', response)
            # 查PN信息
            if '类别A' in response:
                PNpattern = r"S.{9}"
                PN = []
                if len(result_list) == 1 or len(result_list[1]) != 10:
                    PN = re.findall(PNpattern, result_list[1])
                    if not PN: PN.append(extract_from_chat_history(PN_extract))
                else:
                    PN.append(result_list[1])
                response = searchPN.SearchPN(PN[0])
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st.chat_message("assistant").write(response, unsafe_allow_html=True)
            # 查owner
            elif '类别B1' in response:
                project = ''
                pattern = r'[a-zA-Z]'
                if len(result_list) == 1 or re.search(pattern, result_list[1]) is None:
                    project = extract_from_chat_history(extract_project)
                else:
                    project = result_list[1]
                response = catchOwner.GetInfo(project)
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st.chat_message("assistant").write(response, unsafe_allow_html=True)
            # 查Project
            elif '类别B2' in response:
                owner_pattern = r'^[a-zA-Z]+[0-9]*$'
                owner = ''
                if len(result_list) == 1 or re.fullmatch(owner_pattern, result_list[1]) is None:
                    owner = extract_from_chat_history(extract_owner)
                else:
                    owner = result_list[1]
                response = catchOwner.GetProjectInfo(owner)
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st.chat_message("assistant").write(response, unsafe_allow_html=True)
            # 查PN 使用scope
            elif '类别C' in response:
                PNpattern = r"S.{9}"
                PN = []
                if len(result_list) == 1 or len(result_list[1]) != 10:
                    PN = re.findall(PNpattern, result_list[1])
                    if not PN:
                        PN.append(extract_from_chat_history(PN_extract))
                else:
                    PN.append(result_list[1])
                response, nums = searchPN.SearchProject(PN[0])
                st.session_state.messages.append({'role': 'assistant',
                                                  'content': [PN[0] + " uses the projectname as below", response,
                                                              "a total of " + str(nums)]})
                assistant_write = st.chat_message("assistant")
                assistant_write.write(PN[0] + " uses the projectname as below")
                assistant_write.write(response, unsafe_allow_html=True)
                assistant_write.write("a total of " + str(nums))
            # 用KG查询
            elif '类别D' in response:
                project = ''
                pattern = r'[a-zA-Z]'
                if len(result_list) < 3 or re.search(pattern, result_list[1]) is None:
                    project = extract_from_chat_history(extract_project)
                else:
                    project = result_list[1]
                response = chatKG.search_rule_cross_project(result_list[2], project)
                st.session_state.messages.append(
                    {'role': 'assistant', 'content': ['用知识图谱查询到的数据如下:', response]})
                if type(response) == pd.DataFrame:
                    with st.chat_message("assistant"):
                        st.write('用知识图谱查询到的数据如下:')
                        st.write(response)
                else:
                    st.chat_message("assistant").write(response, unsafe_allow_html=True)
            # 查AVL部件
            elif '类别E' in response:
                project = ''
                pattern = r'[a-zA-Z]'
                if len(result_list) < 3 or re.search(pattern, result_list[1]) is None:
                    project = extract_from_chat_history(extract_project)
                else:
                    project = result_list[1]
                response = catchAVL.GetPN([project, result_list[2]])
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st_chat_message = st.chat_message("assistant")
                st_chat_message.write(response, unsafe_allow_html=True)
            # 查T3 rule
            elif '类别F' in response:
                docChatBot = DocChatbot()
                response = docChatBot.llm([SystemMessage(content=T3rule_PROMPT), HumanMessage(content=dialog)]).content
                tier2answer = response.strip('[]').replace('，', ',').split(',')
                dialog2 = catchT3.Getprojectname(tier2answer)
                T3rule_PROMPT2 = T3rule(dialog2)
                print(T3rule_PROMPT2)
                response = docChatBot.llm([SystemMessage(content=T3rule_PROMPT2), HumanMessage(content=dialog)]).content
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st.chat_message("assistant").write(response, unsafe_allow_html=True)
            # 下载AVL T3
            elif '类别G' in response:
                project = ''
                pattern = r'[a-zA-Z]'
                if len(result_list) < 3 or re.search(pattern, result_list[1]) is None:
                    project = extract_from_chat_history(extract_project)
                else:
                    project = result_list[1]
                response = downloadAVLT3.GetAVL([project, result_list[2]])
                print(response)
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st.chat_message("assistant").write(response, unsafe_allow_html=True)
            # 闲聊
            else:
                response = docChatBot.llm([SystemMessage(content=QA_PROMPT), HumanMessage(content=dialog)]).content
                print(response)
                st.session_state.messages.append({'role': 'assistant', 'content': response})
                st.chat_message("assistant").write(response, unsafe_allow_html=True)
            print('===finish===')
