import os
import pymongo
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from collections import defaultdict
import re

from dotenv import load_dotenv

load_dotenv("C:\\Users\\achra\\Downloads\\hackrice-2024\\.env")

def getKnowledgeGraph(topics_input: str, extracted_text: str):
    topics = [topic.strip() for topic in topics_input.split(',')]
    llm_knowledge_graph = ChatOpenAI(model_name="gpt-4o", temperature=0.1)

    topic_graph_prompt_template = PromptTemplate(
        input_variables=["topic_list"],
        template=r"""
    You are a teacher who is going to teach your students particular topics. However, these topics should be taught in a particular order, where some topics should be learned before others. For example, if learning one topic, 'Topic 2', is contingent on a learner having knowledge of another topic, 'Topic 1', then 'Topic 1' should be taught to the learner prior to 'Topic 2'. You are going to be given a list of topics, and should construct a directed graph where each node in this graph is one of the topics that you have been given. You should make a directed edge in this graph (topic1, topic2) where topic1 is prerequisite knowledge for topic2. The edge tail should be topic1 and the edge head should be topic2. Also note that the graph doesn't have to be a connected graph. There can be isolated nodes representing that topic doesn't have any prerequisite knowledge required, and that it isn't a prerequisite for any of the other topics. Your output format is very important, and needs to have the exact same notation every single time that you are given an input on concepts. You should output in mathematical notation a set V that contains the topics that were provided to you and a set E that contains all edges in the directed graph as tuples (topic1, topic2) representing that topic1 should be learned before topic2. Say you have four topics: 'Topic 1', 'Topic 2', 'Topic 3', 'Topic 4'. Your output should be of this format, and have nothing else: V = {{Topic 1, Topic 2, Topic 3, Topic 4}} E = {{(Topic 2, Topic 3), (Topic 2, Topic 1)}}
    Given the following list of topics {topic_list}, give me the output im telling you to do, strictly adhering to the above principles. dont include ANY extra words, just the sets V and E"""
    )
    topic_graph_chain = LLMChain(llm=llm_knowledge_graph, prompt=topic_graph_prompt_template)

    def create_topic_prerequisite_graph(topics):
        topics_str = ", ".join([f"'{topic}'" for topic in topics])
        graph_output = topic_graph_chain.run(topic_list=topics_str)
        graph_output = graph_output.replace("\n", " ")
        return graph_output.strip()

    knowledge_graph = create_topic_prerequisite_graph(topics)

    def parse_gpt_string(gpt_string):
        v_match = re.search(r'V = \{(.+?)\}', gpt_string)
        if v_match:
            v_str = v_match.group(1)
            V = {item.strip() for item in v_str.split(',')}
        else:
            V = set()

        e_match = re.search(r'E = \{(.+?)\}', gpt_string)
        if e_match:
            e_str = e_match.group(1)

            E = re.findall(r'\((.+?)\)', e_str)
            E = {(tuple(map(str.strip, edge.split(',')))) for edge in E}
        else:
            E = set()

        return V, E

    def traverse_graph(vertices, edges):
        ordered_nodes = []
        graph = defaultdict(list)
        in_degree = {vertex: 0 for vertex in vertices}
    
        for parent, child in edges:
            graph[parent].append(child)
            in_degree[child] += 1

        sources = [node for node in vertices if in_degree[node] == 0 and node in graph]
        isolated = [node for node in vertices if in_degree[node] == 0 and node not in graph]
    
        visited = set()

        def traverse(node):
            if node in visited:
                return
            ordered_nodes.append(node)
            visited.add(node)
            for child in graph[node]:
                traverse(child)

        for source in sources:
            traverse(source)

        for node in isolated:
            if node not in visited:
                ordered_nodes.append(node)
                visited.add(node)

        for node in vertices:
            if node not in visited:
                traverse(node)
    
        return ordered_nodes


    V, E = parse_gpt_string(knowledge_graph)
    ordered_nodes = traverse_graph(V, E)
    topics = ordered_nodes

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
    split_texts = text_splitter.split_text(" ".join(extracted_text))

    return (topics, split_texts)