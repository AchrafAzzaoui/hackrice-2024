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

topics_input = input("Enter topics separated by commas: ")
file_path = input("Enter the file path to your PDF: ")

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


extracted_text = []
with pdfplumber.open(file_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text:
            extracted_text.append(text.replace('\n', ' '))

text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=60)
split_texts = text_splitter.split_text(" ".join(extracted_text)) # TODO: THIS IS WHAT WE SEND TO HERE

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

documents = []
user_id = "Wyatt Bellinger"
session = 609

for text_chunk in split_texts:
    embedding = embeddings.embed_query(text_chunk)
    document = {
        'embedding': embedding,
        'text': text_chunk,
        'topics': topics,
        'user_id': user_id,
        'session': session
    }
    documents.append(document)

client = pymongo.MongoClient("mongodb+srv://aa270:Achraf2004**@hackrice-trial-db.v9ye8.mongodb.net/?retryWrites=true&w=majority&appName=Hackrice-Trial-DB")
db = client["test"]
collection = db["pdf_embeddings"]
collection.delete_many({})

vector_store = MongoDBAtlasVectorSearch(collection=collection, embedding=embeddings, index_name='pdf_embeddings')

texts = [doc['text'] for doc in documents]
metadatas = [{'topics': doc['topics'], 'user_id': doc['user_id'], 'session': doc['session']} for doc in documents]
embeddings_list = [doc['embedding'] for doc in documents]

vector_store.add_texts(texts=texts, metadatas=metadatas, embeddings=embeddings_list)

print(f"Added {len(documents)} documents to the vector store.")

llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
memory = ConversationBufferMemory(memory_key="chat_history", input_key="topic", output_key="text")

question_prompt_template = PromptTemplate(
    input_variables=["topic", "context", "chat_history", "evaluation_feedback", "difficulty"],
    template="""
You are an AI tutor helping a student understand the topic "{topic}". You are supposed to act like you are learning from the student,
since teaching is the best way of reinforcing knowledge. IF THE NOTES ARE ABOUT A SPECIFIC PROGRAMMING LANGUAGE, DON'T ASK ABOUT OTHERS.
FOR EXAMPLE, IF ALL THE NOTES ARE ABOUT JAVA ARRAYS, DON'T MENTION PYTHON ARRAYS UNLESS THEY SAID SOMETHING THAT IS RELEVANT TO ANOTHER LANGUAGE BUT DOESN'T WORK IN
THE LANGUAGE IN THE NOTES.

Based on the following context from their notes:
{context}

Considering the conversation so far:
{chat_history}

Here is the evaluation feedback from the previous question:
{evaluation_feedback}

Ask the student one question that assesses their understanding of a {difficulty} concept in this topic, or mention a common misconception and ask them to correct it.

Your question should be clear and concise.
"""
)

evaluation_prompt_template = PromptTemplate(
    input_variables=["topic", "question", "user_answer", "context"],
    template="""
You are an AI tutor evaluating the student's answer.

Topic: {topic}
Question: {question}
Student's Answer: {user_answer}

Based on the context:
{context}

Evaluate the correctness of the student's answer. Provide the following information in JSON format:
1. Degree of correctness (Correct, Partially Correct, Incorrect).
2. Brief explanation of the correctness.
3. Suggestion for the next question difficulty.
4. Provide a clear hint or guidance for the student to improve their answer.
"""
)

hint_prompt_template = PromptTemplate(
    input_variables=["evaluation"],
    template="""
You are an AI that specializes in generating clear and concise hints for students. Based on the evaluation below, extract only the hint that will guide the student toward the correct answer.

Evaluation:
{evaluation}

Provide only the hint.
"""
)


answer_prompt_template = PromptTemplate(
    input_variables=["topic", "question", "context"],
    template="""
You are an AI tutor.

Topic: {topic}
Question: {question}

Based on the context:
{context}

Provide the correct answer to the question.

Your answer should be clear and concise.
"""
)

question_chain = LLMChain(llm=llm, prompt=question_prompt_template, memory=memory)
hint_chain = LLMChain(llm=llm, prompt=hint_prompt_template)
evaluation_chain = LLMChain(llm=llm, prompt=evaluation_prompt_template)
answer_chain = LLMChain(llm=llm, prompt=answer_prompt_template)

#### WE ARE HERE

performance_data = []


