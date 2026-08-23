from app.pipeline.rag_pipeline import RAGPipeline

def main():
    questions = [
        "   ",
        "Can I return my shoes after 20 days?",
        "Can I return my shoes after 40 days?",
        "Can I return a damaged item after 5 days?",
        "Can I return a damaged item after 10 days?",
        "What is the standard return window?",
        "Are gift cards refundable?",
        "What happens if my item is defective?",
        "How do I cook a turkey?"
    ]

    pipeline = RAGPipeline()

    for question in questions:
        print("=" * 60)
        print("QUESTION")
        print("=" * 60)
        print(question)

        result = pipeline.run(question)

        print("\n" + "=" * 60)
        print("PIPELINE RESULT")
        print("=" * 60)
        print("Decision:", result.decision)
        print("Answer:", result.answer)
        if result.citations:
            print("\nCITATIONS:")
            for citation in result.citations:
                print("-", citation)
        print("\n")

        print("\n")

    print("\n" + "=" * 60)
    print("CONVERSATION FOLLOW-UP TEST")
    print("=" * 60)
    
    convo_questions = [
        "Can I return my shoes after 20 days?",
        "after 40 days?",
        "Can I return a damaged item after 5 days?",
        "after 10 days?",
        "How do I cook a turkey?"
    ]
    
    history = []
    for question in convo_questions:
        print("\nUser:", question)
        result = pipeline.run(question, history=history)
        print("Bot Decision:", result.decision)
        print("Bot Answer:", result.answer)
        
        history.append({"type": "user", "text": question})
        history.append({"type": "bot", "text": result.answer})
        
if __name__ == "__main__":
    main()
