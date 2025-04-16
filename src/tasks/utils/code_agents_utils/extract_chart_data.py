def extract_chart_data(ax):
    # Importing inside function, cause this function source goes to e2b executor as string
    import matplotlib.pyplot as plt
    import matplotlib.collections
    import matplotlib.patches
    import plotille

    MAX_DATA_LENGTH = 1000
    chart_info = {
        "type": None,
        "title": ax.get_title(),
        "xlabel": ax.get_xlabel(),
        "ylabel": ax.get_ylabel(),
        "xticks": ax.get_xticks(),
        "yticks": ax.get_yticks(),
        "data": None,
        "ascii": None,
    }
    artists = ax.get_children()  # All elements in the Axes

    # Detect chart type and handle accordingly
    if ax.get_lines():  # Line chart
        chart_info["type"] = "LineChart"
        chart_info["data"] = []
        for line in ax.get_lines():
            data = line.get_xydata()
            label = line.get_label()
            chart_info["data"].append({"label": label, "data": data.tolist()})

        # ASCII representation using plotille
        ascii_representation = ""
        for line_data in chart_info["data"]:
            ascii_representation += f"Label: {line_data['label']}\n"
            ascii_representation += plotille.plot(
                [x[0] for x in line_data["data"]], 
                [x[1] for x in line_data["data"]], 
                height=10, width=30
            )
            ascii_representation += "\n"
        chart_info["ascii"] = ascii_representation

    elif ax.patches and isinstance(artists[0], plt.Rectangle):  # Bar chart
        chart_info["type"] = "BarChart"
        chart_data = []
        max_label_len = 0
        
        for patch, tick in zip(ax.patches, ax.get_xticklabels()):
            label = tick.get_text()
            x = label if isinstance(label, str) else f"{label:.0f}"  
            y = patch.get_height()
            max_label_len = max(max_label_len, len(x))
            chart_data.append({"label": x, "value": y})
        
        # ASCII representation (horizontal bar chart)
        ascii_representation = ""
        max_value = max(item["value"] for item in chart_data)
        scale = 50 / max_value  # Scale bars to fit a max width of 50 characters

        for item in chart_data:
            label = item["label"] 
            value = item["value"]
            bar = "=" * int(value * scale)
            ascii_representation += f"{label.ljust(max_label_len)} |{bar} {value}\n"

        chart_info["ascii"] = ascii_representation

    elif ax.collections and isinstance(ax.collections[0], matplotlib.collections.PathCollection):  # Scatter plot
        chart_info["type"] = "ScatterPlot"
        offsets = ax.collections[0].get_offsets()
        chart_info["data"] = offsets.tolist()

        # ASCII representation using plotille
        x_vals = [point[0] for point in offsets]
        y_vals = [point[1] for point in offsets]
        chart_info["ascii"] = plotille.scatter(x_vals, y_vals, height=10, width=30)

    elif ax.patches and any(isinstance(p, matplotlib.patches.PathPatch) for p in ax.patches):  # Box plot
        chart_info["type"] = "BoxPlot"
        chart_info["data"] = []
        
        # Extract box plot data (box coordinates, whiskers, etc.)
        for i, box in enumerate(ax.patches):
            chart_info["data"].append({
                "box_id": i + 1,
                "coordinates": box.get_bbox().bounds  # (x0, y0, width, height)
            })
        
        # ASCII representation for Box Plot (simplified for text-based representation)
        ascii_representation = ""
        for box_data in chart_info["data"]:
            x0, y0, width, height = box_data["coordinates"]
            ascii_representation += f"Box {box_data['box_id']} - Position: ({x0}, {y0}), Size: ({width}, {height})\n"
            ascii_representation += f"Whiskers: Min: {y0}, Max: {y0 + height}\n"  # Simplified whisker data
        chart_info["ascii"] = ascii_representation

    elif ax.images:  # Heatmap
        chart_info["type"] = "Heatmap"
        heatmap_data = ax.images[0].get_array().data  # Heatmap data
        x_labels = [tick.get_text() for tick in ax.get_xticklabels()]
        y_labels = [tick.get_text() for tick in ax.get_yticklabels()]
        heatmap_data = {
            "values": heatmap_data.tolist(),
            "x_labels": x_labels,
            "y_labels": y_labels,
        }
        rounded_values = [[f"{val:.4f}" for val in row] for row in heatmap_data['values']]
        col_widths = [max(len(val) for val in col) for col in zip(*rounded_values)]
        col_widths = [max(len(label), width) for label, width in zip(heatmap_data['x_labels'], col_widths)]
        header = "      | " + " | ".join(f"{label:^{width}}" for label, width in zip(heatmap_data['x_labels'], col_widths)) + " |"
        rows = []
        for y_label, row_values in zip(heatmap_data['y_labels'], rounded_values):
            row = f"{y_label:<5} | " + " | ".join(f"{val:^{col_widths[i]}}" for i, val in enumerate(row_values)) + " |"
            rows.append(row)

        # Combine everything into a ascii chart
        chart_info['ascii'] = "\n".join([header, "-" * len(header)] + rows)

    elif isinstance(artists[0], matplotlib.patches.Wedge):  # Pie chart
        chart_info["type"] = "PieChart"
        
        wedges = ax.patches
        texts = ax.texts  

        # Extract the label and percentage from texts
        chart_data = [
            {
                "label": texts[i].get_text(),  
                "percentage": texts[i + 1].get_text()  
            }
            for i in range(0, len(texts), 2)
        ]

        ascii_representation = ""
        for entry in chart_data:
            ascii_representation += f"Label: {entry['label']} Value: {entry['percentage']}\n"

        chart_info["ascii"] = ascii_representation


    else:  # Unsupported chart type
        chart_info["type"] = "Could't detect"
        chart_info["data"] = {
            "all_artists": [str(artist) for artist in artists]
        }
        chart_info["ascii"] = """This function is unable to detect and create ascii representation of provided graph, If you only wish to create and save the plot, it's done. Your next steps should be:

        - try solving task without the plot if possible
        - try making simpler graph
        - try with different approach for next few (2-3) iterations.
        """

    # Remove data if it's too long
    if len(str(chart_info['data'])) > MAX_DATA_LENGTH:
        chart_info['data'] = None
    
    return chart_info

def format_chart_info(chart_data):
    formatted_output = "\n-----------------------------------------------\n"\
    
    # Add chart type and title
    formatted_output += f"Type: {chart_data.get('type')}\n"
    if "title" in chart_data and chart_data["title"]:
        formatted_output += f"Title: {chart_data['title']}\n"
    
    # Add axis labels
    if "xlabel" in chart_data and chart_data['xlabel']:
        formatted_output += f"X-Axis Label: {chart_data['xlabel']}\n"
    if "ylabel" in chart_data and chart_data['ylabel']:
        formatted_output += f"Y-Axis Label: {chart_data['ylabel']}\n"

    if "data" in chart_data and chart_data['data']:
        formatted_output += f"Plot Data: {chart_data['data']}\n"
       
    
    # Add ASCII representation
    if "ascii" in chart_data and chart_data["ascii"]:
        formatted_output += "\nASCII Representation:\n"
        formatted_output += chart_data["ascii"]
    formatted_output += "\n-----------------------------------------------\n"
    return formatted_output
