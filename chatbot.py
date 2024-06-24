import os
from dotenv import load_dotenv
from typing import List
from langchain import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.document_loaders import (UnstructuredPowerPointLoader, UnstructuredWordDocumentLoader, PyPDFLoader,
                                        UnstructuredFileLoader, UnstructuredExcelLoader, CSVLoader)
from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.memory import ConversationBufferMemory, StreamlitChatMessageHistory
from langchain.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate, SystemMessagePromptTemplate


REQUEST_TIMEOUT = 20


class NoOpLLMChain(LLMChain):
    def __init__(self):
        super().__init__(llm=ChatOpenAI(), prompt=PromptTemplate(template="", input_variables=[]))

    def run(self, question: str, *args, **kwargs) -> str:
        return question


class DocChatbot:
    embeddings: AzureOpenAIEmbeddings
    vector_db: FAISS

    def __init__(self, temperature=0.1) -> None:
        load_dotenv()
        api_key = str(os.getenv("OPENAI_API_KEY"))

        assert (os.getenv("OPENAI_API_KEY") is not None)
        assert (os.getenv("OPENAI_GPT_DEPLOYMENT_NAME") is not None)
        assert (os.getenv("OPENAI_API_BASE") is not None)
        assert (os.getenv("OPENAI_EMBEDDING_DEPLOYMENT_NAME") is not None)
        assert (len(api_key) == 32)

        self.llm = AzureChatOpenAI(
            deployment_name=os.getenv("OPENAI_GPT_DEPLOYMENT_NAME"),
            temperature=temperature,
            openai_api_version="2023-07-01-preview",
            openai_api_type="azure",
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            openai_api_key=api_key,
            request_timeout=REQUEST_TIMEOUT,
        )

        self.embeddings = AzureOpenAIEmbeddings(
            deployment="text-en-ada-002",
            model="text-embedding-ada-002",
            openai_api_base=os.getenv("OPENAI_API_BASE"),
            openai_api_type="azure",
            # chunk_size=16
        )

    def init_chatchain(self, sysprompt,) -> None:
        retriever = self.vector_db.as_retriever()
        msgs = StreamlitChatMessageHistory(key="special_app_key")
        no_op_chain = NoOpLLMChain()
        self.memory = ConversationBufferMemory(memory_key='chat_history', output_key='answer', return_messages=True, chat_memory=msgs)
        self.chatchain = ConversationalRetrievalChain.from_llm(llm=self.llm,
                                                               chain_type="stuff",
                                                               verbose=False,
                                                               memory=self.memory,
                                                               retriever=retriever,
                                                               return_source_documents=True
                                                               )
        self.chatchain.question_generator = no_op_chain
        self.chatchain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate.from_template(sysprompt)
        self.chatchain.combine_docs_chain.llm_chain.prompt.input_variables = ['context', 'question', 'chat_history']

    def load_vector_db_from_local(self, path: str, index_name: str):
        self.vector_db = FAISS.load_local(path, self.embeddings, index_name)
        print(f"Loaded vector db from local: {path}/{index_name}")

    def save_vector_db_to_local(self, path: str, index_name: str):
        FAISS.save_local(self.vector_db, path, index_name)
        print("Vector db saved to local")

    def init_vector_db_from_documents(self, file_list: List[str]):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)

        docs = []
        for file in file_list:
            print(f"Loading file: {file}")
            ext_name = os.path.splitext(file)[-1]

            # if ext_name == ".pptx":
            #     loader = UnstructuredPowerPointLoader(file)
            if ext_name == ".docx":
                loader = UnstructuredWordDocumentLoader(file)
            elif ext_name == ".pdf":
                loader = PyPDFLoader(file)
            # elif ext_name == ".xlsx":
            #     loader = UnstructuredExcelLoader(file)
            elif ext_name == ".csv":
                loader = CSVLoader(file, encoding='utf-8')
            else:
                loader = UnstructuredFileLoader(file)

            doc = loader.load_and_split(text_splitter)
            docs.extend(doc)
            print("Processed document: " + file)

        print("Generating embeddings and ingesting to vector db.")
        self.vector_db = FAISS.from_documents(docs, self.embeddings)
        print("Vector db initialized.")
