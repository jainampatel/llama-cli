import typer
from typing import Annotated, List, Dict, Any
from rich import print as printR
import ollama
import lists
from pypdf import PdfReader
from pypdf.errors import PdfReadError, FileNotDecryptedError
import tiktoken
import os
from rich.console import Console
from rich.status import Status


console = Console()

app = typer.Typer()
system_prompt = {"role":"system","content":"summarize the provided content. Summarize the provided content into a clear, strictly keep summary 4 lines only. Strictly Do not add lines in response like - Here is a summary of the provided content in 4 lines max or Here is a summary of the provided content in 4 lines max or Here is a summary of the provided content in 4 lines only"}
system_prompt2 = {"role":"system","content":"I want you to summarize the provided file and its content. Understand the content and file name then summarize"}

#! check the file type from a specified list of types
def check_file_type(path:str, list: List) -> bool:
    for type in list:
        if path.find(type) != -1:
            return False
        else:
            return True

#! generates tokens of the text
def tokenizer(text: str, model: str = "cl100k_base") -> List[int]:
    encoding = tiktoken.get_encoding(model)
    return encoding.encode(text)

#! decode tokens
def token_decoder(tokens:List[int], model: str = "cl100k_base") -> str:
    encoding = tiktoken.get_encoding(model)
    return encoding.decode(tokens)

#! read file content from text files and pdf files
def read_file(path: str) -> str | None :
    
    try:
        is_text_file = check_file_type(path=path, list= lists.NON_TEXT_FILE_EXTENSIONS)
        filename = os.path.basename(path)
        is_pdf_file = True if path.find('.pdf') != -1 else False
        #* checks the provided file is text or pdf file?
        if is_text_file:
            #* Executes if it is pdf file
            if is_pdf_file:
                reader = PdfReader(path)
                if reader.is_encrypted:
                    printR("[bold blue]PDF is encrypted please en")
                    password = typer.prompt(typer.style("PDF is encrypted please en",fg=typer.colors.BLUE))
                    reader.decrypt(password)
                text = "".join([page.extract_text() for page in reader.pages]) 
                return {"file_name": reader.metadata.title, "content":text} if reader.metadata else {"content":text}
            else:
                #* Executes if it is text file
                with open(path,"r") as f:
                    content = f.read()
                    return {"file_name": filename, "content":content}

        else:
            raise TypeError("Incorrect file type, please try with text file.")
        
    except FileNotFoundError:
        printR(f"[bold red]File Not Found[/bold red]\n")
        printR(f"Please try with another file\n")
        return None
    except PermissionError:
        printR(f"[bold red]Unable to access file, permission denied![/bold red]\n")
        return None
    except PdfReadError:
        print("The file is not a valid PDF or is corrupted.")
    except FileNotDecryptedError:
        print("The PDF is encrypted. Provide the correct password.")
    except Exception as e:
        printR(f"[bold red]Below error occured while accessing the file[/bold red]\n")
        printR(f"[bold red]{e}[/bold red]\n")
        return None

#! split file content into specific token size lists
def content_spliter(tokens: List[int], size: int = 3000):
    total_splits = 0
    splited_list = []
    for i in range(0,len(tokens),size):
        splited_list.append(tokens[i : i + size])
        total_splits += 1
    
    return {"splited_list":splited_list, "total_splits":total_splits}

@app.command(help="Summarize your file")
def summarize():
    while(True):
        path = typer.prompt(typer.style("\n\nEnter absolute path of the file",fg=typer.colors.BLUE))
        if(path == "/bye"):
            printR("[bold green]Exiting Summarization Tool...[/bold green]")
            raise typer.Exit()
        else:
            # *show spinner while waiting for response
            with console.status("[bold yellow]Processing the file...", spinner="dots") as status:
                file_data = read_file(path=path)
                content = file_data["content"]
                file_name = None 
                if file_data["file_name"]:
                    file_name = file_data["file_name"]
                status.stop()
                printR(f"Summarizing [bold purple] '{file_name}' [/bold purple]\n")
                status.update("[bold yellow]Summarizing file content...")
                status.start()
                tokens = tokenizer(text=content)
                if len(tokens) > 3000:
                    splited_tokens = content_spliter(tokens=tokens)
                    summaries = []
                    for index in range(splited_tokens["total_splits"]):
                        content = token_decoder(splited_tokens["splited_list"][index])
                        messages = [system_prompt,{"role":"user", "content":summaries[index - 1] + content if index > 0 else content}]
                        response = ollama.chat("llama3.2:latest", messages=messages);
                        summaries.append(response.message.content)
                            
                    status.stop()
                    printR("".join(summaries))
                else:
                    messages = [system_prompt2,{"role":"user", "content": "File Name:"+ file_name + "Content: " + content}]
                    response = ollama.chat("llama3.2:latest", messages=messages);
                    summary = response.message.content;
                    status.stop()
                    printR(summary)




                
    

if __name__ == "__main__":
    app()