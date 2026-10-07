from ..state import NoteState


def validate_node(state: NoteState):

    for section in state["analysis"].sections:

        if not section.title.strip():
            raise ValueError(
                "AI returned an empty section title"
            )

        if section.diagram:

            node_ids = {
                node.id
                for node in section.diagram.nodes
            }

            for edge in section.diagram.edges:

                if (
                    edge.source not in node_ids
                    or edge.target not in node_ids
                ):
                    raise ValueError(
                        "Invalid diagram edge"
                    )

    return {
        "validated": True
    }