for current_topic in topics:
    retriever = vector_store.as_retriever(
        search_kwargs={
            "k": 25,
            "pre_filter": {
                "$and": [
                    {"topics": {"$in": [current_topic]}},
                    {"user_id": user_id},
                    {"session": session}
                ]
            }
        }
    )

    relevant_docs = retriever.get_relevant_documents(current_topic)
    context = "\n".join([doc.page_content for doc in relevant_docs])

    memory.clear()

    print(f"Tutor: Explain {current_topic} to me.")
    user_explanation = input("Your explanation: ").strip()

    while not user_explanation:
        user_explanation = input("Your explanation cannot be empty. Please provide an explanation: ").strip()

    memory.save_context({"topic": current_topic}, {"text": user_explanation})

    difficulty = 'easy'
    evaluation_feedback = "None"

    for question_num in range(1, 3):
        question = question_chain.run(
            topic=current_topic,
            context=context,
            chat_history=memory.load_memory_variables({})["chat_history"],
            evaluation_feedback=evaluation_feedback,  
            difficulty=difficulty
        ).strip()

            

        user_answer = input("Your answer: ").strip()

        while not user_answer:
            user_answer = input("Your answer cannot be empty. Please provide an answer: ").strip()

        memory.save_context({"topic": current_topic}, {"text": question})
        memory.save_context({"topic": current_topic}, {"text": user_answer})

        evaluation = evaluation_chain.run(
            topic=current_topic,
            question=question,
            user_answer=user_answer,
            context=context
        ).strip()

        print(f"Tutor Feedback: {evaluation}")

        evaluation_feedback = evaluation

        if 'Incorrect' in evaluation or 'Partially Correct' in evaluation:
            print("Tutor: Would you like to try again with a hint, or see the correct answer?")
            print("1. Re-answer with hint")
            print("2. See the correct answer")
            choice = input("Enter 1 or 2: ").strip()

            while choice not in ['1', '2']:
                choice = input("Invalid choice. Please enter 1 or 2: ").strip()

            if choice == '1':
                hint = hint_chain.run(evaluation=evaluation).strip()
                print(f"Tutor Hint: {hint}")

                user_answer_2 = input("Your new answer: ").strip()

                while not user_answer_2:
                    user_answer_2 = input("Your answer cannot be empty. Please provide an answer: ").strip()

                memory.save_context({"topic": current_topic}, {"text": user_answer_2})

                evaluation_2 = evaluation_chain.run(
                    topic=current_topic,
                    question=question,
                    user_answer=user_answer_2,
                    context=context
                ).strip()

                print(f"Tutor Feedback: {evaluation_2}")

                difficulty = 'harder' if 'Correct' in evaluation_2 else 'easier'
                evaluation_feedback = evaluation_2
            else:
                correct_answer = answer_chain.run(
                    topic=current_topic,
                    question=question,
                    context=context
                ).strip()
                print(f"Tutor: The correct answer is: {correct_answer}")

                difficulty = 'easier'
        else:
            if 'Correct' in evaluation:
                difficulty = 'harder'
            else:
                difficulty = 'same'

    print(f"Finished topic: {current_topic}\n")



import json
import re

llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

mastery_prompt_template = PromptTemplate(
    input_variables=["performance_data"],
    template="""
You are an AI that analyzes student performance data and maps topics to mastery scores.
Given the following performance data, generate a dictionary that maps each topic to:
1. A mastery score from 0 to 100 based on the student's answers, attempts, correctness, and skipped questions, averaged across all questions in the topic.
2. Subtopics they need to practice based on hints and explanations provided in the evaluation.

The performance data is formatted as follows:
{performance_data}

Guidelines for mastery scoring:
- Correct on the first attempt: 90 mastery.
- Correct on the second attempt: 70 mastery.
- Partially correct answers: 50 mastery.
- Incorrect answers or skipped questions with no partial credit: 30 mastery.

Calculate the average mastery for each topic based on all related questions. Also, extract relevant subtopics from the hint or guidance provided in the evaluation.

Output ONLY the result dictionary in the following format, with no additional text or explanation:
{{
  "topic_name": {{
    "mastery": <average mastery score from 0 to 100>,
    "subtopics_to_practice": ["list of subtopics extracted from the hints or guidance"]
  }}
}}

Ensure that the subtopics are concise and directly related to the hints provided.
"""
)


mastery_chain = LLMChain(llm=llm, prompt=mastery_prompt_template)

performance_data_json = json.dumps(performance_data, indent=2)

result = mastery_chain.run(performance_data=performance_data_json)

dictionary_match = re.search(r'\{[^{}]*\{[^{}]*\}[^{}]*\}', result)
if dictionary_match:
    dictionary_result = dictionary_match.group(0)
    mastery_mapping = json.loads(dictionary_result)
else:
    mastery_mapping = {}
    print("No valid dictionary found in the output.")

topic_mastery = json.dumps(mastery_mapping, indent=2)
print(topic_mastery)