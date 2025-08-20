import typer
from typing import Annotated
from rich import print as printR
import ollama
from sqlmodel import create_engine

DATABASE_URL = "postgresql+psycopg://postgres:password@localhost:5432/cli-db"
engine = create_engine(DATABASE_URL)  # echo=True logs SQL

#system prompt to get the title
system_prompt = {"role":"system","content":"In the response also add a title of the response by summarizing the question context. Syntax for title is 'Title: some title\n' and Always start the response after the title from new line. Make the title simple and more relevant to prompt."}

app = typer.Typer()

@app.callback()
def callback():
    #! Check if the database connection is successful
    with engine.connect() as connection:
        printR("✅ Connection successful!")
    


@app.command(help="Start a chat with the model")
def start_chat(user: Annotated[str, typer.Argument()],prompt: Annotated[str, typer.Option(prompt="Enter your message (or type '/bye' to exit)")]):
    
    while(True):
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
            
            printR("\n")

            start_chat(user=user,prompt=typer.prompt("Enter your message (or type '/bye' to exit)"))


if __name__ == "__main__":
    app()