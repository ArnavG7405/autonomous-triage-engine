# pipeline.py
from preprocessor import Preprocessor
from engine import CoreEngine
from auditor import Auditor
import tools  # Import our new tools

class TriagePipeline:
    def __init__(self):
        self.preprocessor = Preprocessor()
        self.engine = CoreEngine()
        self.auditor = Auditor()

    def run(self, raw_message: str) -> dict:
        # Stage 1: Shield & Preprocessing
        cleaned_text, fast_reject_result = self.preprocessor.process(raw_message)
        if fast_reject_result is not None:
            fast_reject_result["tools_triggered"] = "None"
            return fast_reject_result

        # Stage 1.5: Autonomous Tool Routing (RAG & DB Lookup)
        db_data = tools.check_database(cleaned_text)
        rag_data = tools.search_knowledge_base(cleaned_text)
        
        active_tools = []
        if db_data: active_tools.append("SQL_DB")
        if rag_data: active_tools.append("Vector_RAG")
        
        tool_context = ""
        if active_tools:
            tool_context = f"\n<<<SYSTEM_TOOL_CONTEXT>>>\n{db_data}\n{rag_data}\n<<<END_TOOL_CONTEXT>>>\n"

        # Stage 2: Core LLM Triage
        decision = self.engine.triage(cleaned_text, raw_message, tool_context)

        # Stage 3: Verification & Auditing
        final_decision = self.auditor.audit(decision, raw_message)
        
        # Attach the tool badge to the output payload
        final_decision["tools_triggered"] = " + ".join(active_tools) if active_tools else "None"
        
        return final_decision