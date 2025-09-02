import typer
from typing import Annotated, List, Dict, Any
from rich import print as printR
import ollama
from sqlmodel import create_engine, SQLModel,Session, select, text
from sqlalchemy.orm import selectinload
from models import User, Chat, Chat_interactions, Chat_vectors
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import os

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(DATABASE_URL)  # echo=True logs SQL
chat_id = None
loaded_chat = False
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

#system prompt to get the title
system_prompt = {"role":"system","content":"In the response also add a title of the response by summarizing the question context. Syntax for title is 'Title: some title\n' and Always start the response after the title from new line. Make the title simple and more relevant to prompt."}

app = typer.Typer()

@app.callback()
def callback():
    #! Check if the database connection is successful
    with engine.connect() as connection:
        # printR("✅ Connection successful!")
        SQLModel.metadata.create_all(engine)
    
    #!If index was built with lists = 100, setting probes = 10 means it searches 10 clusters out of 100.
    with Session(engine) as s:
        s.exec(text("SET ivfflat.probes = 50;"))
    

#! fetch the selected chat
def get_chat(id: int):
    with Session(engine) as session:
        #! selectinload(Chat.interactions) is used to set to populate/eager loading interactions in Chat group
        statement = select(Chat).where(Chat.id == id).options(selectinload(Chat.interactions)) 
        chat = session.exec(statement).first()
        if chat:
            # printR(f"[green]interactions[/green]",chat.interactions)
            return chat
        else:
            return None

#! Creates embeddings for vector database
def generate_embeddings(data: str) -> list[float]:
    #* encode is use to generate embeddings
    return _model.encode([data],normalize_embeddings=True)[0].tolist()

def get_relevant_chat(chat_id: int, user_prompt: str, k: int = 5) -> List[Dict[str, Any]]:
    if not user_prompt or user_prompt == "/bye":
        return None;
    que_embedding = generate_embeddings(user_prompt)  # returns List[float]

    statement = text("""
        SELECT id, text
        FROM chat_vectors
        WHERE chat_id = :chat_id
        ORDER BY embedding <-> (:qvec)::vector
        LIMIT :k
    """)

    with Session(engine) as s:
        rows = s.execute(
            statement,
            {
                "chat_id": chat_id,
                "qvec": que_embedding,   # pgvector understands this
                "k": k
            }
        ).all()
    if len(rows):
        joined = "\n---\n".join(r[1] for r in rows)
        return f"Relevant prior snippets:\n{joined}\n\n"
    else:
        return



@app.command(help="Start a chat with the model")
def start_chat(user: Annotated[str, typer.Argument()],selected_chat_id: Annotated[int,typer.Argument()] = None):
    global chat_id
    global loaded_chat
    selected_chat = None
    if selected_chat_id:
        chat_id = selected_chat_id
        loaded_chat = True
        selected_chat = get_chat(chat_id)
    if selected_chat:
        for interaction in selected_chat.interactions:
            printR("\n\n[blue]Enter your message (or type '/bye' to exit): [/blue]" + interaction.user_prompt + "\n")
            printR(f"[bold green]Response:[/bold green]\n")
            printR(interaction.system_response + "\n")
    while(True):
        prompt = typer.prompt(typer.style("Enter your message (or type '/bye' to exit)",fg=typer.colors.BLUE))
        search_result = get_relevant_chat(chat_id=chat_id,user_prompt=prompt)
        if(prompt == "/bye"):
            printR("[bold green]Exiting chat...[/bold green]")
            raise typer.Exit()
        else:
            messages = [system_prompt,{"role":"system","content":search_result}, {"role":"user", "content":prompt}] if search_result else [system_prompt,{"role":"user", "content":prompt}]
            response = ollama.chat("llama3.2:latest", messages=messages, stream=True);
            printR(f"[bold green]Response:[/bold green]")
            llm_response = ''
            for chunk in response:
                printR(chunk['message']['content'], end='', flush=True)
                llm_response += chunk['message']['content']
            splited_response = llm_response.split('\n',1)
            if(len(splited_response) > 1):
                response_title = splited_response[0].lstrip("Title: ")
                response_content = splited_response[1].lstrip("\n") 
            else:
                response_title = prompt
                response_content = llm_response
            if(chat_id is None):
                #! saves the chat group in DB
                chat = Chat(title=response_title,user_id=int(user))
                with Session(engine) as session:
                    session.add(chat)
                    session.commit()
                    chat_id = chat.id
            #! saves the chat interactions in DB
            chat_ineraction = Chat_interactions(user_prompt=prompt,system_response=response_content,chat_id=chat_id)
            with Session(engine) as session:
                session.add(chat_ineraction)
                session.commit()
                session.refresh(chat_ineraction) #! to use chat_interaction.id later in the code
            printR("\n")
            #! saves the chat interaction vector in DB
            user_interaction = "User prompt:"+prompt+"\n"+"Response:"+response_content
            embedding = generate_embeddings(user_interaction)
            chat_embedding = Chat_vectors(chat_interaction_id=chat_ineraction.id,text=user_interaction,chat_id=chat_id,embedding=embedding)
            with Session(engine) as session:
                session.add(chat_embedding)
                session.commit()
            start_chat(user=user)


if __name__ == "__main__":
    app()