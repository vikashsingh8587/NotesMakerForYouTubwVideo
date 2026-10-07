from concurrent.futures import ThreadPoolExecutor, as_completed
from langgraph.graph import StateGraph, START, END
from .state import NoteState
from .nodes.analyze import analyze_node
from .nodes.validate import validate_node

TEXT_CHUNK_SIZE = 30000
TEXT_MAX_WORKERS = 2

def prepare_chunks(state: NoteState):
    transcript = state["transcript"]
    chunks = [transcript[i:i + TEXT_CHUNK_SIZE] for i in range(0, len(transcript), TEXT_CHUNK_SIZE)]
    if not chunks:
        raise ValueError("Transcript is empty")
    print(f"Text analysis: {len(chunks)} chunk(s)")
    return {"chunks": chunks, "current_chunk": 0, "chunk_results": []}

def analyze_all_chunks(state: NoteState):
    chunks = state["chunks"]
    results = [None] * len(chunks)

    def run_one(index: int):
        print(f"Text chunk {index + 1}/{len(chunks)} started")
        result = analyze_node({**state, "transcript": chunks[index]})
        return index, result["analysis"]

    workers = min(TEXT_MAX_WORKERS, len(chunks))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(run_one, i) for i in range(len(chunks))]
        for future in as_completed(futures):
            index, analysis = future.result()
            results[index] = analysis
            print(f"Text chunk {index + 1}/{len(chunks)} completed")

    return {"chunk_results": results}

def combine_results(state: NoteState):
    results = [r for r in state.get("chunk_results", []) if r is not None]
    if not results:
        raise ValueError("No analysis results were generated")
    first = results[0]
    all_sections = []
    for result in results:
        all_sections.extend(result.sections)
    combined = first.model_copy(update={"sections": all_sections, "visuals": []})
    return {"analysis": combined, "final_notes": combined}

def build_text_graph():
    graph = StateGraph(NoteState)
    graph.add_node("prepare_chunks", prepare_chunks)
    graph.add_node("analyze_chunks", analyze_all_chunks)
    graph.add_node("combine_results", combine_results)
    graph.add_node("validate_notes", validate_node)
    graph.add_edge(START, "prepare_chunks")
    graph.add_edge("prepare_chunks", "analyze_chunks")
    graph.add_edge("analyze_chunks", "combine_results")
    graph.add_edge("combine_results", "validate_notes")
    graph.add_edge("validate_notes", END)
    return graph.compile()
