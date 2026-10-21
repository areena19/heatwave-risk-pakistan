"""Tab 2: Climate Intelligence (RAG) Advisory Assistant."""
import streamlit as st

EMERGENCY_NOTE = "Official NDMA & WHO Protocol. In an emergency, contact local rescue (1122)."


def render_rag(evidence_index_path):
    st.markdown("### 💬 National Heat Action Plan & Labor Protection Advisory")
    st.markdown(
        """
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:1.2rem; margin-bottom:1.4rem;">
            <div style="font-weight:700; color:#0f172a; margin-bottom:0.3rem;">Ground-Truth Evidence Verification</div>
            <div style="color:#64748b; font-size:0.88rem;">
                All answers are grounded strictly in indexed <b>National Disaster Management Authority (NDMA)</b> heat action plans, 
                <b>World Health Organization (WHO)</b> advisories, and occupational safety documents for outdoor laborers.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not evidence_index_path.exists():
        st.warning("⚠️ RAG vector cache not indexed yet. Run `python -m src.rag.ingest` to index documents.")

    @st.cache_resource(ttl=300, show_spinner=False)
    def load_agent():
        try:
            from src.rag.answer import InsightAgent
            return InsightAgent(), None
        except Exception as exc:
            return None, f"{type(exc).__name__}: {exc}"

    agent, agent_err = load_agent()
    if agent_err:
        st.error(f"Intelligence Agent error: {agent_err}")
        return

    st.markdown("**💡 Common Advisory Inquiries:**")
    q_cols = st.columns(3)
    sample_questions = [
        "What rest-work cycles apply during Extreme Caution?",
        "What hydration is mandatory for construction labor?",
        "How should brick kiln shifts be scheduled during peak heat?",
    ]
    chosen_prompt = None
    for idx, q_text in enumerate(sample_questions):
        with q_cols[idx]:
            if st.button(q_text, key=f"chip_{idx}", use_container_width=True):
                chosen_prompt = q_text

    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)
    st.session_state.setdefault("chat", [])

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander("📚 Verified Evidence Citations"):
                    for s in msg["sources"]:
                        st.markdown(f"- `{s}`")

    prompt_input = st.chat_input("Ask about worker protection, hydration protocols, or legal temperature thresholds...")
    active_query = chosen_prompt or prompt_input

    if active_query:
        st.session_state.chat.append({"role": "user", "content": active_query})
        with st.chat_message("user"):
            st.markdown(active_query)

        sources = []
        with st.chat_message("assistant"):
            with st.spinner("Synthesizing guidance from verified NDMA/WHO documents..."):
                try:
                    res = agent.generate_answer(active_query)
                    text = getattr(res, "text", res)
                    text = str(text) if text else "No direct advisory matches found in indexed evidence."
                    try:
                        for h in agent.retriever.retrieve(active_query, top_k=3):
                            sources.append(f"{h['source']}, Page {h['page']} (Similarity Match: {h['score']:.2f})")
                    except Exception:
                        pass
                except Exception as exc:
                    text = f"Intelligence Agent Exception: {type(exc).__name__}: {exc}"

                text += f"\n\n---\n*⚠️ {EMERGENCY_NOTE}*"
                st.markdown(text)
                if sources:
                    with st.expander("📚 Verified Evidence Citations", expanded=True):
                        for s in sources:
                            st.markdown(f"- `{s}`")

        st.session_state.chat.append({"role": "assistant", "content": text, "sources": sources})
        if chosen_prompt:
            st.rerun()