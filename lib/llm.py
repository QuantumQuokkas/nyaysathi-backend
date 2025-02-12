from dotenv import load_dotenv
import os

from openai import OpenAI
from langchain.llms import OpenAI as openai
from langchain.chains import RetrievalQA

from lib.utils import getDataChunks, createKnowledgeHub

ResponsePrompt = """Consider you are a legal advisor based in India. Your day to day job is to reply to legal queries in the most simplified language possible by using least words. Make sure the reader of the response might not understand legal jargons so avoid difficult language. You can mention laws, acts, sections, subsections applicable in your response for the sake of reference or to support the accuraccy of your response. At the end of the response also mention the punishments given in the laws for the action if any (optional).

Answer the question using the given knowledge hub as a part of the retriver. Do not answer the question if you are not sure about the answer, just reply with "I am not sure about this". If the question is in hindi reply in hindi and if the question is in english reply in english. Do not mix the languages. If the question is in a different language other than hindi or english reply with "I can only understand English and Hindi.".

"""

ActPrompt = """Based on the below question can you give the law, act, section, subsection assosciated with it in context with the indian judicial system. get me the response strictly in 2 - 3 words. do not format the response in a list or any other format. just give me the response in plain text. Do not add any sections, subsections or specific laws.

"""

client = OpenAI(api_key=os.getenv("OPENAI_KEY"), organization=os.getenv("ORG"))

def generateResponse(text, question):
    chunks = getDataChunks(text)
    knowledge_hub = createKnowledgeHub(chunks)
    retriever = knowledge_hub.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    
    chain = RetrievalQA.from_chain_type(
        llm=openai(api_key=os.getenv("OPENAI_KEY"), organization=os.getenv("ORG"), temperature=0.6, model_name="gpt-3.5-turbo-instruct", max_tokens=600),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
    
    result = chain({"query": ResponsePrompt + "Question: " + question})
    return result['result']

def generateChatResponse(text, previousContext, followUpQuestion):
    chunks = getDataChunks(text)
    knowledge_hub = createKnowledgeHub(chunks)
    retriever = knowledge_hub.as_retriever(search_type="similarity", search_kwargs={"k": 2})
    
    chain = RetrievalQA.from_chain_type(
        llm=openai(api_key=os.getenv("OPENAI_KEY"), organization=os.getenv("ORG"), temperature=0.6, model_name="gpt-3.5-turbo-instruct", max_tokens=600),
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
    
    result = chain({"query": ResponsePrompt + "Previous Context: " + previousContext + "\n\nQuestion: " + followUpQuestion})
    return result['result']

def getAct(question):    
    response = client.completions.create(
      model = "gpt-3.5-turbo-instruct",
      prompt = ActPrompt + question,
      max_tokens=50,
    )
    return response.choices[0].text

def visionOCR(imgs):
    msg = [
        {
        "role": "user",
        "content": [
            {"type": "text", "text": "Detect the language and return the exact text from the image."},
        ],
        }
    ]
    
    for img in imgs:
        msg[0]['content'].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{img}",
            },
        })
    
    response = client.chat.completions.create(
    model="gpt-4-vision-preview",
    messages=msg,
    max_tokens=300,
    )

    return response.choices[0].message.content

def SummarizeLegalText(text):
    response = client.completions.create(
        model = "gpt-3.5-turbo-instruct",
        prompt = "Summarize the given text in brief. If there is anything important which should be represented as it is do so, other than that try to simplify the difficult language in the simplest terms. Do not add anything from your own.\n\n" + text,
        max_tokens=700,
    )
    return response.choices[0].text