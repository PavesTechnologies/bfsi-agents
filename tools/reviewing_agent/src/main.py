from workflows.initial_state import initial_review_state
from workflows.review_workflow import build_review_graph


def main():
    print("Reviewing Agent started")

    graph = build_review_graph()
    graph.invoke(initial_review_state())

    print("Reviewing Agent finished (non-blocking)")


if __name__ == "__main__":
    main()
