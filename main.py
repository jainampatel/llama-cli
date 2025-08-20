import typer
from typing import Annotated, List
from rich import print as printR
import ollama
import chat 
from InquirerPy import prompt
from sqlmodel import create_engine, Field, SQLModel, Session, select, Relationship
import os
from models import  User

DATABASE_URL = "postgresql+psycopg://postgres:password@localhost:5432/cli-db"
engine = create_engine(DATABASE_URL)  # echo=True logs SQL


#! Check if the database connection is successful
def checkDBConnection():
    with engine.connect() as connection:
        printR("[bold green]Connection successful![/bold green]")

#! Register the User
def registerUser():
    printR("[bold blue]Registering user...[/bold blue]")
    first_name = typer.prompt("Enter your first name")
    last_name = typer.prompt("Enter your last name")
    username = typer.prompt("Enter your username")
    password = typer.prompt("Enter your password", hide_input=True)
    
    user = User(first_name=first_name, last_name=last_name, username=username, password=password)
    SQLModel.metadata.create_all(engine)  # Create tables if they don't exist
    with Session(engine) as session:
        session.add(user)
        session.commit()
        printR("[bold green]User registered successfully![/bold green]")

#! Login the User
def loginUser():
    printR("[bold blue]Logging in user...[/bold blue]")
    username = typer.prompt("Enter your username")
    password = typer.prompt("Enter your password", hide_input=True)
    
    with Session(engine) as session:
        statement = select(User).where(User.username == username, User.password == password)
        user = session.exec(statement).first()
        if user:
            return user
        else:
            printR("[bold red]Invalid username or password![/bold red]")
            return None

def main():
    checkDBConnection()
    printR("[bold blue]Welcome to the Ollama CLI![/bold blue]")
    questions = [
    {
        "type": "list",
        "message": "Select the command you want to run:",
        "choices": ["Login","Register"],
    },
    ]
    result = prompt(questions)
    command = result[0]
    
    if command == "Login":
        user = None
        while not user:
            user = loginUser()
            if not user:
                printR("[bold red]Try again![/bold red]")

        #! If login is successful, proceed to chat
        printR("[bold green]Login successful![/bold green]")
        #! to clear the terminal
        if os.name == "nt":
            os.system("cls")
        # Linux / Mac
        else:
            os.system("clear") 
        printR(f"[bold purple]Welcome {user.first_name} {user.last_name}![/bold purple]")
        questions = [
            {
                "type": "list",
                "message": "Select the command you want to run:",
                "choices": ["Chat", "History"],
            },
        ]
        result = prompt(questions)
        command = result[0]
        if command == "Chat":
            import sys
            printR('[bold yellow]user in main[/bold yellow]',str(user.id))
            sys.argv = ["main.py", "start-chat", str(user.id)]
            chat.app()  # Typer will now parse args and run callback
        elif command == "History":
            printR("[bold green]History command is not implemented yet.[/bold green]")
        
    elif command == "Register":
        registerUser()

if __name__ == "__main__":
    typer.run(main)