print("Salom! Men bu dastur xafsizlik tamilayman")

name = input("Ismingiz kim?:\n>>>")
name = name.capitalize()

if name == "Barounzx":
    admin = input("Kodni kiritnig:\n>>>");
    if admin == "int":
        two_exam =int(input("Togri kod kiriting: "));
        if two_exam == 10:
            print("Xush kelibsiz!")
        else:
            fake = input("Boshqa nom kiriting")
            if fake == "Barounzx":
                input("Iltmos boshqa nom qoying bu nom taqiqlangan!")
            else:
                age = int(input("Yoshing neshada?:\n>>>"))
                if age >= 18:
                    print("Xush kelibsiz!")
                    print(name, "endi siz bizni klandansiz")
                else:
                    print("Siz kira olmadingiz!");
    else:
        fake = input("Boshqa nom kiriting")
        if fake == "Barounzx":
            input("Iltmos boshqa nom qoying bu nom taqiqlangan!")
        else:
            age = int(input("Yoshing neshada?:\n>>>"))
            if age >= 18:
                print("Xush kelibsiz!")
                print(name, "endi siz bizni klandansiz")
            else:
                print("Siz kira olmadingiz!");
else:
    age = int(input("Yoshingiz neshada?:\n>>>"));
    if age >= 18:
        print("Xush kelibsiz!")
        print(f"{name} endi siz bizni klandansiz")
    else:
        print("Siz kira olmadingiz!")



