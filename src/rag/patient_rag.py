import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class PatientContextRAG:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model_name: str = "gpt-4",
        embedding_model: str = "text-embedding-ada-002",
        chroma_persist_directory: str = "./chroma_db"
    ):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.openai_api_key:
            logger.warning("OpenAI API key not provided, using local embeddings only")
            self.use_openai = False
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        else:
            self.use_openai = True
            self.llm = ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model_name=model_name,
                temperature=0.1
            )
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.openai_api_key,
                model=embedding_model
            )
        
        self.chroma_client = chromadb.PersistentClient(path=chroma_persist_directory)
        self.collection_name = "patient_clinical_data"
        
        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
        
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=5,
            return_messages=True
        )
        
    def create_patient_summary_prompt(self):
        return PromptTemplate(
            input_variables=["patient_context", "clinical_question"],
            template="""
You are a clinical AI assistant helping healthcare providers understand patient conditions and make informed decisions.

Patient Context:
{patient_context}

Clinical Question: {clinical_question}

Based on the patient context provided, please provide:

1. **Clinical Assessment**: A concise summary of the patient's current condition
2. **Risk Factors**: Key risk factors for deterioration based on the available data
3. **Recommendations**: Specific clinical recommendations or interventions to consider
4. **Monitoring**: Important parameters to monitor closely

Please be specific, evidence-based, and focus on actionable insights. If certain information is missing, indicate what additional data would be helpful.

Response:"""
        )
    
    def embed_patient_data(
        self,
        patient_id: str,
        demographics: Dict[str, Any],
        vitals_history: List[Dict[str, Any]],
        clinical_notes: List[str],
        lab_results: List[Dict[str, Any]] = None
    ):
        """Embed patient data into the vector database"""
        
        documents = []
        
        demographics_text = self._format_demographics(demographics)
        documents.append(Document(
            page_content=demographics_text,
            metadata={
                "patient_id": patient_id,
                "data_type": "demographics",
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        vitals_summary = self._format_vitals_summary(vitals_history)
        documents.append(Document(
            page_content=vitals_summary,
            metadata={
                "patient_id": patient_id,
                "data_type": "vitals_summary",
                "timestamp": datetime.utcnow().isoformat()
            }
        ))
        
        for i, note in enumerate(clinical_notes):
            if note and len(note.strip()) > 0:
                documents.append(Document(
                    page_content=note,
                    metadata={
                        "patient_id": patient_id,
                        "data_type": "clinical_note",
                        "note_index": i,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                ))
        
        if lab_results:
            lab_summary = self._format_lab_results(lab_results)
            documents.append(Document(
                page_content=lab_summary,
                metadata={
                    "patient_id": patient_id,
                    "data_type": "lab_results",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ))
        
        if self.use_openai:
            embeddings = self.embeddings.embed_documents([doc.page_content for doc in documents])
        else:
            embeddings = self.embedding_model.encode([doc.page_content for doc in documents]).tolist()
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = f"{patient_id}_{doc.metadata['data_type']}_{i}"
            
            self.collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[doc.page_content],
                metadatas=[doc.metadata]
            )
        
        logger.info(f"Embedded {len(documents)} documents for patient {patient_id}")
    
    def _format_demographics(self, demographics: Dict[str, Any]) -> str:
        parts = []
        
        age = demographics.get('age')
        gender = demographics.get('gender')
        if age and gender:
            parts.append(f"{age}-year-old {gender} patient")
        
        diagnosis = demographics.get('primary_diagnosis')
        if diagnosis:
            parts.append(f"Primary diagnosis: {diagnosis}")
        
        comorbidities = demographics.get('comorbidities', [])
        if comorbidities:
            parts.append(f"Comorbidities: {', '.join(comorbidities)}")
        
        medications = demographics.get('medications', [])
        if medications:
            med_names = [med.get('name', 'Unknown') if isinstance(med, dict) else str(med) for med in medications]
            parts.append(f"Current medications: {', '.join(med_names)}")
        
        allergies = demographics.get('allergies', [])
        if allergies:
            parts.append(f"Known allergies: {', '.join(allergies)}")
        
        return ". ".join(parts) + "."
    
    def _format_vitals_summary(self, vitals_history: List[Dict[str, Any]]) -> str:
        if not vitals_history:
            return "No vital signs available."
        
        df = pd.DataFrame(vitals_history)
        
        summary_parts = []
        
        for vital in ['heart_rate', 'blood_pressure_systolic', 'respiratory_rate', 'temperature', 'oxygen_saturation']:
            if vital in df.columns:
                values = df[vital].dropna()
                if not values.empty:
                    mean_val = values.mean()
                    trend = "stable"
                    
                    if len(values) > 1:
                        recent_vals = values.tail(3).mean()
                        earlier_vals = values.head(3).mean()
                        if recent_vals > earlier_vals * 1.1:
                            trend = "increasing"
                        elif recent_vals < earlier_vals * 0.9:
                            trend = "decreasing"
                    
                    vital_name = vital.replace('_', ' ').title()
                    summary_parts.append(f"{vital_name}: average {mean_val:.1f}, trend {trend}")
        
        recent_time = datetime.utcnow() - timedelta(hours=1)
        recent_vitals = [v for v in vitals_history if pd.to_datetime(v.get('timestamp', datetime.utcnow())) > recent_time]
        
        if recent_vitals:
            summary_parts.append(f"Recent readings ({len(recent_vitals)} in last hour)")
        
        return ". ".join(summary_parts) + "."
    
    def _format_lab_results(self, lab_results: List[Dict[str, Any]]) -> str:
        if not lab_results:
            return "No laboratory results available."
        
        summary_parts = []
        
        for lab in lab_results:
            test_name = lab.get('test_name', 'Unknown test')
            value = lab.get('value')
            unit = lab.get('unit', '')
            is_critical = lab.get('is_critical', False)
            
            if value is not None:
                critical_flag = " (CRITICAL)" if is_critical else ""
                summary_parts.append(f"{test_name}: {value} {unit}{critical_flag}")
        
        return ". ".join(summary_parts) + "."
    
    def retrieve_patient_context(
        self,
        patient_id: str,
        query: str = "",
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant patient context based on query"""
        
        if self.use_openai:
            query_embedding = self.embeddings.embed_query(query or f"patient {patient_id} clinical summary")
        else:
            query_embedding = self.embedding_model.encode([query or f"patient {patient_id} clinical summary"]).tolist()[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=max_results,
            where={"patient_id": patient_id}
        )
        
        context_docs = []
        for i in range(len(results['documents'][0])):
            context_docs.append({
                'content': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'similarity': results['distances'][0][i] if 'distances' in results else None
            })
        
        return context_docs
    
    def generate_patient_summary(
        self,
        patient_id: str,
        clinical_question: str = "Provide a comprehensive clinical assessment of this patient's condition and risk factors."
    ) -> Dict[str, Any]:
        """Generate AI-powered patient summary"""
        
        if not self.use_openai:
            return {
                'summary': 'AI summary not available without OpenAI API key',
                'confidence': 0.0,
                'recommendations': [],
                'context_used': []
            }
        
        context_docs = self.retrieve_patient_context(patient_id, clinical_question)
        
        if not context_docs:
            return {
                'summary': f'No clinical data available for patient {patient_id}',
                'confidence': 0.0,
                'recommendations': ['Gather more patient data'],
                'context_used': []
            }
        
        patient_context = "\n\n".join([
            f"**{doc['metadata'].get('data_type', 'Unknown').replace('_', ' ').title()}:**\n{doc['content']}"
            for doc in context_docs
        ])
        
        prompt = self.create_patient_summary_prompt()
        
        try:
            response = self.llm.predict(
                prompt.format(
                    patient_context=patient_context,
                    clinical_question=clinical_question
                )
            )
            
            return {
                'summary': response,
                'confidence': 0.8,
                'context_used': [doc['metadata'] for doc in context_docs],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating patient summary: {e}")
            return {
                'summary': f'Error generating summary: {e}',
                'confidence': 0.0,
                'recommendations': ['Manual clinical review recommended'],
                'context_used': []
            }
    
    def clinical_qa(
        self,
        patient_id: str,
        question: str
    ) -> Dict[str, Any]:
        """Answer specific clinical questions about a patient"""
        
        if not self.use_openai:
            return {
                'answer': 'Clinical Q&A not available without OpenAI API key',
                'confidence': 0.0
            }
        
        context_docs = self.retrieve_patient_context(patient_id, question)
        
        context_text = "\n\n".join([doc['content'] for doc in context_docs])
        
        qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template="""
Based on the following patient clinical data, please answer the specific question asked.

Patient Clinical Data:
{context}

Question: {question}

Please provide a direct, evidence-based answer. If the information is not available in the provided context, clearly state that and suggest what additional information would be needed.

Answer:"""
        )
        
        try:
            response = self.llm.predict(
                qa_prompt.format(
                    context=context_text,
                    question=question
                )
            )
            
            return {
                'answer': response,
                'confidence': 0.8 if context_docs else 0.3,
                'sources': [doc['metadata'] for doc in context_docs],
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in clinical Q&A: {e}")
            return {
                'answer': f'Error processing question: {e}',
                'confidence': 0.0
            }
    
    def get_similar_cases(
        self,
        patient_id: str,
        patient_demographics: Dict[str, Any],
        n_similar: int = 3
    ) -> List[Dict[str, Any]]:
        """Find similar patient cases for reference"""
        
        demographics_text = self._format_demographics(patient_demographics)
        
        if self.use_openai:
            query_embedding = self.embeddings.embed_query(demographics_text)
        else:
            query_embedding = self.embedding_model.encode([demographics_text]).tolist()[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_similar * 2,
            where={"data_type": "demographics"}
        )
        
        similar_cases = []
        seen_patients = set()
        
        for i in range(len(results['documents'][0])):
            case_patient_id = results['metadatas'][0][i]['patient_id']
            
            if case_patient_id != patient_id and case_patient_id not in seen_patients:
                similar_cases.append({
                    'patient_id': case_patient_id,
                    'demographics': results['documents'][0][i],
                    'similarity_score': 1 - results['distances'][0][i] if 'distances' in results else None
                })
                seen_patients.add(case_patient_id)
                
                if len(similar_cases) >= n_similar:
                    break
        
        return similar_cases