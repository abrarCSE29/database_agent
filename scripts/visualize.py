import matplotlib.pyplot as plt
from src.agent.graph import app

def visualize_agent_graph():
    """
    Generates a visualization of the agent graph and saves it as a PNG image.
    """
    try:
        # Get the graph from the compiled app
        graph = app.get_graph()

        # Draw the graph to a PNG file
        png_data = graph.draw_mermaid_png()

        # Save the PNG data to a file
        with open("agent_graph.png", "wb") as f:
            f.write(png_data)

        print("Agent graph visualization saved to agent_graph.png")

    except ImportError:
        print("Please install pygraphviz to visualize the agent graph.")
        print("For Windows, you might need to install graphviz first.")
        print("See: https://graphviz.org/download/")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    visualize_agent_graph()
