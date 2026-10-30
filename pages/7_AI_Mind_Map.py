
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
            "utf-8",
            errors="replace"
        )

    raise ValueError("Please upload a PDF or TXT file.")


# --------------------------------------------------
# CLEAN AI JSON RESPONSE
# --------------------------------------------------

def clean_ai_json(response):
    """Extract and clean JSON returned by the AI."""

    if isinstance(response, dict):
        return response

    if not isinstance(response, str):
        raise ValueError("The AI returned an unexpected response.")

    response = response.strip()

    # Remove Markdown code fences
    response = re.sub(
        r"```(?:json)?",
        "",
        response,
        flags=re.IGNORECASE
    ).strip()

    # Extract JSON object
    start = response.find("{")
    end = response.rfind("}")

    if start == -1 or end == -1 or end < start:
        raise ValueError(
            "The AI did not return a valid JSON object."
        )

    return json.loads(response[start:end + 1])


# --------------------------------------------------
# GENERATE MIND MAP DATA WITH OLLAMA
# --------------------------------------------------

def generate_mind_map(notes):
    """Generate an organized mind map using the local AI model."""

    prompt = f"""
You are an educational AI assistant.

Convert the student's lecture notes into a clear,
organized and useful mind map.

Use ONLY information supported by the notes.
Do not invent facts or add unrelated information.

Return valid JSON ONLY using this exact structure:

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

IMPORTANT RULES:

1. Identify one central topic.
2. Create 3 to 6 main branches.
3. Include the most important sections from the notes.
4. Put related concepts under the correct branch.
5. Add 2 to 4 subtopics under each branch when possible.
6. Use short keywords or phrases.
7. Avoid repeating concepts.
8. Keep labels short and easy to understand.
9. Do not write long explanations.
10. Return JSON only, without Markdown or explanations.

STUDENT NOTES:

{notes}
"""

    last_error = None

    # Try generation up to 2 times
    for attempt in range(2):

        try:

            response = generate_ai_response(
                prompt,
                timeout=600,
                json_mode=True,
                num_predict=1200
            )

            data = clean_ai_json(response)

            if not isinstance(data, dict):
                raise ValueError("Invalid mind map structure.")

            topic = data.get("topic")
            branches = data.get("branches")

            if not isinstance(topic, str) or not topic.strip():
                raise ValueError(
                    "The AI did not generate a main topic."
                )

            if not isinstance(branches, list):
                raise ValueError(
                    "The AI did not generate a branch list."
                )

            cleaned_branches = []

            for branch in branches:

                if not isinstance(branch, dict):
                    continue

                name = branch.get("name")
                children = branch.get("children", [])

                if not isinstance(name, str) or not name.strip():
                    continue

                if not isinstance(children, list):
                    children = []

                cleaned_children = []

                for child in children:

                    if isinstance(child, str) and child.strip():

                        cleaned_children.append(
                            child.strip()[:100]
                        )

                # Keep the branch even if it has fewer
                # than 2 children, so useful information
                # is not discarded.
                cleaned_branches.append({
                    "name": name.strip()[:100],
                    "children": cleaned_children[:4]
                })

            if not cleaned_branches:
                raise ValueError(
                    "The AI did not generate any valid branches."
                )

            return {
                "topic": topic.strip()[:100],
                "branches": cleaned_branches[:8]
            }

        except json.JSONDecodeError as error:

            last_error = (
                "The AI returned invalid JSON."
            )

        except ValueError as error:

            last_error = str(error)

        except Exception as error:

            # Connection or Ollama errors
            raise RuntimeError(
                f"Could not generate the mind map: {error}"
            ) from error

    raise ValueError(
        f"Mind map generation failed after 2 attempts. "
        f"Reason: {last_error}"
    )


# --------------------------------------------------
# CREATE INTERACTIVE VISUALIZATION
# --------------------------------------------------

