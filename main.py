import asyncio
from parse import parse_metro


def main():
    asyncio.run(parse_metro(query="Чай", threads=7))


if __name__ == '__main__':
    main()
