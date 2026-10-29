"""LangGraph 구조 출력. 노드와 연결을 보여 준다. (검증 4.3: retrieve 와 generate 두 노드인지 확인)

실행:  python show_graph.py
"""
from graph import build_graph


def main() -> None:
    graph = build_graph(llm=object()).get_graph()
    print("노드:", [name for name in graph.nodes if not name.startswith("__")])
    print("연결:")
    for edge in graph.edges:
        print(f"  {edge.source} -> {edge.target}")
    print("\n[Mermaid]")
    print(graph.draw_mermaid())


if __name__ == "__main__":
    main()