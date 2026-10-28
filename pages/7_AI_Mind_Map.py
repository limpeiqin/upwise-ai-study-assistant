
import json
import re

import streamlit as st
from pypdf import PdfReader
from streamlit_agraph import agraph, Node, Edge, Config
from ai_helpers import generate_ai_response


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.title("🧠 AI Mind Map")
st.write(
    "Turn your study notes into an interactive mind map "
    "with AI-powered topic connections."
)

st.divider()


# --------------------------------------------------
# EXTRACT TEXT FROM UPLOADED FILES
# --------------------------------------------------

def extract_uploaded_text(uploaded_file):
    """Extract text from PDF or TXT files."""
    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        pages = []

        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n".join(pages)

    if filename.endswith(".txt"):
        return uploaded_file.getvalue().decode(
            "utf-8", errors="replace"
        )

    raise ValueError("Please upload a PDF or TXT file.")


# --------------------------------------------------
# GENERATE MIND MAP DATA WITH OLLAMA
# --------------------------------------------------

def generate_mind_map(notes):
    """Ask the local AI model to organize notes into a mind map."""

    prompt = f"""
You are an educational assistant that creates mind maps
from student lecture notes.

Use ONLY information supported by the notes.
Do not invent facts or add unrelated topics.

Return valid JSON only, using this exact structure:
{{
  "topic": "Main topic",
  "branches": [
    {{
      "name": "Main branch",
      "children": [
        "Subtopic one",
        "Subtopic two"
      ]
    }}
  ]
}}

Rules:
- Choose one clear central topic.
- Create exactly 3 main branches.
- Include all important concepts from the notes.
- Each main branch should have 2 short subtopics.
- Keep every label under 6 words.
- Use keywords or short phrases, not full sentences.
- Do not include long definitions or examples as node labels.
- Use only information supported by the notes.
- Return valid JSON only, without explanations.

STUDENT NOTES:
{notes}
"""

    response = generate_ai_response(
        prompt,
        timeout=600,
        json_mode=True,
        num_predict=400
    )

    
    # Clean the AI response before parsing JSON.
    response = response.strip()

    # Remove Markdown code fences if present.
    response = re.sub(
        r"```(?:json)?",
        "",
        response,
        flags=re.IGNORECASE
    ).strip()

    # Extract the JSON object if extra text is present.
    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError(
            "The AI did not return a valid JSON object. "
            "Please try again."
        )

    response = response[start:end + 1]
    data = json.loads(response)

    if not isinstance(data, dict):
        raise ValueError("The AI returned an invalid mind map.")

    topic = data.get("topic")
    branches = data.get("branches")

    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("The AI did not return a main topic.")

    if not isinstance(branches, list) or not branches:
        raise ValueError("The AI did not return any branches.")

    # Validate and limit the generated structure.
    cleaned_branches = []

    for branch in branches[:8]:
        if not isinstance(branch, dict):
            continue

        name = branch.get("name")
        children = branch.get("children", [])

        if not isinstance(name, str) or not name.strip():
            continue

        if not isinstance(children, list):
            children = []

        cleaned_children = [
            child.strip()
            for child in children
            if isinstance(child, str) and child.strip()
        ][:4]

        cleaned_branches.append({
            "name": name.strip()[:100],
            "children": cleaned_children
        })

    if not cleaned_branches:
        raise ValueError("No valid branches were generated.")

    return {
        "topic": topic.strip()[:100],
        "branches": cleaned_branches
    }


# --------------------------------------------------
# CREATE INTERACTIVE VISUALIZATION
# --------------------------------------------------


def display_mind_map(data):
    """Display a clean, interactive hierarchical mind map."""

    nodes = []
    edges = []

    branch_colors = [
        "#38BDF8",
        "#34D399",
        "#FBBF24",
        "#C084FC",
        "#FB7185",
        "#FB923C"
    ]

    # Central topic
    nodes.append(
        Node(
            id="root",
            label=data["topic"],
            size=32,
            shape="box",
            color="#6366F1",
            font={"color": "#FFFFFF", "size": 22},
            title=data["topic"]
        )
    )

    node_count = 0

    for branch_index, branch in enumerate(data["branches"]):
        branch_id = f"branch_{branch_index}"
        branch_color = branch_colors[
            branch_index % len(branch_colors)
        ]

        nodes.append(
            Node(
                id=branch_id,
                label=branch["name"],
                size=25,
                shape="box",
                color=branch_color,
                font={"color": "#172033", "size": 17},
                title=branch["name"]
            )
        )

        edges.append(
            Edge(
                source="root",
                target=branch_id,
                color=branch_color,
                width=3
            )
        )

        for child_index, child in enumerate(branch["children"]):
            child_id = f"child_{branch_index}_{child_index}"

            nodes.append(
                Node(
                    id=child_id,
                    label=child,
                    size=17,
                    shape="box",
                    color="#E2E8F0",
                    font={"color": "#1E293B", "size": 13},
                    title=child
                )
            )

            edges.append(
                Edge(
                    source=branch_id,
                    target=child_id,
                    color="#94A3B8",
                    width=2
                )
            )

            node_count += 1

    # Configure the graph ONCE, after creating all nodes.
    config = Config(
        width="100%",
        height=750,
        directed=True,
        physics=False,
        hierarchical=True,
        nodeHighlightBehavior=True,
        highlightColor="#A5B4FC",
        collapsible=True,
        staticGraph=False
    )

    agraph(
        nodes=nodes,
        edges=edges,
        config=config
    )

    st.caption(
        "Tip: Hover over a node to see its full label. "
        "You can drag nodes to adjust their positions."
    )

    st.caption(
        f"Total nodes: {len(nodes)} "
        f"(including {node_count} subtopics)"
    )


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

