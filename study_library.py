
import json
import uuid
from pathlib import Path

import streamlit as st
from pypdf import PdfReader
from pypdf.errors import PdfReadError


LIBRARY_DIR = Path("study_library")
INDEX_FILE = LIBRARY_DIR / "library_index.json"

FOLDER_COLORS = {
    "Orange": "#F59E0B",
    "Pink": "#EC4899",
    "Blue": "#3B82F6",
    "Green": "#22C55E",
    "Purple": "#8B5CF6",
    "Yellow": "#EAB308",
}


def load_library():
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    if not INDEX_FILE.exists():
        return {"subjects": [], "notes": []}

    try:
        data = json.loads(INDEX_FILE.read_text(encoding="utf-8"))

        # Support the previous library format.
        if isinstance(data, list):
            data = {"subjects": [], "notes": data}

        if not isinstance(data, dict):
            raise ValueError("Invalid library format.")

        data.setdefault("subjects", [])
        data.setdefault("notes", [])

        # Preserve existing documents and assign missing subjects a color.
        existing_subjects = {
            subject["name"].lower()
            for subject in data["subjects"]
        }

        for note in data["notes"]:
            subject_name = (
                note.get("subject", "General").strip() or "General"
            )

            if subject_name.lower() not in existing_subjects:
                data["subjects"].append({
                    "id": str(uuid.uuid4()),
                    "name": subject_name,
                    "color": FOLDER_COLORS["Blue"],
                })
                existing_subjects.add(subject_name.lower())

            note.setdefault("id", str(uuid.uuid4()))

        return data

    except (json.JSONDecodeError, OSError, TypeError, AttributeError, ValueError, KeyError):
        st.error(
            "Unable to read the library index. "
            "Please check library_index.json before saving changes."
        )
        return {"subjects": [], "notes": []}


