import typer
from typing import Annotated, List
from rich import print as printR
import ollama
import chat 
import history
from InquirerPy import prompt, inquirer
from sqlmodel import create_engine, Field, SQLModel, Session, select, Relationship
import os
from models import  User
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DB_URL")
engine = create_engine(DATABASE_URL)  # echo=True logs SQL


#! Check if the database connection is successful
def checkDBConnection():
    with engine.connect() as connection:
        SQLModel.metadata.create_all(engine)  # Create tables if they don't exist
        printR("[bold green]Connection successful![/bold green]")

#! to clear the terminal
def clear_cli():
    if os.name == "nt":
        os.system("cls")
    # Linux / Mac
    else:
        os.system("clear") 

#! Register method
def registerUser():
    printR("[bold blue]Registering user...[/bold blue]")
    first_name = typer.prompt("Enter your first name")
    last_name = typer.prompt("Enter your last name")
    username = typer.prompt("Enter your username")
    password = typer.prompt("Enter your password", hide_input=True)
    
    user = User(first_name=first_name, last_name=last_name, username=username, password=password)
    try:
        with Session(engine) as session:
            session.add(user)
            session.commit()
            session.refresh(user) # ensures user.id is available
            printR("[bold green]User registered successfully![/bold green]")
            return user
    except Exception as e:
        printR(f"[bold red]Error registering user: {e}[/bold red]")
        return None

#! Login method
def loginUser(saved_username: str = "" ,saved_password: str = ""):
    printR("[bold blue]Logging in user...[/bold blue]")
    username =  saved_username or typer.prompt("Enter your username")
    password = saved_password or typer.prompt("Enter your password", hide_input=True)
    
    with Session(engine) as session:
        statement = select(User).where(User.username == username, User.password == password)
        user = session.exec(statement).first()
        if user:
            return user
        else:
            printR("[bold red]Invalid username or password![/bold red]")
            return None

#! Save credential in memory as environment variables
def save_credentials(username: str, password: str):
    if username and password:
        with open(".env","r") as f:
            file_content = f.read()
            if file_content.find("USERNAME=") == -1 and file_content.find("PASSWORD=") == -1:
                with open(".env","a") as f:
                    f.write(f"USERNAME={username}\n")
                    f.write(f"PASSWORD={password}\n")
            else:
                new_file_content = []
                for content in file_content.split():
                    if content.find("USERNAME=") == -1 and content.find("PASSWORD=") == -1:
                        new_file_content.append(content)
                if len(new_file_content):
                    with open(".env","w") as f:
                        f.write("\n".join(new_file_content)+"\n")
                    with open(".env","a") as f:
                        f.write(f"USERNAME={username}\n")
                        f.write(f"PASSWORD={password}\n")
    else:
        raise TypeError("Please provide username and password!")

#! Option selection method
def select_options(user):
    printR(f"[bold purple]Welcome {user.first_name} {user.last_name}![/bold purple]")
    questions = [
        {
            "type": "list",
            "message": "Select the command you want to run:",
            "choices": ["Chat", "History"],
        },
    ]
    result = prompt(questions,style={"pointer": "fg:white bg:#ff9d00 bold"}, vi_mode=True, style_override=False)
    command = result[0]
    import sys
    if command == "Chat":
        sys.argv = ["main.py", "start-chat", str(user.id)]
        chat.app()  # Typer will now parse args and run callback
    elif command == "History":
        sys.argv = ["history.py", "get-history", str(user.id)]
        history.app()

def main():
    checkDBConnection()
    printR("[bold blue]Welcome to the Ollama CLI![/bold blue]")
    username = os.getenv("USERNAME","")
    password = os.getenv("PASSWORD","")
    user = None
    if(username and password):
        user = loginUser(saved_username = username, saved_password = password)
        if not user:
            while not user:
                user = loginUser()
                if not user:
                    printR("[bold red]Try again![/bold red]")
                else:
                    save_cred = inquirer.confirm(message="Want to save?", default=True).execute()
                    if save_cred:
                        save_credentials(username=user.username,password=user.password)
        else:
            #! If login is successful, proceed to chat
            printR("[bold green]Login successful![/bold green]")
    else: 
        questions = [
        {
            "type": "list",
            "message": "Select the command you want to run:",
            "choices": ["Login","Register"],
        },
        ]
        result = prompt(questions,style={"pointer": "fg:white bg:#ff9d00 bold"}, vi_mode=True, style_override=False)
        command = result[0]
        
        #* if user select login then this section will execute
        if command == "Login":
            while not user:
                user = loginUser()
                if not user:
                    printR("[bold red]Try again![/bold red]")

            #! If login is successful, proceed to chat
            printR("[bold green]Login successful![/bold green]")
            
        #* if user select register then this section will execute
        elif command == "Register":
            while not user:
                user = registerUser()
                if not user:
                    printR("[bold red]Try again![/bold red]")
        save_cred = False
        save_cred = inquirer.confirm(message="Want to save?", default=True).execute()
        if save_cred:
            save_credentials(username=user.username,password=user.password)
        
        
    clear_cli()
    select_options(user=user)


if __name__ == "__main__":
    typer.run(main)