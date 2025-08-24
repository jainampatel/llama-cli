def main():
    with open(".env","r") as f:
        file_content = f.read()
        print('file_content.find("USERNAME=")',file_content.find("USERNAME="))
        if file_content.find("USERNAME=") >= 0 and file_content.find("PASSWORD=") >= 0:
            username=file_content.split("USERNAME=",1)[1].partition("\n")[0]
            password=file_content.split("PASSWORD=",1)[1].partition("\n")[0]
            print("username",username, "password",password,)


main()