def display_mind_map(data):
    """Display an interactive hierarchical mind map."""

    nodes = []
    edges = []

    branch_colors = [
        "#38BDF8",
        "#34D399",
        "#FBBF24",
        "#C084FC",
        "#FB7185",
        "#FB923C",
        "#A3E635",
        "#F472B6"
    ]

    # Central topic
    nodes.append(
        Node(
            id="root",
            label=data["topic"],
            size=32,
            shape="box",
            color="#6366F1",
            font={
                "color": "#FFFFFF",
                "size": 22
            },
            title=data["topic"]
        )
    )

    node_count = 0

    # Create branches and child nodes
    for branch_index, branch in enumerate(data["branches"]):

        branch_id = f"branch_{branch_index}"

        branch_color = branch_colors[
            branch_index % len(branch_colors)
        ]

        # Main branch
        nodes.append(
            Node(
                id=branch_id,
                label=branch["name"],
                size=25,
                shape="box",
                color=branch_color,
                font={
                    "color": "#172033",
                    "size": 17
                },
                title=branch["name"]
            )
        )

        # Connect branch to central topic
        edges.append(
            Edge(
                source="root",
                target=branch_id,
                color=branch_color,
                width=3
            )
        )

        # Child nodes
        for child_index, child in enumerate(branch["children"]):

            child_id = f"child_{branch_index}_{child_index}"

            nodes.append(
                Node(
                    id=child_id,
                    label=child,
                    size=17,
                    shape="box",
                    color="#E2E8F0",
                    font={
                        "color": "#1E293B",
                        "size": 13
                    },
                    title=child
                )
            )

            # Connect child to its branch
            edges.append(
                Edge(
                    source=branch_id,
                    target=child_id,
                    color="#94A3B8",
                    width=2
                )
            )

            node_count += 1

    # Configure graph once
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

    # Display graph
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

    if len(data["branches"]) < 3:
        st.warning(
            "The AI generated fewer than 3 main branches. "
            "Try using more detailed study notes for a "
            "more complete mind map."
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


# --------------------------------------------------
# UPLOAD PDF OR TXT
# --------------------------------------------------

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


# --------------------------------------------------
# PASTE STUDY NOTES
# --------------------------------------------------

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

        # Use up to 6,000 characters
        notes_for_ai = notes[:6000]

        if len(notes) > 6000:

            st.info(
                "Your notes are long. The first 6,000 "
                "characters will be used for this mind map."
            )

        # Remove previous result before generating
        st.session_state.pop(
            "generated_mind_map",
            None
        )

        try:

            with st.spinner(
                "Upwise is analyzing your notes..."
            ):

                mind_map_data = generate_mind_map(
                    notes_for_ai
                )

            # Save generated mind map
            st.session_state["generated_mind_map"] = (
                mind_map_data
            )

            st.session_state["mind_map_source_notes"] = (
                notes_for_ai
            )

            st.success("Your mind map is ready!")

        except json.JSONDecodeError:

            st.error(
                "The AI returned invalid JSON. "
                "Please try generating again."
            )

        except RuntimeError as error:

            st.error(
                "Unable to connect to Ollama. "
                "Please check that Ollama is running "
                "and llama3.2:1b is available."
            )

            st.caption(f"Technical details: {error}")

        except Exception as error:

            st.error(
                "Unable to generate the mind map."
            )

            st.caption(
                f"Technical details: {error}"
            )


# --------------------------------------------------
# DISPLAY GENERATED MIND MAP
# --------------------------------------------------

if "generated_mind_map" in st.session_state:

    st.divider()

    st.subheader("🗺️ Your Interactive Mind Map")

    mind_map_data = st.session_state["generated_mind_map"]

    display_mind_map(mind_map_data)


    # --------------------------------------------------
    # DOWNLOAD MIND MAP DATA AS JSON
    # --------------------------------------------------

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


    # --------------------------------------------------
    # DOWNLOAD STUDY OUTLINE AS TXT
    # --------------------------------------------------

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
