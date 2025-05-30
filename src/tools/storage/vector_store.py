"""
向量存储工具
实现基于Chroma的向量存储和检索
"""
import chromadb
from typing import List, Optional, Dict, Any
from sentence_transformers import SentenceTransformer
from langchain.callbacks.manager import CallbackManagerForToolRun
import json

from ..base import StorageTool, ToolResult
from ...core.models import ContentItem
from ...core.config import config
from ...core.exceptions import VectorStoreException


class ChromaVectorStoreTool(StorageTool):
    """Chroma向量存储工具"""
    
    name = "chroma_vector_store"
    description = "使用Chroma进行向量存储和语义搜索"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 初始化Chroma客户端
        self.client = chromadb.PersistentClient(
            path=str(config.data_dir / "chroma_db")
        )
        
        # 初始化embedding模型
        self.embedding_model = SentenceTransformer(
            config.vector_store.embedding_model
        )
        
        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name="news_content",
            metadata={"description": "AI新闻内容向量存储"}
        )
        
        self.logger.info(f"Chroma向量存储初始化完成，集合文档数量: {self.collection.count()}")
    
    def _execute(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> ToolResult:
        """执行向量搜索"""
        try:
            results = self.search_content(query, n_results=10)
            
            return ToolResult(
                success=True,
                data=results,
                metadata={
                    "query": query,
                    "total_results": len(results),
                    "collection_size": self.collection.count()
                }
            )
        except Exception as e:
            raise VectorStoreException(f"向量搜索失败: {str(e)}")
    
    def store_content(self, content: ContentItem) -> str:
        """存储内容项到向量数据库"""
        try:
            # 生成embedding
            text_to_embed = self._prepare_text_for_embedding(content)
            embedding = self.embedding_model.encode(text_to_embed).tolist()
            
            # 准备元数据
            metadata = {
                "title": content.title,
                "source_name": content.source_name,
                "content_type": content.content_type.value,
                "published_at": content.published_at.isoformat(),
                "quality_score": content.quality_score,
                "url": content.url,
                "authors": json.dumps(content.authors),
                "categories": json.dumps(content.categories),
                "tags": json.dumps(content.tags)
            }
            
            # 存储到Chroma
            self.collection.add(
                ids=[content.id],
                embeddings=[embedding],
                documents=[text_to_embed],
                metadatas=[metadata]
            )
            
            self.logger.info(f"内容已存储到向量数据库: {content.id}")
            return content.id
            
        except Exception as e:
            self.logger.error(f"向量存储失败: {str(e)}")
            raise VectorStoreException(f"存储内容失败: {str(e)}")
    
    def retrieve_content(self, content_id: str) -> Optional[ContentItem]:
        """根据ID检索内容"""
        try:
            results = self.collection.get(
                ids=[content_id],
                include=["documents", "metadatas"]
            )
            
            if not results["ids"]:
                return None
            
            # 重构ContentItem（简化版本，主要用于搜索结果）
            metadata = results["metadatas"][0]
            document = results["documents"][0]
            
            return ContentItem(
                id=content_id,
                title=metadata["title"],
                content=document,
                url=metadata["url"],
                content_type=metadata["content_type"],
                source_id="",  # 这里需要从其他地方获取
                source_name=metadata["source_name"],
                authors=json.loads(metadata.get("authors", "[]")),
                categories=json.loads(metadata.get("categories", "[]")),
                tags=json.loads(metadata.get("tags", "[]")),
                published_at=datetime.fromisoformat(metadata["published_at"]),
                quality_score=metadata.get("quality_score", 0.0)
            )
            
        except Exception as e:
            self.logger.error(f"内容检索失败: {str(e)}")
            raise VectorStoreException(f"检索内容失败: {str(e)}")
    
    def search_content(
        self,
        query: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """语义搜索内容"""
        try:
            # 生成查询embedding
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # 执行搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # 格式化结果
            search_results = []
            for i, doc_id in enumerate(results["ids"][0]):
                result = {
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # 转换距离为相似度
                }
                search_results.append(result)
            
            self.logger.info(f"向量搜索完成，查询: '{query}', 结果数量: {len(search_results)}")
            return search_results
            
        except Exception as e:
            self.logger.error(f"向量搜索失败: {str(e)}")
            raise VectorStoreException(f"搜索失败: {str(e)}")
    
    def search_similar_content(
        self,
        content_item: ContentItem,
        n_results: int = 5,
        exclude_self: bool = True
    ) -> List[Dict[str, Any]]:
        """查找相似内容"""
        try:
            # 生成内容的embedding
            text_to_embed = self._prepare_text_for_embedding(content_item)
            embedding = self.embedding_model.encode(text_to_embed).tolist()
            
            # 执行相似性搜索
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=n_results + (1 if exclude_self else 0),
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            for i, doc_id in enumerate(results["ids"][0]):
                # 排除自身
                if exclude_self and doc_id == content_item.id:
                    continue
                
                result = {
                    "id": doc_id,
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],
                }
                search_results.append(result)
            
            return search_results[:n_results]
            
        except Exception as e:
            self.logger.error(f"相似内容搜索失败: {str(e)}")
            raise VectorStoreException(f"相似内容搜索失败: {str(e)}")
    
    def delete_content(self, content_id: str) -> bool:
        """删除内容"""
        try:
            self.collection.delete(ids=[content_id])
            self.logger.info(f"内容已从向量数据库删除: {content_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除内容失败: {str(e)}")
            return False
    
    def update_content(self, content: ContentItem) -> bool:
        """更新内容"""
        try:
            # 先删除旧内容
            self.delete_content(content.id)
            # 再添加新内容
            self.store_content(content)
            return True
            
        except Exception as e:
            self.logger.error(f"更新内容失败: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """获取集合统计信息"""
        try:
            count = self.collection.count()
            
            # 获取一些样本数据来分析
            sample_results = self.collection.get(
                limit=min(100, count),
                include=["metadatas"]
            )
            
            # 统计内容类型分布
            content_types = {}
            sources = {}
            
            for metadata in sample_results.get("metadatas", []):
                content_type = metadata.get("content_type", "unknown")
                source_name = metadata.get("source_name", "unknown")
                
                content_types[content_type] = content_types.get(content_type, 0) + 1
                sources[source_name] = sources.get(source_name, 0) + 1
            
            return {
                "total_documents": count,
                "content_type_distribution": content_types,
                "source_distribution": sources,
                "embedding_dimension": config.vector_store.vector_dimension
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {"error": str(e)}
    
    def _prepare_text_for_embedding(self, content: ContentItem) -> str:
        """准备用于embedding的文本"""
        # 组合标题、摘要和部分内容
        text_parts = [content.title]
        
        if content.summary:
            text_parts.append(content.summary)
        
        # 截取内容的前1000个字符
        if content.content:
            text_parts.append(content.content[:1000])
        
        # 添加作者和标签信息
        if content.authors:
            text_parts.append(f"作者: {', '.join(content.authors)}")
        
        if content.tags:
            text_parts.append(f"标签: {', '.join(content.tags)}")
        
        return "\n".join(text_parts)
