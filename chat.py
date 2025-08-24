import typer
from typing import Annotated
from rich import print as printR
import ollama
from sqlmodel import create_engine, SQLModel,Session, select
from sqlalchemy.orm import selectinload
from models import User, Chat, Chat_interactions
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(DATABASE_URL)  # echo=True logs SQL
chat_id = None
loaded_chat = False

#system prompt to get the title
system_prompt = {"role":"system","content":"In the response also add a title of the response by summarizing the question context. Syntax for title is 'Title: some title\n' and Always start the response after the title from new line. Make the title simple and more relevant to prompt."}

app = typer.Typer()

@app.callback()
def callback():
    #! Check if the database connection is successful
    with engine.connect() as connection:
        # printR("✅ Connection successful!")
        SQLModel.metadata.create_all(engine)
    

#! fetch the selected chat
def get_chat(id):
    with Session(engine) as session:
        statement = select(Chat).where(Chat.id == id).options(selectinload(Chat.interactions)) #! selectinload(Chat.interactions) is used to set interactions to eager loading
        chat = session.exec(statement).first()
        if chat:
            # printR(f"[green]interactions[/green]",chat.interactions)
            return chat
        else:
            return None



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
        if(prompt == "/bye"):
            printR("[bold green]Exiting chat...[/bold green]")
            raise typer.Exit()
        else:
            response = ollama.chat("llama3.2:latest", messages=[system_prompt, {"role":"user", "content":prompt}], stream=True);
            printR(f"[bold green]Response:[/bold green]")
            llm_response = ''
            for chunk in response:
                printR(chunk['message']['content'], end='', flush=True)
                llm_response += chunk['message']['content']
            splited_response = llm_response.split('\n',1)
            response_title = splited_response[0].lstrip("Title: ")
            response_content = splited_response[1].lstrip("\n") 
            if(chat_id is None):
                chat = Chat(title=response_title,user_id=int(user))
                with Session(engine) as session:
                    session.add(chat)
                    session.commit()
                    chat_id = chat.id
            chat_ineraction = Chat_interactions(user_prompt=prompt,system_response=response_content,chat_id=chat_id)
            with Session(engine) as session:
                session.add(chat_ineraction)
                session.commit()
            printR("\n")

            start_chat(user=user)


if __name__ == "__main__":
    app()