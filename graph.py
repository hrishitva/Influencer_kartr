    import pandas as pd
    import networkx as nx
    import plotly.graph_objects as go
    import os

    # --- Configuration ---
    # Assuming database.csv is in the parent directory of this script's location
    CSV_PATH = os.path.join(os.path.dirname(__file__), '..', 'database.csv')
    OUTPUT_HTML_PATH = os.path.join(os.path.dirname(__file__), 'influencer_sponsor_graph.html')
    # ---

    def load_data(csv_path):
        """Loads data from the CSV file."""
        if not os.path.exists(csv_path):
            print(f"Error: CSV file not found at {csv_path}")
            return None
        try:
            df = pd.read_csv(csv_path)
            print(f"Loaded {len(df)} rows from {csv_path}")
            # Basic cleaning
            df.dropna(subset=['Sponsor Name', 'Video Creator Name'], inplace=True)
            df = df[df['Sponsor Name'].astype(str).str.strip() != '']
            df = df[df['Video Creator Name'].astype(str).str.strip() != '']
            df['Sponsor Name'] = df['Sponsor Name'].astype(str)
            df['Video Creator Name'] = df['Video Creator Name'].astype(str)
            print(f"Using {len(df)} rows after cleaning.")
            return df
        except Exception as e:
            print(f"Error loading or cleaning data: {e}")
            return None

    def calculate_frequencies(df):
        """Calculates sponsorship frequencies and identifies the strongest link per sponsor."""
        frequencies = df.groupby(['Sponsor Name', 'Video Creator Name']).size().reset_index(name='frequency')

        # Find the maximum frequency for each sponsor
        max_freq_per_sponsor = frequencies.loc[frequencies.groupby('Sponsor Name')['frequency'].idxmax()]
        max_freq_map = max_freq_per_sponsor.set_index(['Sponsor Name', 'Video Creator Name'])['frequency']

        # Determine edge style based on max frequency
        frequencies['is_max'] = frequencies.apply(
            lambda row: row['frequency'] == max_freq_map.get((row['Sponsor Name'], row['Video Creator Name']), -1),
            axis=1
        )
        frequencies['style'] = frequencies['is_max'].apply(lambda x: 'solid' if x else 'dash')

        print(f"Calculated frequencies for {len(frequencies)} unique sponsor-creator pairs.")
        return frequencies

    def build_graph(frequency_data):
        """Builds a NetworkX graph from the frequency data."""
        G = nx.Graph()
        sponsors = frequency_data['Sponsor Name'].unique()
        creators = frequency_data['Video Creator Name'].unique()

        # Add nodes with type attribute
        for sponsor in sponsors:
            G.add_node(sponsor, node_type='sponsor')
        for creator in creators:
            # Avoid adding a node if a creator name is the same as a sponsor name (handle potential overlap)
            if creator not in G:
                 G.add_node(creator, node_type='creator')
            else:
                 # If name exists, ensure it's marked potentially as both if applicable, or prioritize one type?
                 # For now, let's assume distinct roles or handle during visualization if needed.
                 pass 

        # Add edges with attributes
        for _, row in frequency_data.iterrows():
            G.add_edge(row['Sponsor Name'], row['Video Creator Name'], 
                       frequency=row['frequency'], style=row['style'])

        print(f"Built graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        return G

    def visualize_with_plotly(G, output_path):
        """Visualizes the graph using Plotly and saves to HTML."""
        if not G.nodes():
            print("Graph is empty, cannot visualize.")
            return

        # --- Prepare Plotly data ---
        pos = nx.spring_layout(G, k=0.8, iterations=50) # Position nodes using a layout algorithm

        edge_x = []
        edge_y = []
        edge_styles = [] # To store style for each edge segment
        edge_weights = [] # To store frequency for hover text

        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None]) # Add x coordinates for edge segment
            edge_y.extend([y0, y1, None]) # Add y coordinates for edge segment
            edge_styles.append(edge[2]['style']) # Store style ('solid' or 'dash')
            edge_weights.append(edge[2]['frequency']) # Store frequency

        # Create separate traces for solid and dashed lines
        solid_edge_trace = go.Scatter(
            x=[x for i, x in enumerate(edge_x) if edge_styles[i//3] == 'solid'], 
            y=[y for i, y in enumerate(edge_y) if edge_styles[i//3] == 'solid'],
            line=dict(width=1, color='#888'),
            hoverinfo='none',
            mode='lines')

        dash_edge_trace = go.Scatter(
            x=[x for i, x in enumerate(edge_x) if edge_styles[i//3] == 'dash'], 
            y=[y for i, y in enumerate(edge_y) if edge_styles[i//3] == 'dash'],
            line=dict(width=1, color='#888', dash='dash'), # Use dash style
            hoverinfo='none',
            mode='lines')

        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        node_sizes = []

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(f"{node}<br>Type: {G.nodes[node]['node_type']}")
            # Color nodes based on type
            node_colors.append('lightblue' if G.nodes[node]['node_type'] == 'creator' else 'lightcoral')
            # Optional: Size nodes based on degree (number of connections)
            node_sizes.append(G.degree(node) * 3 + 10) # Adjust multiplier for size scaling

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text', # Show markers and text labels
            hoverinfo='text',
            text=list(G.nodes()), # Display node name directly on graph
            textposition="top center",
            marker=dict(
                showscale=False,
                color=node_colors,
                size=node_sizes, # Use calculated sizes
                line_width=1,
                line_color='black'
                ),
            hovertext=node_text # More detailed text on hover
            )

        # --- Create Figure ---
        fig = go.Figure(data=[solid_edge_trace, dash_edge_trace, node_trace],
                     layout=go.Layout(
                        title=dict(text='Interactive Sponsor-Creator Relationship Graph', font=dict(size=16)),
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        annotations=[ dict(
                            text="Nodes: Sponsors (Red), Creators (Blue). Edges: Solid=Strongest Link, Dashed=Other Links.",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002 ) ],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )

        # --- Save/Show Figure ---
        try:
            fig.write_html(output_path)
            print(f"Graph saved successfully to {output_path}")
        except Exception as e:
            print(f"Error saving graph to HTML: {e}")
        # fig.show() # Uncomment to display in a browser window if running interactively

    # --- Main Execution ---
    if __name__ == "__main__":
        print("Starting Phase 2: Graph Generation...")
        df = load_data(CSV_PATH)
        if df is not None and not df.empty:
            frequency_data = calculate_frequencies(df)
            if not frequency_data.empty:
                graph = build_graph(frequency_data)
                visualize_with_plotly(graph, OUTPUT_HTML_PATH)
            else:
                print("No frequency data to build graph.")
        else:
            print("Failed to load or process data. Exiting.")
        print("Phase 2 script finished.")
