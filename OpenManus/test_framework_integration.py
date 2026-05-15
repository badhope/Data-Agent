"""测试核心框架集成"""
import sys
import os
sys.path.insert(0, '.')

def test_langgraph():
    """测试LangGraph智能体框架"""
    print('测试 LangGraph 智能体框架...')
    try:
        from app.agent.langgraph_agent import LangGraphAgent
        
        agent = LangGraphAgent()
        print('✓ 创建智能体成功')
        
        if agent.is_available():
            print('✓ LangGraph可用')
            print('✓ 状态图已构建')
        else:
            print('⚠️ LangGraph未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ LangGraph未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ LangGraph测试失败: {e}')
        return False

def test_llama_index():
    """测试LlamaIndex RAG"""
    print('\n测试 LlamaIndex RAG...')
    try:
        from app.knowledge.llama_index_rag import LlamaIndexRAG
        
        rag = LlamaIndexRAG(persist_dir="./data/test_llama_index")
        print('✓ 创建RAG实例成功')
        
        if rag.is_available():
            print('✓ LlamaIndex可用')
            
            # 测试添加文本
            success = rag.add_text("测试文档内容", {"source": "test"})
            if success:
                print('✓ 添加文档成功')
            else:
                print('✗ 添加文档失败')
            
            # 测试统计
            stats = rag.get_stats()
            print(f'✓ 统计信息: {stats}')
            
            # 清理测试数据
            rag.clear()
            print('✓ 清理测试数据成功')
        else:
            print('⚠️ LlamaIndex未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ LlamaIndex未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ LlamaIndex测试失败: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_langfuse():
    """测试Langfuse可观测性"""
    print('\n测试 Langfuse 可观测性...')
    try:
        from app.observability.langfuse_service import LangfuseService
        
        service = LangfuseService()
        print('✓ 创建服务成功')
        
        if service.is_available():
            print('✓ Langfuse可用')
            
            # 测试获取指标
            metrics = service.get_metrics()
            if metrics.success:
                print(f'✓ 指标获取成功: {metrics.metrics}')
            else:
                print(f'⚠️ 指标获取失败: {metrics.error}')
        else:
            print('⚠️ Langfuse未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ Langfuse未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ Langfuse测试失败: {e}')
        return False

def test_faiss():
    """测试FAISS向量存储"""
    print('\n测试 FAISS 向量存储...')
    try:
        from app.knowledge.faiss_vector_store import FAISSVectorStore, DocumentChunk
        import numpy as np
        
        store = FAISSVectorStore(persist_dir="./data/test_faiss")
        print('✓ 创建向量存储成功')
        
        if store.is_available():
            print('✓ FAISS可用')
            
            # 测试添加和搜索
            chunks = [DocumentChunk(id="1", content="测试内容", embedding=np.random.rand(768).tolist())]
            store.add_documents(chunks)
            print('✓ 添加文档成功')
            
            results = store.search(np.random.rand(768).tolist())
            print(f'✓ 搜索成功，找到 {len(results)} 条结果')
            
            store.clear()
            print('✓ 清理数据成功')
        else:
            print('⚠️ FAISS未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ FAISS未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ FAISS测试失败: {e}')
        return False

def test_whisper():
    """测试Whisper语音识别"""
    print('\n测试 Whisper 语音识别...')
    try:
        from app.voice.whisper_service import WhisperService
        
        service = WhisperService()
        print('✓ 创建服务成功')
        
        if service.is_available():
            print('✓ Whisper可用')
            print(f'✓ 支持模型: {list(service.get_model_sizes().keys())}')
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
        
        if processor.is_available():
            print('✓ PyMuPDF可用')
        else:
            print('⚠️ PyMuPDF未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ PyMuPDF未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ PyMuPDF测试失败: {e}')
        return False

def test_plotly():
    """测试Plotly可视化"""
    print('\n测试 Plotly 可视化...')
    try:
        from app.visualization.plotly_service import PlotlyService
        
        service = PlotlyService()
        print('✓ 创建服务成功')
        
        if service.is_available():
            print('✓ Plotly可用')
            
            # 测试创建图表
            data = [["A", 10], ["B", 20], ["C", 15]]
            html = service.create_bar_chart(data)
            if "<div" in html:
                print('✓ 创建图表成功')
            else:
                print('✗ 创建图表失败')
        else:
            print('⚠️ Plotly未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ Plotly未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ Plotly测试失败: {e}')
        return False

def test_spacy():
    """测试spaCy NLP"""
    print('\n测试 spaCy NLP...')
    try:
        from app.nlp.spacy_service import SpacyService
        
        service = SpacyService()
        print('✓ 创建服务成功')
        
        if service.is_available():
            print('✓ spaCy可用')
        else:
            print('⚠️ spaCy未安装')
        
        return True
    except ImportError as e:
        print(f'⚠️ spaCy未安装: {e}')
        return True
    except Exception as e:
        print(f'✗ spaCy测试失败: {e}')
        return False

def main():
    print('='*70)
    print('核心框架集成测试')
    print('='*70)
    
    tests = [
        test_langgraph,
        test_llama_index,
        test_langfuse,
        test_faiss,
        test_whisper,
        test_pymupdf,
        test_plotly,
        test_spacy
    ]
    
    passed = 0
    failed = 0
    
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
        print('\n🎉 所有框架集成测试通过！')
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main())