"""Plotly可视化服务 - 使用Plotly实现交互式图表"""
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

@dataclass
class ChartConfig:
    """图表配置"""
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    show_legend: bool = True
    show_labels: bool = False
    color_scheme: str = "viridis"

class PlotlyService:
    """Plotly可视化服务"""
    
    def __init__(self):
        if not PLOTLY_AVAILABLE:
            print("警告: Plotly未安装，图表功能可能受限")
    
    def create_bar_chart(self, data: List[List], config: Optional[ChartConfig] = None) -> str:
        """
        创建柱状图
        
        Args:
            data: 数据列表，格式为 [[标签1, 值1], [标签2, 值2], ...]
            config: 图表配置
        
        Returns:
            str: 图表HTML字符串
        """
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly未安装，请安装: pip install plotly pandas</p>"
        
        config = config or ChartConfig()
        
        try:
            labels = [row[0] for row in data]
            values = [row[1] for row in data]
            
            fig = px.bar(
                x=labels,
                y=values,
                title=config.title,
                labels={'x': config.x_label, 'y': config.y_label},
                color_discrete_sequence=px.colors.sequential[config.color_scheme]
            )
            
            fig.update_layout(
                showlegend=config.show_legend,
                font=dict(size=12),
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            if config.show_labels:
                fig.update_traces(text=values, textposition='outside')
            
            return fig.to_html(full_html=False)
        
        except Exception as e:
            return f"<p>创建柱状图失败: {str(e)}</p>"
    
    def create_line_chart(self, data: List[List], config: Optional[ChartConfig] = None) -> str:
        """
        创建折线图
        
        Args:
            data: 数据列表，格式为 [[标签1, 值1], [标签2, 值2], ...]
            config: 图表配置
        
        Returns:
            str: 图表HTML字符串
        """
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly未安装</p>"
        
        config = config or ChartConfig()
        
        try:
            labels = [row[0] for row in data]
            values = [row[1] for row in data]
            
            fig = px.line(
                x=labels,
                y=values,
                title=config.title,
                labels={'x': config.x_label, 'y': config.y_label},
                markers=True
            )
            
            fig.update_layout(
                showlegend=config.show_legend,
                font=dict(size=12),
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            if config.show_labels:
                fig.update_traces(text=values, textposition='top center')
            
            return fig.to_html(full_html=False)
        
        except Exception as e:
            return f"<p>创建折线图失败: {str(e)}</p>"
    
    def create_pie_chart(self, data: List[List], config: Optional[ChartConfig] = None) -> str:
        """
        创建饼图
        
        Args:
            data: 数据列表，格式为 [[标签1, 值1], [标签2, 值2], ...]
            config: 图表配置
        
        Returns:
            str: 图表HTML字符串
        """
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly未安装</p>"
        
        config = config or ChartConfig()
        
        try:
            labels = [row[0] for row in data]
            values = [row[1] for row in data]
            
            fig = px.pie(
                values=values,
                names=labels,
                title=config.title,
                color_discrete_sequence=px.colors.sequential[config.color_scheme]
            )
            
            fig.update_layout(
                showlegend=config.show_legend,
                font=dict(size=12),
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            if config.show_labels:
                fig.update_traces(textposition='inside', textinfo='percent+label')
            
            return fig.to_html(full_html=False)
        
        except Exception as e:
            return f"<p>创建饼图失败: {str(e)}</p>"
    
    def create_scatter_plot(self, data: List[List], config: Optional[ChartConfig] = None) -> str:
        """
        创建散点图
        
        Args:
            data: 数据列表，格式为 [[x1, y1], [x2, y2], ...]
            config: 图表配置
        
        Returns:
            str: 图表HTML字符串
        """
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly未安装</p>"
        
        config = config or ChartConfig()
        
        try:
            x_values = [row[0] for row in data]
            y_values = [row[1] for row in data]
            
            fig = px.scatter(
                x=x_values,
                y=y_values,
                title=config.title,
                labels={'x': config.x_label, 'y': config.y_label}
            )
            
            fig.update_layout(
                showlegend=config.show_legend,
                font=dict(size=12),
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            return fig.to_html(full_html=False)
        
        except Exception as e:
            return f"<p>创建散点图失败: {str(e)}</p>"
    
    def create_histogram(self, data: List[float], config: Optional[ChartConfig] = None) -> str:
        """
        创建直方图
        
        Args:
            data: 数值列表
            config: 图表配置
        
        Returns:
            str: 图表HTML字符串
        """
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly未安装</p>"
        
        config = config or ChartConfig()
        
        try:
            fig = px.histogram(
                x=data,
                title=config.title,
                labels={'x': config.x_label, 'y': config.y_label}
            )
            
            fig.update_layout(
                showlegend=config.show_legend,
                font=dict(size=12),
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            return fig.to_html(full_html=False)
        
        except Exception as e:
            return f"<p>创建直方图失败: {str(e)}</p>"
    
    def create_table(self, data: List[List], headers: List[str] = None) -> str:
        """
        创建表格
        
        Args:
            data: 数据列表
            headers: 表头列表
        
        Returns:
            str: 表格HTML字符串
        """
        if not PLOTLY_AVAILABLE:
            return "<p>Plotly未安装</p>"
        
        try:
            fig = go.Figure(data=[go.Table(
                header=dict(values=headers if headers else ['列1', '列2', '列3']),
                cells=dict(values=[[row[i] for row in data] for i in range(len(data[0]))])
            )])
            
            fig.update_layout(
                margin=dict(l=10, r=10, t=10, b=10),
                font=dict(size=11)
            )
            
            return fig.to_html(full_html=False)
        
        except Exception as e:
            return f"<p>创建表格失败: {str(e)}</p>"
    
    def create_chart(self, chart_type: str, data: List[List], config: Optional[ChartConfig] = None) -> str:
        """
        根据类型创建图表
        
        Args:
            chart_type: 图表类型 (bar, line, pie, scatter, histogram, table)
            data: 数据列表
            config: 图表配置
        
        Returns:
            str: 图表HTML字符串
        """
        chart_type = chart_type.lower()
        
        if chart_type == 'bar':
            return self.create_bar_chart(data, config)
        elif chart_type == 'line':
            return self.create_line_chart(data, config)
        elif chart_type == 'pie':
            return self.create_pie_chart(data, config)
        elif chart_type == 'scatter':
            return self.create_scatter_plot(data, config)
        elif chart_type == 'histogram':
            return self.create_histogram([row[1] for row in data], config)
        elif chart_type == 'table':
            return self.create_table(data)
        else:
            return f"<p>不支持的图表类型: {chart_type}</p>"
    
    def export_to_image(self, chart_html: str, output_path: str, format: str = 'png') -> bool:
        """
        导出图表为图片
        
        Args:
            chart_html: 图表HTML字符串
            output_path: 输出路径
            format: 输出格式 (png, jpeg, webp, svg)
        
        Returns:
            bool: 是否成功
        """
        if not PLOTLY_AVAILABLE:
            return False
        
        try:
            # 需要安装kaleido
            from kaleido.scopes.plotly import PlotlyScope
            scope = PlotlyScope()
            scope.transform(chart_html, format=format, path=output_path)
            return True
        except ImportError:
            print("需要安装kaleido: pip install kaleido")
            return False
        except Exception as e:
            print(f"导出图片失败: {e}")
            return False
    
    def get_chart_json(self, chart_type: str, data: List[List], config: Optional[ChartConfig] = None) -> str:
        """
        获取图表JSON配置
        
        Args:
            chart_type: 图表类型
            data: 数据列表
            config: 图表配置
        
        Returns:
            str: JSON字符串
        """
        if not PLOTLY_AVAILABLE:
            return json.dumps({'error': 'Plotly未安装'})
        
        try:
            config = config or ChartConfig()
            
            if chart_type.lower() == 'bar':
                fig = px.bar(
                    x=[row[0] for row in data],
                    y=[row[1] for row in data],
                    title=config.title
                )
            elif chart_type.lower() == 'line':
                fig = px.line(
                    x=[row[0] for row in data],
                    y=[row[1] for row in data],
                    title=config.title
                )
            elif chart_type.lower() == 'pie':
                fig = px.pie(
                    values=[row[1] for row in data],
                    names=[row[0] for row in data],
                    title=config.title
                )
            else:
                return json.dumps({'error': f'不支持的图表类型: {chart_type}'})
            
            return json.dumps(fig.to_dict())
        
        except Exception as e:
            return json.dumps({'error': str(e)})
    
    @staticmethod
    def is_available() -> bool:
        """检查Plotly是否可用"""
        return PLOTLY_AVAILABLE
    
    @staticmethod
    def get_supported_charts() -> List[str]:
        """获取支持的图表类型"""
        return ['bar', 'line', 'pie', 'scatter', 'histogram', 'table']

# 全局实例
plotly_service = None

def get_plotly_service() -> PlotlyService:
    """获取全局Plotly服务实例"""
    global plotly_service
    if plotly_service is None:
        plotly_service = PlotlyService()
    return plotly_service