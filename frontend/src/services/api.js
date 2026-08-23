export const queryAssistant = async (question, history = []) => {
  try {
    const response = await fetch("http://localhost:8000/api/query", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, history }),
    });

    if (!response.ok) {
      try {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Unable to connect to the policy assistant. Please try again.");
      } catch (e) {
        if (e.message && !e.message.includes("Unexpected token")) throw e;
        throw new Error("Unable to connect to the policy assistant. Please try again.");
      }
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error.name === "TypeError" || (error.message && error.message.includes("fetch"))) {
      throw new Error("Unable to connect to the policy assistant. Please try again.");
    }
    throw error;
  }
};