st.subheader("📚 Add Your Study Notes")

input_method = st.radio(
    "Choose your input method",
    [
        "Upload PDF or TXT",
        "Paste notes"
    ],
    horizontal=True,
    key="mind_map_input_method"
)

notes = ""

if input_method == "Upload PDF or TXT":
    uploaded_files = st.file_uploader(
        "Upload study notes",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        help="You can upload multiple PDF or TXT files."
    )

    if uploaded_files:
        extracted_parts = []

        for uploaded_file in uploaded_files:
            try:
                extracted_text = extract_uploaded_text(
                    uploaded_file
                )

                if extracted_text.strip():
                    extracted_parts.append(
                        f"\n--- {uploaded_file.name} ---\n"
                        f"{extracted_text}"
                    )
                else:
                    st.warning(
                        f"No readable text found in "
                        f"{uploaded_file.name}. "
                        "Scanned PDFs may require OCR."
                    )

            except Exception as error:
                st.error(
                    f"Could not read {uploaded_file.name}: "
                    f"{error}"
                )

        notes = "\n".join(extracted_parts)

else:
    notes = st.text_area(
        "Paste your study notes here",
        height=250,
        placeholder=(
            "Paste your study notes here...\n\n"
            "Example: Database normalization reduces "
            "data redundancy using normal forms."
        ),
        key="mind_map_pasted_notes"
    )


# --------------------------------------------------
# GENERATE BUTTON
# --------------------------------------------------

st.divider()

if st.button(
    "✨ Generate AI Mind Map",
    type="primary",
    use_container_width=True
):
    if not notes or not notes.strip():
        st.warning(
            "Please upload a file or paste your notes first."
        )

    elif len(notes.strip()) < 30:
        st.warning(
            "Please provide more notes so the AI can "
            "create a useful mind map."
        )

    else:
        # Limit prompt size to help the local model.
        notes_for_ai = notes[:3000]

        if len(notes) > 3000:
            st.info(
                "Your notes are long. The first 3,000 "
                "characters will be used for this mind map."
            )

        try:
            with st.spinner(
                "Upwise is analyzing your notes..."
            ):
                mind_map_data = generate_mind_map(
                    notes_for_ai
                )

            st.session_state["generated_mind_map"] = (
                mind_map_data
            )

            st.session_state["mind_map_source_notes"] = (
                notes_for_ai
            )

            st.success("Your mind map is ready!")

        except json.JSONDecodeError:
            st.error(
                "The AI returned an invalid format. "
                "Please try generating the mind map again."
            )

        except Exception as error:
            st.error(
                "Unable to generate the mind map. "
                "Make sure Ollama is running and your "
                "llama3.2:1b model is available."
            )
            st.caption(f"Technical details: {error}")


# --------------------------------------------------
# DISPLAY GENERATED MIND MAP
# --------------------------------------------------

if "generated_mind_map" in st.session_state:
    st.divider()
    st.subheader("🗺️ Your Interactive Mind Map")

    mind_map_data = st.session_state["generated_mind_map"]

    display_mind_map(mind_map_data)

    # Download the structured mind map as JSON.
    st.download_button(
        label="⬇️ Download Mind Map Data (JSON)",
        data=json.dumps(
            mind_map_data,
            indent=2,
            ensure_ascii=False
        ),
        file_name="upwise_mind_map.json",
        mime="application/json",
        use_container_width=True
    )

    # Download a readable text outline.
    outline = [mind_map_data["topic"]]

    for branch in mind_map_data["branches"]:
        outline.append(f"\n- {branch['name']}")

        for child in branch["children"]:
            outline.append(f"    - {child}")

    st.download_button(
        label="⬇️ Download Study Outline (TXT)",
        data="\n".join(outline),
        file_name="upwise_study_outline.txt",
        mime="text/plain",
        use_container_width=True
    )
