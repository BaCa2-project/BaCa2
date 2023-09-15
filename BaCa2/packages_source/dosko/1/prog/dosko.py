
def sumadziel(n):
    wynik = 0
    for i in range(1, n):
        if n%i == 0:
            wynik += i
    return wynik

def main():
    n = int(input())
    if n == sumadziel(n):
        print("TAK")
    else:
        print("NIE")


if __name__ == "__main__":
    main()
    
