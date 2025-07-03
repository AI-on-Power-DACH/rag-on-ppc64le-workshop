import textwrap

import chromadb
import gradio as gr
import openai

from ibm_theme import IBMTheme


chroma_client = chromadb.HttpClient(host="localhost", port=8000)
llm_client = openai.OpenAI(
    api_key="examplekey001",
    base_url="http://0.0.0.0:8080",
    default_headers={
        "Content-Type": "application/json",
    },
)


def retrieve_documents(query, collection_name, top_k=1):
    collection = chroma_client.get_collection(collection_name)
    results = collection.query(query_texts=[query], n_results=top_k)
    documents = results["documents"]
    return [doc for sublist in documents for doc in sublist]


def generate_response(query, collection_name, top_k, max_tokens, timeout):
    documents = retrieve_documents(query, collection_name, int(top_k))
    context = "\n".join(documents)

    prompt = textwrap.dedent(f"""
        ### CONTEXT:
        {context}
        
        ### QUERY:
        {query}
        
        Answer the user's QUERY using the CONTEXT above.
        If the CONTEXT doesn’t contain enough information, reply with: "I do not know."
        
        ### Answer:
        """)

    full_response = ""
    response = llm_client.completions.create(
        prompt=prompt,
        model="",
        max_tokens=int(max_tokens),
        timeout=float(timeout),
        stream=True,
    )

    for chunk in response:
        token_text = chunk.content
        full_response += token_text
        yield "", [(query, full_response)], context

    return "", [(query, full_response)], ""


def main():
    with gr.Blocks(theme=IBMTheme()) as demo:
        gr.Markdown("# Chat with IBM RedBooks")

        topic_choices = [collection.name for collection in chroma_client.list_collections()]

        with gr.Accordion(label="Advanced Settings", open=False):
            top_k_input = gr.Textbox(label="Number of documents to query", value="1")
            max_tokens_input = gr.Textbox(label="Maximum number of tokens", value="4096")
            timeout_input = gr.Textbox(label="Timeout in seconds", value="360")

        chatbot = gr.Chatbot(label="Chatbot", elem_id="chatbot", height=400)
        context_box = gr.Textbox(lines=8, interactive=False, label="Source from Documents in Vector DB")
        query_input = gr.Textbox(show_label=False, placeholder="Enter your query here...", container=False)
        topic_dropdown = gr.Dropdown(label="Which POWER Topic?", choices=sorted(topic_choices))
        submit_button = gr.Button("Submit")

        submit_button.click(
            fn=generate_response,
            inputs=[query_input, topic_dropdown, top_k_input, max_tokens_input, timeout_input],
            outputs=[query_input, chatbot, context_box]
        )

    demo.launch(server_name="0.0.0.0", server_port=7860)


if __name__ == "__main__":
    main()
