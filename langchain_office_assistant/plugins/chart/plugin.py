from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from langchain_office_assistant.plugins.base import BasePlugin
from langchain_office_assistant.utils.logger import get_logger
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.io as pio
import pandas as pd
import numpy as np

logger = get_logger(__name__)

class ChartPlugin(BasePlugin):
    name = "chart"
    description = "图表插件 - 折线图、柱状图、雷达图等"
    
    def __init__(self):
        super().__init__()
    
    def initialize(self, config: Dict) -> None:
        self.config = config
        plt.switch_backend('Agg')
        logger.info(f"ChartPlugin initialized")
    
    def get_tools(self) -> List:
        return [create_bar_chart, create_line_chart, create_pie_chart, create_radar_chart, create_scatter_plot]
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        tools_map = {
            "create_bar_chart": create_bar_chart,
            "create_line_chart": create_line_chart,
            "create_pie_chart": create_pie_chart,
            "create_radar_chart": create_radar_chart,
            "create_scatter_plot": create_scatter_plot,
        }
        
        if tool_name not in tools_map:
            return f"❌ Tool not found: {tool_name}"
        
        tool_func = tools_map[tool_name]
        return tool_func(**kwargs)

@tool
def create_bar_chart(
    title: str,
    labels: List[str],
    values: List[float],
    file_path: str = "chart.png",
    color: str = "blue"
) -> str:
    try:
        plt.figure(figsize=(10, 6))
        bars = plt.bar(labels, values, color=color)
        
        plt.title(title, fontsize=14)
        plt.xlabel("Categories", fontsize=12)
        plt.ylabel("Values", fontsize=12)
        plt.xticks(rotation=45)
        
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Bar chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Categories: {', '.join(labels)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_line_chart(
    title: str,
    x_data: List[str],
    y_data: List[float],
    file_path: str = "chart.png",
    color: str = "blue",
    show_markers: bool = True
) -> str:
    try:
        plt.figure(figsize=(10, 6))
        plt.plot(x_data, y_data, color=color, marker='o' if show_markers else None, linewidth=2)
        
        plt.title(title, fontsize=14)
        plt.xlabel("X Axis", fontsize=12)
        plt.ylabel("Y Axis", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Line chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Data points: {len(x_data)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_pie_chart(
    title: str,
    labels: List[str],
    values: List[float],
    file_path: str = "chart.png"
) -> str:
    try:
        plt.figure(figsize=(8, 8))
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title(title, fontsize=14)
        plt.axis('equal')
        
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Pie chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Categories: {', '.join(labels)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_radar_chart(
    title: str,
    categories: List[str],
    values: List[float],
    file_path: str = "chart.png"
) -> str:
    try:
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=title
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(values) * 1.2]
                )),
            title=title,
            showlegend=True
        )
        
        pio.write_image(fig, file_path)
        
        return f"✅ Radar chart created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Dimensions: {len(categories)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"

@tool
def create_scatter_plot(
    title: str,
    x_data: List[float],
    y_data: List[float],
    file_path: str = "chart.png",
    color: str = "blue"
) -> str:
    try:
        plt.figure(figsize=(10, 6))
        plt.scatter(x_data, y_data, color=color, s=100, alpha=0.7)
        
        z = np.polyfit(x_data, y_data, 1)
        p = np.poly1d(z)
        plt.plot(x_data, p(x_data), "r--")
        
        plt.title(title, fontsize=14)
        plt.xlabel("X Values", fontsize=12)
        plt.ylabel("Y Values", fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        plt.savefig(file_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return f"✅ Scatter plot created!\n\n📊 Title: {title}\n📄 File: {file_path}\n📈 Data points: {len(x_data)}"
    except Exception as e:
        return f"❌ Failed to create chart: {str(e)}"