def save_library(data):
    LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

    INDEX_FILE.write_text(
        json.dumps(data, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def display_study_library():
    st.title("📚 My Study Library")
    st.write("Organize your study materials by subject.")

    data = load_library()
    subjects = data["subjects"]
    notes = data["notes"]

    if "selected_subject_id" not in st.session_state:
        st.session_state.selected_subject_id = None

    # Add a new subject.
    with st.expander("➕ Add Subject"):
        with st.form("add_subject_form"):
            subject_name = st.text_input("Subject name")

            color_name = st.selectbox(
                "Choose folder color",
                list(FOLDER_COLORS.keys()),
            )

            create_subject = st.form_submit_button("Create Subject")

        if create_subject:
            clean_name = subject_name.strip()

            if not clean_name:
                st.warning("Please enter a subject name.")

            elif any(
                s["name"].lower() == clean_name.lower()
                for s in subjects
            ):
                st.warning("This subject already exists.")

            else:
                subjects.append({
                    "id": str(uuid.uuid4()),
                    "name": clean_name,
                    "color": FOLDER_COLORS[color_name],
                })

                save_library(data)
                st.success("Subject created!")
                st.rerun()

    # Search subjects and documents.
    search = st.text_input(
        "🔎 Search subjects or study materials",
        key="library_search",
    ).strip().lower()

    selected_id = st.session_state.selected_subject_id

    # Open a selected subject.
    if selected_id:
        selected_subject = next(
            (s for s in subjects if s["id"] == selected_id),
            None,
        )

        if selected_subject is None:
            st.session_state.selected_subject_id = None
            st.rerun()
            return

        st.button(
            "← All Subjects",
            on_click=lambda: setattr(
                st.session_state,
                "selected_subject_id",
                None,
            ),
        )

        st.header(f"📁 {selected_subject['name']}")

        # Customize the subject folder color.
        color_names = list(FOLDER_COLORS.keys())
        color_values = list(FOLDER_COLORS.values())

        current_color_index = next(
            (
                i for i, value in enumerate(color_values)
                if value == selected_subject.get("color")
            ),
            2,
        )

        new_color = st.selectbox(
            "Customize folder color",
            color_names,
            index=current_color_index,
            key=f"color_{selected_id}",
        )

        if FOLDER_COLORS[new_color] != selected_subject.get("color"):
            selected_subject["color"] = FOLDER_COLORS[new_color]
            save_library(data)
            st.rerun()

        subject_notes = [
            note for note in notes
            if note.get("subject", "").lower()
            == selected_subject["name"].lower()
        ]

        # Upload a study document.
        with st.form(
            f"upload_{selected_id}",
            clear_on_submit=True,
        ):
            title = st.text_input("Document title")

            uploaded_pdf = st.file_uploader(
                "Upload PDF document",
                type=["pdf"],
                key=f"pdf_{selected_id}",
            )

            save_note = st.form_submit_button("💾 Save Document")

        if save_note:
            if not title.strip():
                st.warning("Please enter a document title.")

            elif uploaded_pdf is None:
                st.warning("Please upload a PDF document.")

            else:
                try:
                    uploaded_pdf.seek(0)
                    reader = PdfReader(uploaded_pdf)

                    # Check that the PDF can be read.
                    len(reader.pages)

                    filename = f"{uuid.uuid4().hex}.pdf"

                    LIBRARY_DIR.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    (LIBRARY_DIR / filename).write_bytes(
                        uploaded_pdf.getvalue()
                    )

                    notes.append({
                        "id": str(uuid.uuid4()),
                        "title": title.strip(),
                        "subject": selected_subject["name"],
                        "filename": filename,
                    })

                    save_library(data)
                    st.success("Document saved!")
                    st.rerun()

                except (PdfReadError, OSError, ValueError):
                    st.error(
                        "Unable to read this PDF. "
                        "Please check the file and try again."
                    )

        st.subheader(f"Study Materials ({len(subject_notes)})")

        if not subject_notes:
            st.info(
                "No study materials in this subject yet. "
                "Upload your first PDF above."
            )

        for note in subject_notes:
            with st.expander(f"📄 {note['title']}"):
                file_path = LIBRARY_DIR / note["filename"]

                if file_path.is_file():
                    st.download_button(
                        "📥 Download PDF",
                        data=file_path.read_bytes(),
                        file_name=f"{note['title']}.pdf",
                        mime="application/pdf",
                        key=f"download_{note['id']}",
                    )

                else:
                    st.warning(
                        "The PDF file could not be found."
                    )

                
                if st.button(
                    "🗑️ Delete Document",
                    key=f"delete_{note['id']}",
                ):
                    st.session_state["confirm_delete_note_id"] = note["id"]

                if st.session_state.get("confirm_delete_note_id") == note["id"]:
                    st.warning(
                        f"Are you sure you want to delete "
                        f"'{note['title']}'? This cannot be undone."
                    )

                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:
                        if st.button(
                            "Yes, Delete PDF",
                            key=f"confirm_delete_note_{note['id']}",
                            type="primary",
                            use_container_width=True,
                        ):
                            if file_path.is_file():
                                file_path.unlink()

                            data["notes"] = [
                                item for item in data["notes"]
                                if item["id"] != note["id"]
                            ]

                            st.session_state["confirm_delete_note_id"] = None
                            save_library(data)
                            st.rerun()

                    with cancel_col:
                        if st.button(
                            "Cancel",
                            key=f"cancel_delete_note_{note['id']}",
                            use_container_width=True,
                        ):
                            st.session_state["confirm_delete_note_id"] = None
                            st.rerun()


        # Delete the selected subject and its documents.
        if st.button("🗑️ Delete This Subject"):
            for note in subject_notes:
                file_path = LIBRARY_DIR / note["filename"]

                if file_path.is_file():
                    file_path.unlink()

            data["notes"] = [
                note for note in data["notes"]
                if note.get("subject", "").lower()
                != selected_subject["name"].lower()
            ]

            data["subjects"] = [
                subject for subject in data["subjects"]
                if subject["id"] != selected_id
            ]

            st.session_state.selected_subject_id = None
            save_library(data)
            st.rerun()

        return

    # Display subject cards.
    filtered_subjects = [
        subject for subject in subjects
        if search in subject["name"].lower()
        or any(
            search in note.get("title", "").lower()
            for note in notes
            if note.get("subject", "").lower()
            == subject["name"].lower()
        )
    ]

    if not filtered_subjects:
        st.info(
            "No subjects found. Create your first subject above."
        )
        return

    columns = st.columns(3)

    for index, subject in enumerate(filtered_subjects):
        subject_count = sum(
            1 for note in notes
            if note.get("subject", "").lower()
            == subject["name"].lower()
        )

        color = subject.get("color", FOLDER_COLORS["Blue"])

        with columns[index % 3]:
            st.markdown(
                f"""
                <div style="
                    background: {color}20;
                    border: 1px solid {color}65;
                    border-radius: 16px;
                    padding: 20px;
                    min-height: 135px;
                    margin-bottom: 10px;
                ">
                    <div style="font-size: 42px;">📁</div>
                    <div style="
                        font-size: 18px;
                        font-weight: 600;
                        overflow-wrap: anywhere;
                    ">{subject["name"]}</div>
                    <div style="font-size: 14px; opacity: 0.8;">
                        {subject_count} documents
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
           
            if st.button(
             f"Open {subject['name']}",
             key=f"open_{subject['id']}",
             use_container_width=True,
            ):
                
             st.session_state["selected_subject_id"] = subject["id"]
             st.rerun()

display_study_library()
