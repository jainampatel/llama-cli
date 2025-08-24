import typer
from typing import Annotated
from rich import print as printR
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session, select
import os
from models import Chat, User
from InquirerPy import prompt
import chat

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(DATABASE_URL)
app = typer.Typer()

@app.callback()
def callback():
    #! Check if the database connection is successful
    with engine.connect() as connection:
        # printR("✅ Connection successful!")
        SQLModel.metadata.create_all(engine)

@app.command(help="Get user history")
def get_history(user_id:Annotated[int,typer.Argument()]):
    # user_id = int(user_id)
    while True:
        history=[]
        with Session(engine) as session:
            statement = select(Chat).where(Chat.user_id == user_id)
            history = list(session.exec(statement))
            chat_titles = [chat.title for chat in history]
            chat_titles.append("Exit")
            questions = [
                    {
                        "type": "list",
                        "message": "Chats history:",
                        "choices": chat_titles,
                    },
                    ]
            result = prompt(questions,style={"pointer": "fg:white bg:#ff9d00 bold"}, vi_mode=True, style_override=False)
            command = result[0]
            if command == "Exit":
                printR("[bold green]Exiting history section...[/bold green]")
                raise typer.Exit()
            else:
                chat_id = [chat.id for chat in history if chat.title == command][0] #! it extracts the selected chat ID
                import sys
                sys.argv = ["main.py", "start-chat", str(user_id), str(chat_id)]
                chat.app()  # Typer will now parse args and run callback
                
            



if __name__ == "__main__":
    app()