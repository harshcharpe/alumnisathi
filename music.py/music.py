import time
import sys

def print_lyrics():
    lyrics = ["tu hi meri shab hai"
"subha hai"
"tu hi din hai mera"
"tu hi mera rab hai"
"jahaan hai"
"tu hi meri duniya"
"tu waqt ! mere liyeeeee"
"main hoon tera lamha"
"kaise rahega bhalaaaaa"
"hoke tu mujhse judaaaaaaaa"


"o o o o ho ho......"]
    
    delays = [0.5,0.4,0.7,0.7,0.3,0.3,0.3,0.8,]

    print["tu hi meri sab hai:\n"]
    time.sleep(1.2)
    
    for i, line in enumerate(lyrics):
        for char in line:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(0.06)

        print()
        if i<len(delays):
            time.sleep(delays[i])
        else:
            time.sleep(0.8)

print_lyrics()