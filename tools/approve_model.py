
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from model_governance.approval_workflow import ApprovalWorkflow
from research_pipeline.model_registry import ModelRegistry, ModelEntry
from datetime import datetime, timezone

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--approver", required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--registry", help="JSON registry file")
    args = parser.parse_args()

    registry = ModelRegistry()
    if args.registry and os.path.exists(args.registry):
        with open(args.registry, "r") as f:
            data = json.load(f)
        for mid, mdata in data.items():
            registry.register(ModelEntry(**mdata))

    workflow = ApprovalWorkflow(registry)
    result = workflow.approve(args.model_id, args.approver, args.notes)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
