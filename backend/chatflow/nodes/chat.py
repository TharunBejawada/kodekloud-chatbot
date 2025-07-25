def chat_node(state):
    from utils.embeddings import get_embedding, cosine_similarity
    from rag.neo4j_loader import get_topic_embedding_from_neo4j

    user_input = state["user_input"]
    guide_steps = state.get("guide", [])
    topic = state["topic"]

    # Recheck similarity with topic before proceeding
    user_vec = get_embedding(user_input)
    topic_vec = get_topic_embedding_from_neo4j(topic)
    similarity = cosine_similarity(user_vec, topic_vec)
    state["similarity"] = similarity

    print(f"🔁 Rechecking similarity in chat_node: {similarity:.4f}")

    if similarity < 0.85:
        if "response" not in state:
            state["response"] = f"Let's stick to the topic you're learning: '{topic}'. Please ask related questions."
        return state

    if not guide_steps:
        state["response"] = "Sorry, no guide found to answer your question."
        return state

    # Build retriever
    from langchain_community.embeddings import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain_community.chat_models import ChatOpenAI
    from langchain.chains import RetrievalQA
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document

    documents = [
        Document(page_content=step["content"], metadata={"title": step["title"]})
        for step in guide_steps
    ]

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(split_docs, embeddings)
    retriever = vectorstore.as_retriever()

    llm = ChatOpenAI(temperature=0)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=False
    )

    answer = qa_chain.run(user_input)

    state["response"] = answer
    return state
