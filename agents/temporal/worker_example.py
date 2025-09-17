"""
Optional Temporal worker example.
This file is import-safe even when 'temporalio' isn't installed by providing
no-op decorator stubs. Install temporalio to run a real worker:
    pip install temporalio
"""
try:  # runtime-optional dependency
    from temporalio import workflow, activity  # type: ignore
except Exception:  # pragma: no cover - editor/import convenience
    class _DecoStub:
        def __getattr__(self, _name: str):
            def _decorator(fn=None, *args, **kwargs):
                if fn is None:
                    def _wrap(f):
                        return f
                    return _wrap
                return fn
            return _decorator

    workflow = _DecoStub()  # type: ignore
    activity = _DecoStub()  # type: ignore

@activity.defn
async def fetch_entity(company_id: str):
    return {"company_id": company_id}

@activity.defn
async def retrieve_docs(company_id: str, filters: dict | None = None, k: int = 20):
    return [{"doc_id": "doc:1", "score": 0.9}]

@activity.defn
async def compute_comps(company_id: str):
    return {"comps": []}

@activity.defn
async def call_llm(prompt_template: str, model: str = "llama3", max_tokens: int = 2000):
    return {"memo_json": {"sections": []}}

@activity.defn
async def post_validate(memo_json: dict, schema: dict | None = None, min_sources: int = 3, faithfulness_threshold: float = 0.9):
    return {"valid": True, "score": 0.91, "issues": []}

@activity.defn
async def publish_or_escalate(destination: str, payload: dict):
    return {"status": "published"}

@workflow.defn
class MemoistWorkflow:
    @workflow.run
    async def run(self, company_id: str):
        entity = await workflow.execute_activity(fetch_entity, company_id, schedule_to_close_timeout=30)
        docs = await workflow.execute_activity(retrieve_docs, company_id, {"segment": "vector-db"}, 60)
        comps = await workflow.execute_activity(compute_comps, company_id, 60)
        llm_out = await workflow.execute_activity(call_llm, "memoist", 120)
        val = await workflow.execute_activity(post_validate, llm_out, 60)
        if val.get("valid"):
            await workflow.execute_activity(publish_or_escalate, "store", llm_out, 30)
            return {"status": "published"}
        else:
            await workflow.execute_activity(publish_or_escalate, "human_queue", {"memo": llm_out}, 30)
            return {"status": "escalated"}
