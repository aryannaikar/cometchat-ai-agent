import os
import sys
sys.path.append(os.path.dirname(__file__))
from app.pipeline.rag_pipeline import RAGPipeline
p = RAGPipeline()
res = p.run('What is the return window?', [])
print("Final Answer:", res.answer)
print("Citations:", res.citations)
