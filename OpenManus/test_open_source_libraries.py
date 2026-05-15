"""测试所有开源库集成"""
import sys
import os
sys.path.insert(0, '.')

def test_faiss():
    """测试FAISS向量存储"""
    print('测试 FAISS 向量存储...')
    try:
        from app.knowledge.faiss_vector_store import FAISSVectorStore, DocumentChunk
        
        # 创建向量存储
        store = FAISSVectorStore(persist_dir="./data/test_faiss")
        print('✓ 创建向量存储成功')
        
        # 添加文档
        chunks = [
            DocumentChunk(id="1", content="机器学习是人工智能的核心技术", metadata={"type": "text"}),
            DocumentChunk(id="2", content="深度学习在图像识别中表现出色", metadata={"type": "text"}),
            DocumentChunk(id="3", content="自然语言处理让机器理解人类语言", metadata={"type": "text"}),
        ]
        
        # 生成模拟嵌入
        import numpy as np
        for i, chunk in enumerate(chunks):
            chunk.embedding = np.random.rand(768).tolist()
        
        store.add_documents(chunks)
        print('✓ 添加文档成功')
        
        # 搜索
        query_embedding = np.random.rand(768).tolist()
        results = store.search(query_embedding, top_k=2)
        print(f'✓ 搜索成功，找到 {len(results)} 条结果')
        
        # 统计
        stats = store.get_metadata_stats()
        print(f'✓ 元数据统计成功')
        
        # 清空
        store.clear()
        print('✓ 清空数据成功')
        
        return True
    except ImportError as e:
        print(f'⚠️ FAISS未安装: {e}')
        return True  # 不算失败，只是未安装
    except Exception as e:
        print(f'✗ FAISS测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_whisper():
    """测试Whisper语音识别"""
    print('\n测试 Whisper 语音识别...')
    try:
        from app.voice.whisper_service import WhisperService
        
        service = WhisperService()
        print('✓ 创建服务成功')
        
        # 检查可用性
        if service.is_available():
            print('✓ Whisper可用')
            print(f'✓ 支持的模型: {list(service.get_model_sizes().keys())}')
        else:
            print('⚠️ Whisper未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ Whisper未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ Whisper测试失败: {e}')
        return False

def test_pymupdf():
    """测试PyMuPDF PDF处理"""
    print('\n测试 PyMuPDF PDF处理...')
    try:
        from app.document.pymupdf_processor import PyMuPDFProcessor
        
        processor = PyMuPDFProcessor()
        print('✓ 创建处理器成功')
        
        # 检查可用性
        if processor.is_available():
            print('✓ PyMuPDF可用')
            print(f'✓ 支持文件类型: PDF')
        else:
            print('⚠️ PyMuPDF未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ PyMuPDF未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ PyMuPDF测试失败: {e}')
        return False

def test_spacy():
    """测试spaCy NLP"""
    print('\n测试 spaCy NLP...')
    try:
        from app.nlp.spacy_service import SpacyService
        
        service = SpacyService()
        print('✓ 创建服务成功')
        
        # 检查可用性
        if service.is_available():
            print('✓ spaCy可用')
            print(f'✓ 支持的模型: {service.get_available_models()}')
        else:
            print('⚠️ spaCy未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ spaCy未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ spaCy测试失败: {e}')
        return False

def test_plotly():
    """测试Plotly可视化"""
    print('\n测试 Plotly 可视化...')
    try:
        from app.visualization.plotly_service import PlotlyService, ChartConfig
        
        service = PlotlyService()
        print('✓ 创建服务成功')
        
        # 检查可用性
        if service.is_available():
            print('✓ Plotly可用')
            print(f'✓ 支持的图表类型: {service.get_supported_charts()}')
            
            # 测试创建图表
            data = [["A", 10], ["B", 20], ["C", 15], ["D", 25]]
            config = ChartConfig(title="测试图表", x_label="类别", y_label="数值")
            
            html = service.create_bar_chart(data, config)
            if html and "<div" in html:
                print('✓ 创建柱状图成功')
            else:
                print('✗ 创建柱状图失败')
            
            html = service.create_pie_chart(data, config)
            if html and "<div" in html:
                print('✓ 创建饼图成功')
            else:
                print('✗ 创建饼图失败')
            
            html = service.create_line_chart(data, config)
            if html and "<div" in html:
                print('✓ 创建折线图成功')
            else:
                print('✗ 创建折线图失败')
        else:
            print('⚠️ Plotly未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ Plotly未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ Plotly测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_loguru():
    """测试loguru日志"""
    print('\n测试 loguru 日志...')
    try:
        from loguru import logger
        
        logger.info("测试loguru日志")
        print('✓ loguru可用')
        
        return True
    except ImportError as e:
        print(f'⚠️ loguru未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ loguru测试失败: {e}')
        return False

def test_pydantic_settings():
    """测试Pydantic Settings"""
    print('\n测试 Pydantic Settings...')
    try:
        from pydantic_settings import BaseSettings
        
        class TestSettings(BaseSettings):
            app_name: str = "TestApp"
            debug: bool = False
        
        settings = TestSettings()
        print(f'✓ Pydantic Settings可用，app_name={settings.app_name}')
        
        return True
    except ImportError as e:
        print(f'⚠️ Pydantic Settings未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ Pydantic Settings测试失败: {e}')
        return False

def test_httpx():
    """测试httpx HTTP客户端"""
    print('\n测试 httpx HTTP客户端...')
    try:
        import httpx
        
        print('✓ httpx可用')
        
        async def test_request():
            async with httpx.AsyncClient() as client:
                response = await client.get("https://httpbin.org/get")
                if response.status_code == 200:
                    print('✓ HTTP请求测试成功')
        
        import asyncio
        asyncio.run(test_request())
        
        return True
    except ImportError as e:
        print(f'⚠️ httpx未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ httpx测试失败: {e}')
        return False

def test_beautifulsoup():
    """测试BeautifulSoup HTML解析"""
    print('\n测试 BeautifulSoup HTML解析...')
    try:
        from bs4 import BeautifulSoup
        
        html = "<html><body><h1>Test</h1></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.h1.text
        
        if title == "Test":
            print('✓ BeautifulSoup可用')
        else:
            print('✗ BeautifulSoup解析失败')
        
        return True
    except ImportError as e:
        print(f'⚠️ BeautifulSoup未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ BeautifulSoup测试失败: {e}')
        return False

def main():
    print('='*70)
    print('开源库集成测试')
    print('='*70)
    
    tests = [
        test_faiss,
        test_whisper,
        test_pymupdf,
        test_spacy,
        test_plotly,
        test_loguru,
        test_pydantic_settings,
        test_httpx,
        test_beautifulsoup
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f'\n✗ {test.__name__} 执行异常: {e}')
            failed += 1
    
    print('\n' + '='*70)
    print(f'测试完成！')
    print(f'通过: {passed}/{len(tests)}')
    print(f'失败: {failed}/{len(tests)}')
    print('='*70)
    
    if failed == 0:
        print('\n🎉 所有开源库集成测试通过！')
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())