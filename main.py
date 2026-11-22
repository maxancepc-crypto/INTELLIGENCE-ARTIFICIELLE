import sys

from dotenv import load_dotenv

load_dotenv()
from agent.core import run  # noqa: E402

if __name__ == "__main__":
    goal = " ".join(sys.argv[1:]) or input("Objectif : ")
    print("\n=== Résultat ===\n" + run(goal))
