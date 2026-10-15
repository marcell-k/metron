import random
from pathlib import Path


def main() -> None:
    o = []
    for _ in range(100):
        x = random.randint(-100, 100)
        o.append(x)
    with Path("sample.txt").open("w") as f:
        f.write(", ".join([str(x) for x in o]))


if __name__ == "__main__":
    main()
